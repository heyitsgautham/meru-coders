#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REST API Routes

API endpoints for Sanskrit meter identification.
"""

import base64
import csv
import json
import logging
import asyncio
import uuid
from pathlib import Path
from flask import request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename

from backend.config import settings

# Import edge-tts for text-to-speech functionality
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logging.warning("edge-tts not available. TTS functionality will be disabled.")

# Path to source datasets
SOURCE_DIR = Path(__file__).parent.parent / 'source'
from backend.utils.file_processor import (
    get_processor,
    FileProcessingError,
    FileType,
    ExtractionResult
)


logger = logging.getLogger(__name__)


def allowed_file(filename, allowed_extensions):
    """Check if file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


# Extended allowed extensions for multi-format support
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'docx', 'txt', 'text'}


def register_routes(app):
    """
    Register all API routes with the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    # Register chatbot blueprint
    from backend.api.chatbot import chatbot_bp
    app.register_blueprint(chatbot_bp)
    
    @app.route(f'{settings.API_PREFIX}/identify/text', methods=['POST'])
    def identify_text():
        """
        Identify meter from plain text.
        
        Request JSON:
            {
                "text": "Sanskrit text in Devanagari or other scheme",
                "output_scheme": "devanagari|iast|itrans|...",
                "text_mode": "verse|line",
                "identification_mode": "auto|vedic|classical",
                "enable_sandhi": true|false
            }
        
        identification_mode options:
            - auto: Smart detection (default) - tries both and picks best
            - vedic: For Rigveda/Vedic texts - syllable-count based identification
            - classical: For Kavya/classical poetry - L-G pattern based identification
        
        Returns:
            JSON with identified meters and analysis results
        """
        try:
            data = request.get_json()
            
            if not data or 'text' not in data:
                return jsonify({
                    'error': 'Missing required field: text'
                }), 400
            
            text = data['text']
            output_scheme = data.get('output_scheme', None)
            # Accept both 'text_mode' and 'mode' for compatibility with frontend
            text_mode = data.get('text_mode') or data.get('mode', 'line')
            enable_sandhi = data.get('enable_sandhi', False)
            # New: identification_mode for Vedic vs Classical detection
            identification_mode = data.get('identification_mode', 'auto')
            verse_mode = (text_mode == 'verse')
            
            logger.info(f"Analyzing text (text_mode: {text_mode}, id_mode: {identification_mode}, sandhi: {enable_sandhi})")
            
            # Perform meter identification
            result = app.chanda.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=True,
                save_path=settings.RESULTS_DIR,
                scheme=output_scheme,
                use_sandhi=enable_sandhi,
                mode=identification_mode
            )
            
            # Generate summary
            summary = app.chanda.summarize_results(result['result'])
            summary_formatted = app.chanda.format_summary(summary)
            
            # Handle result path
            result_path = None
            if result.get('path'):
                if isinstance(result['path'], Path):
                    result_path = result['path'].name
                else:
                    result_path = str(result['path'])
            
            return jsonify({
                'success': True,
                'result': result['result'],
                'result_path': result_path,
                'summary': summary,
                'summary_formatted': summary_formatted,
                'input': {
                    'text': text,
                    'output_scheme': output_scheme,
                    'text_mode': text_mode,
                    'identification_mode': identification_mode,
                    'enable_sandhi': enable_sandhi
                }
            })
            
        except Exception as e:
            logger.exception(f"Error in identify_text: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/identify/image', methods=['POST'])
    def identify_image():
        """
        Identify meter from an image containing Sanskrit text.
        
        Request can be:
        1. Multipart form data with 'image_file' field
        2. JSON with base64 encoded image in 'image_data' field
        
        Additional fields:
            ocr_engine: "tesseract" or "google"
            output_scheme: transliteration scheme
            text_mode: "verse" or "line"
            enable_sandhi: boolean
        """
        try:
            # Get OCR engine preference
            identification_mode = 'auto'  # Default
            if request.is_json:
                data = request.get_json()
                ocr_engine = data.get('ocr_engine', 'tesseract')
                output_scheme = data.get('output_scheme', None)
                text_mode = data.get('text_mode', 'line')
                enable_sandhi = data.get('enable_sandhi', False)
                identification_mode = data.get('identification_mode', 'auto')
                
                # Handle base64 encoded image
                if 'image_data' in data:
                    image_data = data['image_data']
                    # Remove data URL prefix if present
                    if ',' in image_data:
                        image_data = image_data.split(',', 1)[1]
                    
                    # Decode and save
                    image_bytes = base64.b64decode(image_data)
                    filename = 'uploaded_image.png'
                    filepath = settings.PHOTOS_DIR / filename
                    filepath.write_bytes(image_bytes)
                else:
                    return jsonify({
                        'error': 'Missing image_data in JSON request'
                    }), 400
            else:
                # Handle multipart form data
                if 'image_file' not in request.files:
                    return jsonify({
                        'error': 'No image file provided'
                    }), 400
                
                file = request.files['image_file']
                if file.filename == '':
                    return jsonify({
                        'error': 'Empty filename'
                    }), 400
                
                if not allowed_file(file.filename, settings.ALLOWED_IMAGE_EXTENSIONS):
                    return jsonify({
                        'error': f'Invalid file type. Allowed: {settings.ALLOWED_IMAGE_EXTENSIONS}'
                    }), 400
                
                filename = secure_filename(file.filename)
                filepath = settings.PHOTOS_DIR / filename
                file.save(filepath)
                
                ocr_engine = request.form.get('ocr_engine', 'tesseract')
                output_scheme = request.form.get('output_scheme', None)
                text_mode = request.form.get('text_mode', 'line')
                enable_sandhi = request.form.get('enable_sandhi', 'false').lower() == 'true'
                identification_mode = request.form.get('identification_mode', 'auto')
            
            # Perform OCR - Cloud Vision first, fallback to Tesseract
            text = None
            engine_used = None
            
            if app.cloud_vision_ocr:
                try:
                    text = app.cloud_vision_ocr.extract_text(filepath)
                    engine_used = 'cloud_vision'
                except Exception as e:
                    logger.warning(f"Cloud Vision OCR failed, falling back to Tesseract: {e}")
            
            if text is None and app.tesseract_ocr:
                try:
                    text = app.tesseract_ocr.extract_text(filepath)
                    engine_used = 'tesseract'
                except Exception as e:
                    logger.error(f"Tesseract OCR also failed: {e}")
                    return jsonify({
                        'success': False,
                        'error': f'OCR extraction failed: {e}'
                    }), 500
            
            if text is None:
                return jsonify({
                    'error': 'No OCR engine available'
                }), 503
            
            logger.info(f"Extracted text via {engine_used}: {text[:100] if text else '(empty)'}...")
            
            # Perform meter identification
            verse_mode = (text_mode == 'verse')
            result = app.chanda.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=True,
                save_path=settings.RESULTS_DIR,
                scheme=output_scheme,
                use_sandhi=enable_sandhi,
                mode=identification_mode
            )
            
            # Generate summary
            summary = app.chanda.summarize_results(result['result'])
            summary_formatted = app.chanda.format_summary(summary)
            
            # Handle result path
            result_path = None
            if result.get('path'):
                if isinstance(result['path'], Path):
                    result_path = result['path'].name
                else:
                    result_path = str(result['path'])
            
            # Encode image for response
            with open(filepath, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'text': text,
                'result': result['result'],
                'result_path': result_path,
                'summary': summary,
                'summary_formatted': summary_formatted,
                'image_data': image_base64,
                'input': {
                    'ocr_engine': ocr_engine,
                    'output_scheme': output_scheme,
                    'text_mode': text_mode,
                    'enable_sandhi': enable_sandhi,
                    'identification_mode': identification_mode
                }
            })
            
        except Exception as e:
            logger.exception(f"Error in identify_image: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/identify/file', methods=['POST'])
    def identify_file():
        """
        Identify meter from an uploaded document file.
        
        Supports: PDF (text-based), DOCX, TXT
        Max file size: 10MB
        
        Request: Multipart form data with 'text_file' field
        Additional fields:
            output_scheme: transliteration scheme
            text_mode: "verse" or "line"
            enable_sandhi: boolean
        """
        try:
            if 'text_file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No file provided',
                    'error_code': 'NO_FILE'
                }), 400
            
            file = request.files['text_file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'Empty filename',
                    'error_code': 'EMPTY_FILENAME'
                }), 400
            
            # Check extension first (fast validation)
            if not allowed_file(file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
                return jsonify({
                    'success': False,
                    'error': f'Unsupported file type. Allowed: PDF, DOCX, TXT',
                    'error_code': 'INVALID_TYPE'
                }), 400
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = settings.TEXTS_DIR / filename
            file.save(filepath)
            
            # Use file processor for text extraction
            processor = get_processor()
            
            try:
                extraction_result = processor.process_file(
                    filepath,
                    validate_sanskrit=True
                )
            except FileProcessingError as e:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code,
                    'details': e.details
                }), 400
            
            text = extraction_result.text
            
            # Get parameters
            output_scheme = request.form.get('output_scheme', None)
            text_mode = request.form.get('text_mode', 'line')
            enable_sandhi = request.form.get('enable_sandhi', 'false').lower() == 'true'
            identification_mode = request.form.get('identification_mode', 'auto')
            
            logger.info(f"Analyzing file: {filename} ({extraction_result.file_type.value}, {extraction_result.page_count} pages)")
            
            # Perform meter identification
            verse_mode = (text_mode == 'verse')
            result = app.chanda.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=True,
                save_path=settings.RESULTS_DIR,
                scheme=output_scheme,
                use_sandhi=enable_sandhi,
                mode=identification_mode
            )
            
            # Generate summary
            summary = app.chanda.summarize_results(result['result'])
            summary_formatted = app.chanda.format_summary(summary)
            
            # Handle result path
            result_path = None
            if result.get('path'):
                if isinstance(result['path'], Path):
                    result_path = result['path'].name
                else:
                    result_path = str(result['path'])
            
            return jsonify({
                'success': True,
                'text': text,
                'result': result['result'],
                'result_path': result_path,
                'summary': summary,
                'summary_formatted': summary_formatted,
                'file_info': {
                    'filename': filename,
                    'file_type': extraction_result.file_type.value,
                    'page_count': extraction_result.page_count,
                    'encoding': extraction_result.encoding
                },
                'input': {
                    'filename': filename,
                    'output_scheme': output_scheme,
                    'text_mode': text_mode,
                    'enable_sandhi': enable_sandhi,
                    'identification_mode': identification_mode
                }
            })
            
        except Exception as e:
            logger.exception(f"Error in identify_file: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/file/extract', methods=['POST'])
    def extract_file():
        """
        Extract text from a document file (no meter analysis).
        
        Supports: PDF (text-based), DOCX, TXT
        Max file size: 10MB
        
        Request: Multipart form data with 'file' field
        
        Returns:
            JSON with extracted text and file info
        """
        try:
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No file provided',
                    'error_code': 'NO_FILE'
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'Empty filename',
                    'error_code': 'EMPTY_FILENAME'
                }), 400
            
            # Check extension first (fast validation)
            if not allowed_file(file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
                return jsonify({
                    'success': False,
                    'error': f'Unsupported file type. Allowed: PDF, DOCX, TXT',
                    'error_code': 'INVALID_TYPE'
                }), 400
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = settings.TEXTS_DIR / filename
            file.save(filepath)
            
            logger.info(f"Extracting text from file: {filename}")
            
            # Use file processor for text extraction
            processor = get_processor()
            
            try:
                extraction_result = processor.process_file(
                    filepath,
                    validate_sanskrit=True
                )
            except FileProcessingError as e:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code,
                    'details': e.details
                }), 400
            
            logger.info(f"Extracted {len(extraction_result.text)} characters from {filename}")
            
            response_data = {
                'success': True,
                'text': extraction_result.text,
                'file_info': {
                    'filename': filename,
                    'file_type': extraction_result.file_type.value,
                    'page_count': extraction_result.page_count,
                    'encoding': extraction_result.encoding
                }
            }
            
            # Include warnings if any (e.g., CID encoding issues)
            if extraction_result.warnings:
                response_data['warnings'] = extraction_result.warnings
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.exception(f"Error in extract_file: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/download/<filename>', methods=['GET'])
    def download_result(filename):
        """
        Download a result file.
        
        Args:
            filename: Name of the file to download
        """
        try:
            return send_from_directory(
                settings.RESULTS_DIR,
                filename,
                as_attachment=True
            )
        except Exception as e:
            logger.exception(f"Error downloading file: {e}")
            return jsonify({
                'error': 'File not found'
            }), 404
    
    # ============================================================
    # DATASETS API - Browse CSV datasets with filtering
    # ============================================================
    
    def load_dataset_catalog():
        """Load the dataset catalog from JSON file."""
        catalog_path = SOURCE_DIR / 'dataset_sources.json'
        if catalog_path.exists():
            with open(catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"datasets": {}, "sourceDescriptions": {}}
    
    def read_csv_data(filename, limit=None, offset=0, chandas_filter=None, source_filter=None):
        """
        Read CSV data with optional filtering and pagination.
        
        Args:
            filename: CSV filename in source directory
            limit: Max rows to return (None = all)
            offset: Rows to skip for pagination
            chandas_filter: Filter by chandas name (substring match)
            source_filter: Filter by source (not applicable for CSVs without source column)
            
        Returns:
            tuple: (rows, total_count, columns)
        """
        filepath = SOURCE_DIR / filename
        if not filepath.exists():
            return [], 0, []
        
        rows = []
        columns = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames or []
            
            all_rows = list(reader)
            
            # Apply chandas filter if specified
            if chandas_filter:
                catalog = load_dataset_catalog()
                dataset_info = None
                for ds_id, ds_data in catalog.get('datasets', {}).items():
                    if ds_data.get('filename') == filename:
                        dataset_info = ds_data
                        break
                
                if dataset_info and dataset_info.get('chandasColumn'):
                    chandas_col = dataset_info['chandasColumn']
                    chandas_filter_lower = chandas_filter.lower()
                    all_rows = [
                        row for row in all_rows
                        if chandas_col in row and 
                        chandas_filter_lower in row[chandas_col].lower()
                    ]
            
            total_count = len(all_rows)
            
            # Apply pagination
            if offset:
                all_rows = all_rows[offset:]
            if limit:
                all_rows = all_rows[:limit]
            
            rows = all_rows
        
        return rows, total_count, columns
    
    def get_unique_chandas(filename, chandas_column):
        """Get unique chandas values from a dataset."""
        filepath = SOURCE_DIR / filename
        if not filepath.exists():
            return []
        
        chandas_set = set()
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if chandas_column in row and row[chandas_column].strip():
                    # Handle multiple chandas in one cell (comma-separated)
                    values = row[chandas_column].split(',')
                    for v in values:
                        v = v.strip()
                        if v:
                            chandas_set.add(v)
        
        return sorted(list(chandas_set))
    
    @app.route(f'{settings.API_PREFIX}/datasets', methods=['GET'])
    def list_datasets():
        """
        List all available datasets with metadata.
        
        Returns:
            JSON with list of datasets and their metadata
        """
        try:
            catalog = load_dataset_catalog()
            datasets = []
            
            for ds_id, ds_data in catalog.get('datasets', {}).items():
                # Handle merged datasets (like iitk_meters)
                if 'files' in ds_data:
                    # Merged dataset - count rows from all files
                    actual_row_count = 0
                    unique_chandas_set = set()
                    for file_info in ds_data['files']:
                        filepath = SOURCE_DIR / file_info.get('filename', '')
                        if filepath.exists():
                            with open(filepath, 'r', encoding='utf-8') as f:
                                actual_row_count += sum(1 for _ in f) - 1
                            # Get unique chandas from each file
                            chandas_col = file_info.get('chandasColumn')
                            if chandas_col:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    reader = csv.DictReader(f)
                                    for row in reader:
                                        if chandas_col in row and row[chandas_col].strip():
                                            unique_chandas_set.add(row[chandas_col].strip())
                    unique_chandas = sorted(list(unique_chandas_set))
                else:
                    # Single file dataset
                    filepath = SOURCE_DIR / ds_data.get('filename', '')
                    actual_row_count = 0
                    if filepath.exists():
                        with open(filepath, 'r', encoding='utf-8') as f:
                            actual_row_count = sum(1 for _ in f) - 1  # Subtract header
                    
                    # Get unique chandas for filtering
                    chandas_column = ds_data.get('chandasColumn')
                    unique_chandas = []
                    if chandas_column:
                        unique_chandas = get_unique_chandas(
                            ds_data.get('filename', ''),
                            chandas_column
                        )
                
                datasets.append({
                    'id': ds_id,
                    'name': ds_data.get('name', ds_id),
                    'description': ds_data.get('description', ''),
                    'source': ds_data.get('source', 'Unknown'),
                    'sourceReference': ds_data.get('sourceReference', ''),
                    'rowCount': actual_row_count,
                    'dataType': ds_data.get('dataType', 'verses'),
                    'hasSloka': ds_data.get('slokaColumn') is not None,
                    'slokaColumn': ds_data.get('slokaColumn'),
                    'chandasColumn': ds_data.get('chandasColumn'),
                    'patternColumn': ds_data.get('patternColumn'),
                    'patternType': ds_data.get('patternType', 'lg_pattern'),
                    'isMerged': 'files' in ds_data,
                    'uniqueChandas': unique_chandas[:100]  # Limit to first 100 for UI
                })
            
            # Get all unique sources for filtering
            sources = list(set(ds.get('source') for ds in datasets if ds.get('source')))
            
            return jsonify({
                'success': True,
                'datasets': datasets,
                'sources': sorted(sources),
                'sourceDescriptions': catalog.get('sourceDescriptions', {})
            })
            
        except Exception as e:
            logger.exception(f"Error listing datasets: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/datasets/<dataset_id>', methods=['GET'])
    def get_dataset(dataset_id):
        """
        Get dataset contents with pagination and filtering.
        
        Query parameters:
            limit: Max rows to return (default: 50, max: 500)
            offset: Rows to skip (default: 0)
            chandas: Filter by chandas name (substring match)
            
        Returns:
            JSON with dataset rows and metadata
        """
        try:
            catalog = load_dataset_catalog()
            
            if dataset_id not in catalog.get('datasets', {}):
                return jsonify({
                    'success': False,
                    'error': f'Dataset not found: {dataset_id}'
                }), 404
            
            ds_data = catalog['datasets'][dataset_id]
            
            # Get query parameters
            limit = min(int(request.args.get('limit', 50)), 500)
            offset = int(request.args.get('offset', 0))
            chandas_filter = request.args.get('chandas', '').strip()
            
            # Handle merged datasets (like iitk_meters)
            if 'files' in ds_data:
                all_rows = []
                all_columns = set()
                
                for file_info in ds_data['files']:
                    filepath = SOURCE_DIR / file_info.get('filename', '')
                    if not filepath.exists():
                        continue
                    
                    chandas_col = file_info.get('chandasColumn')
                    pattern_col = file_info.get('patternColumn')
                    category = file_info.get('category', '')
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        all_columns.update(reader.fieldnames or [])
                        for row in reader:
                            # Add category for merged datasets
                            row['_category'] = category
                            row['_source_file'] = file_info.get('filename', '')
                            
                            # Apply chandas filter if specified
                            if chandas_filter:
                                if chandas_col and chandas_col in row:
                                    if chandas_filter.lower() not in row[chandas_col].lower():
                                        continue
                                else:
                                    continue
                            
                            all_rows.append(row)
                
                total_count = len(all_rows)
                
                # Apply pagination
                paginated_rows = all_rows[offset:offset + limit]
                
                # Map to standardized format
                chandas_col = ds_data.get('chandasColumn')
                pattern_col = ds_data.get('patternColumn')
                
                formatted_rows = []
                for row in paginated_rows:
                    formatted_row = {
                        'sloka': None,
                        'chandas': row.get(chandas_col, '') if chandas_col else None,
                        'pattern': row.get(pattern_col, '') if pattern_col else None,
                        'source': ds_data.get('source', ''),
                        'category': row.get('_category', ''),
                        'raw': {k: v for k, v in row.items() if not k.startswith('_')}
                    }
                    formatted_rows.append(formatted_row)
                
                columns = sorted(list(all_columns))
            else:
                # Single file dataset
                filename = ds_data.get('filename', '')
                
                # Read data with filters
                rows, total_count, columns = read_csv_data(
                    filename,
                    limit=limit,
                    offset=offset,
                    chandas_filter=chandas_filter if chandas_filter else None
                )
                
                # Map to standardized format
                sloka_col = ds_data.get('slokaColumn')
                chandas_col = ds_data.get('chandasColumn')
                pattern_col = ds_data.get('patternColumn')
                
                formatted_rows = []
                for row in rows:
                    formatted_row = {
                        'sloka': row.get(sloka_col, '') if sloka_col else None,
                        'chandas': row.get(chandas_col, '') if chandas_col else None,
                        'pattern': row.get(pattern_col, '') if pattern_col else None,
                        'source': ds_data.get('source', ''),
                        'category': None,
                        'raw': row  # Include all original columns
                    }
                    formatted_rows.append(formatted_row)
            
            return jsonify({
                'success': True,
                'datasetId': dataset_id,
                'name': ds_data.get('name', dataset_id),
                'description': ds_data.get('description', ''),
                'source': ds_data.get('source', ''),
                'sourceReference': ds_data.get('sourceReference', ''),
                'dataType': ds_data.get('dataType', 'verses'),
                'patternType': ds_data.get('patternType', 'lg_pattern'),
                'columns': columns,
                'slokaColumn': ds_data.get('slokaColumn'),
                'chandasColumn': ds_data.get('chandasColumn'),
                'patternColumn': ds_data.get('patternColumn'),
                'rows': formatted_rows,
                'totalCount': total_count,
                'limit': limit,
                'offset': offset,
                'hasMore': offset + len(formatted_rows) < total_count
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid parameter: {e}'
            }), 400
        except Exception as e:
            logger.exception(f"Error getting dataset {dataset_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/tts/generate', methods=['POST'])
    def generate_tts():
        """
        Generate text-to-speech audio for Sanskrit/Hindi text.
        
        Request JSON:
            {
                "text": "Sanskrit text to convert to speech",
                "voice": "male|female" (optional, defaults to "male")
            }
        
        Returns:
            JSON with audio file URL
        """
        if not EDGE_TTS_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Text-to-speech functionality is not available. Please install edge-tts.'
            }), 503
        
        try:
            data = request.get_json()
            
            if not data or 'text' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing required field: text'
                }), 400
            
            text = data['text'].strip()
            if not text:
                return jsonify({
                    'success': False,
                    'error': 'Text cannot be empty'
                }), 400
            
            # Voice selection - Hindi neural voices work well for Sanskrit
            voice_type = data.get('voice', 'male')
            voices = {
                "female": "hi-IN-SwaraNeural",
                "male": "hi-IN-MadhurNeural"
            }
            voice = voices.get(voice_type, voices['male'])
            
            # Generate unique filename
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            output_path = settings.AUDIO_DIR / filename
            
            # Ensure audio directory exists
            settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
            
            # Generate speech using edge-tts
            async def generate_speech():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(str(output_path))
            
            # Run async function
            asyncio.run(generate_speech())
            
            logger.info(f"TTS audio generated: {filename}")
            
            return jsonify({
                'success': True,
                'audio_url': f'{settings.API_PREFIX}/tts/audio/{filename}',
                'filename': filename
            })
            
        except Exception as e:
            logger.exception(f"Error in generate_tts: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/tts/audio/<filename>', methods=['GET'])
    def serve_tts_audio(filename):
        """
        Serve generated TTS audio files.
        
        Args:
            filename: Name of the audio file
        
        Returns:
            Audio file with proper mimetype and CORS headers
        """
        try:
            audio_path = settings.AUDIO_DIR / filename
            
            if not audio_path.exists():
                return jsonify({
                    'success': False,
                    'error': 'Audio file not found'
                }), 404
            
            response = send_from_directory(
                settings.AUDIO_DIR,
                filename,
                mimetype='audio/mpeg'
            )
            
            # Add explicit headers for better browser compatibility
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Cache-Control'] = 'no-cache'
            response.headers['Access-Control-Allow-Origin'] = '*'
            
            return response
            
        except Exception as e:
            logger.exception(f"Error serving TTS audio: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route(f'{settings.API_PREFIX}/examples', methods=['GET'])
    def get_examples():
        """
        Get example verses for testing.
        
        Returns:
            JSON array of example verses with their meters
        """
        try:
            examples_dict = app.chanda.read_examples()
            
            # Convert dictionary to array format for frontend
            examples_array = []
            for meter_name, content in examples_dict.items():
                if isinstance(content, list):
                    # Format: meter_name: [lines...]
                    lines = [line for line in content if line.strip()]
                    if lines:
                        examples_array.append({
                            'meter': meter_name,
                            'lines': lines,
                            'text': '\n'.join(lines)
                        })
                elif isinstance(content, dict):
                    # Format: meter_name: {description: ..., examples: [...]}
                    if 'examples' in content and isinstance(content['examples'], list):
                        for example_text in content['examples']:
                            examples_array.append({
                                'meter': meter_name,
                                'text': example_text,
                                'lines': example_text.split('\n'),
                                'description': content.get('description', '')
                            })
            
            return jsonify({
                'success': True,
                'examples': examples_array
            })
        except Exception as e:
            logger.exception(f"Error loading examples: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'examples': []
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/schemes', methods=['GET'])
    def get_schemes():
        """
        Get available transliteration schemes.
        
        Returns:
            JSON array of available schemes
        """
        schemes = [
            {"value": "", "label": "Match Input"},
            {"value": "devanagari", "label": "Devanagari"},
            {"value": "iast", "label": "IAST"},
            {"value": "itrans", "label": "ITRANS"},
            {"value": "hk", "label": "Harvard-Kyoto"},
            {"value": "wx", "label": "WX"},
            {"value": "slp1", "label": "SLP1"},
            {"value": "assamese", "label": "Assamese"},
            {"value": "bengali", "label": "Bangla"},
            {"value": "gujarati", "label": "Gujarati"},
            {"value": "kannada", "label": "Kannada"},
            {"value": "malayalam", "label": "Malayalam"},
            {"value": "oriya", "label": "Oriya"},
            {"value": "tamil", "label": "Tamil"},
            {"value": "telugu", "label": "Telugu"}
        ]
        
        return jsonify({
            'success': True,
            'schemes': schemes
        })
    
    @app.route(f'{settings.API_PREFIX}/ocr/extract', methods=['POST'])
    def ocr_extract():
        """
        Extract text from an image using OCR only (no meter analysis).
        
        Uses Cloud Vision OCR as primary, falls back to Tesseract if unavailable.
        
        Request: Multipart form data with 'image_file' field
        
        Returns:
            JSON with extracted text only
        """
        try:
            # Handle multipart form data
            if 'image_file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No image file provided'
                }), 400
            
            file = request.files['image_file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'Empty filename'
                }), 400
            
            if not allowed_file(file.filename, settings.ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({
                    'success': False,
                    'error': f'Invalid file type. Allowed: {settings.ALLOWED_IMAGE_EXTENSIONS}'
                }), 400
            
            filename = secure_filename(file.filename)
            filepath = settings.PHOTOS_DIR / filename
            file.save(filepath)
            
            logger.info(f"OCR extraction requested for: {filename}")
            
            # Try Cloud Vision first, fallback to Tesseract
            text = None
            engine_used = None
            
            if app.cloud_vision_ocr:
                try:
                    text = app.cloud_vision_ocr.extract_text(filepath)
                    engine_used = 'cloud_vision'
                    logger.info(f"Cloud Vision OCR extracted {len(text)} characters")
                except Exception as e:
                    logger.warning(f"Cloud Vision OCR failed, falling back to Tesseract: {e}")
            
            if text is None and app.tesseract_ocr:
                try:
                    text = app.tesseract_ocr.extract_text(filepath)
                    engine_used = 'tesseract'
                    logger.info(f"Tesseract OCR extracted {len(text)} characters")
                except Exception as e:
                    logger.error(f"Tesseract OCR also failed: {e}")
                    return jsonify({
                        'success': False,
                        'error': f'OCR extraction failed: {e}'
                    }), 500
            
            if text is None:
                return jsonify({
                    'success': False,
                    'error': 'No OCR engine available'
                }), 503
            
            logger.info(f"OCR extraction complete via {engine_used}: {len(text)} chars")
            
            return jsonify({
                'success': True,
                'text': text
            })
            
        except Exception as e:
            logger.exception(f"Error in ocr_extract: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
