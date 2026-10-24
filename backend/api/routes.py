#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REST API Routes

API endpoints for Sanskrit meter identification.
"""

import asyncio
import base64
import csv
import json
import logging
import time
import uuid
from pathlib import Path

from flask import jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from backend.api.text_matching import calculate_similarity, normalize_sanskrit_text
from backend.config import settings

# Import AI validator for shloka pre-validation
from backend.core.ai_validator import validate_shloka_input
from backend.utils.file_processor import FileProcessingError, get_processor

# Import edge-tts for text-to-speech functionality
try:
    import edge_tts

    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logging.warning("edge-tts not available. TTS functionality will be disabled.")

# Import gTTS as fallback
try:
    from gtts import gTTS

    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logging.warning("gTTS not available. Fallback TTS will be disabled.")

# Import Google Cloud TTS (best quality with voice selection)
try:
    from google.cloud import texttospeech

    GOOGLE_TTS_AVAILABLE = True
    logging.info("Google Cloud TTS library imported successfully")
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    logging.warning("Google Cloud TTS not available - install with: pip install google-cloud-texttospeech")

# Import pyttsx3 (offline TTS with voice selection)
try:
    import pyttsx3  # noqa: F401 - availability probe

    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available.")

# Path to source datasets
SOURCE_DIR = Path(__file__).parent.parent / 'source'

logger = logging.getLogger(__name__)


def allowed_file(filename, allowed_extensions):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


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

    # Register auth and contribution blueprints
    from backend.api.community import community_bp
    from backend.auth.routes import auth_bp
    from backend.contributions.routes import contribution_bp

    app.register_blueprint(auth_bp, url_prefix=f'{settings.API_PREFIX}/auth')
    app.register_blueprint(contribution_bp, url_prefix=f'{settings.API_PREFIX}/contributions')
    app.register_blueprint(community_bp, url_prefix=f'{settings.API_PREFIX}/community')

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
                return jsonify({'error': 'Missing required field: text'}), 400

            text = data['text']
            output_scheme = data.get('output_scheme', None)
            # Accept both 'text_mode' and 'mode' for compatibility with frontend
            text_mode = data.get('text_mode') or data.get('mode', 'line')
            enable_sandhi = data.get('enable_sandhi', False)
            # New: identification_mode for Vedic vs Classical detection
            identification_mode = data.get('identification_mode', 'auto')
            verse_mode = text_mode == 'verse'

            # Start timing for latency measurement
            start_time = time.time()
            timing_info = {
                'total_ms': 0,
                'cache_lookup_ms': 0,
                'ai_validation_ms': 0,
                'rule_engine_ms': 0,
                'cache_hit': False,
                'ai_skipped': False,
            }

            logger.info(
                f"Analyzing text (text_mode: {text_mode}, id_mode: {identification_mode}, sandhi: {enable_sandhi})"
            )

            # =====================================================================
            # STEP 1: VERSE CACHE LOOKUP - Check if we have this verse already
            # If found with high similarity, skip AI validation entirely
            # =====================================================================
            cache_start = time.time()
            cache_result = find_cached_verse_match(text, threshold=CACHE_CLOSE_MATCH_THRESHOLD)
            timing_info['cache_lookup_ms'] = round((time.time() - cache_start) * 1000, 2)

            skip_ai = cache_result.get('skip_ai', False)
            timing_info['cache_hit'] = cache_result.get('found', False)
            timing_info['ai_skipped'] = skip_ai

            if cache_result.get('found'):
                logger.info(f"Cache hit! Similarity: {cache_result['similarity']:.2%}, Skip AI: {skip_ai}")

            # =====================================================================
            # STEP 2: AI PRE-VALIDATION (skipped if cache hit with high similarity)
            # This prevents the rule-based model from predicting invalid chandas
            # =====================================================================
            ai_validation = {'ai_validated': False, 'text_type': 'unknown', 'confidence': 0.0}

            if skip_ai:
                # Cache hit - assume valid Sanskrit (it's in our verified dataset)
                logger.info("Skipping AI validation - verse found in cache")
                should_proceed = True
                ai_validation = {
                    'ai_validated': False,
                    'text_type': 'verse',
                    'confidence': cache_result.get('similarity', 0.9),
                    'skipped_reason': 'cache_hit',
                }
            else:
                # No cache hit - run AI validation
                ai_start = time.time()
                should_proceed, rejection_reason, ai_validation = validate_shloka_input(text, skip_ai=False)
                timing_info['ai_validation_ms'] = round((time.time() - ai_start) * 1000, 2)

            if not should_proceed:
                logger.info(f"AI validation rejected input: {rejection_reason}")
                timing_info['total_ms'] = round((time.time() - start_time) * 1000, 2)

                # Return a 200 OK with invalid input result (same format as chanda.py)
                # This allows the frontend to display it nicely instead of as an error
                invalid_result = {
                    'line': [
                        {
                            'line': text,
                            'result': {
                                'found': False,
                                'is_padya': False,
                                'is_valid_input': False,
                                'validation_error': 'Invalid Sanskrit input',
                                'prose_message': 'Please enter valid Sanskrit text using Devanagari (देवनागरी) or IAST with diacritics (dharmakṣetre)',
                                'syllables': [],
                                'lg': [],
                                'gana': '',
                                'length': 0,
                                'matra': 0,
                                'chanda': [],
                                'jaati': [],
                                'display_scheme': None,
                                'display_line': text,
                                'display_syllables': [],
                                'display_lg': [],
                                'display_gana': '',
                                'display_length': 0,
                                'display_matra': 0,
                                'display_chanda': '',
                                'display_chanda_primary': '',
                                'fuzzy': [],
                            },
                        }
                    ]
                }

                return jsonify(
                    {
                        'success': True,  # Return success so frontend doesn't show error box
                        'result': invalid_result,
                        'summary': {
                            'count': {'line': 1, 'match_line': 0},
                            'line': {'match': {'chanda': {}}, 'no_match': 1},
                        },
                        'summary_formatted': 'Invalid input - not Sanskrit text',
                        'is_valid_input': False,
                        'validation_message': 'Please enter valid Sanskrit text using Devanagari (देवनागरी) or IAST with diacritics (dharmakṣetre)',
                        'timing': timing_info,
                    }
                )
            # =====================================================================

            # =====================================================================
            # STEP 3: METER IDENTIFICATION (rule engine)
            # =====================================================================
            rule_start = time.time()
            result = app.chanda.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=True,
                save_path=settings.RESULTS_DIR,
                scheme=output_scheme,
                use_sandhi=enable_sandhi,
                mode=identification_mode,
            )
            timing_info['rule_engine_ms'] = round((time.time() - rule_start) * 1000, 2)
            timing_info['total_ms'] = round((time.time() - start_time) * 1000, 2)

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

            # Log timing summary
            if timing_info['cache_hit']:
                ai_status = 'SKIPPED' if timing_info['ai_skipped'] else f"{timing_info['ai_validation_ms']}ms"
                logger.info(
                    f"[TIMING] Cache HIT | Total: {timing_info['total_ms']}ms | Cache: {timing_info['cache_lookup_ms']}ms | AI: {ai_status} | Rule: {timing_info['rule_engine_ms']}ms"
                )
            else:
                logger.info(
                    f"[TIMING] Cache MISS | Total: {timing_info['total_ms']}ms | Cache: {timing_info['cache_lookup_ms']}ms | AI: {timing_info['ai_validation_ms']}ms | Rule: {timing_info['rule_engine_ms']}ms"
                )

            return jsonify(
                {
                    'success': True,
                    'result': result['result'],
                    'result_path': result_path,
                    'summary': summary,
                    'summary_formatted': summary_formatted,
                    'ai_validation': {
                        'validated': ai_validation.get('ai_validated', False),
                        'text_type': ai_validation.get('text_type', 'unknown'),
                        'confidence': ai_validation.get('confidence', 0.0),
                        'skipped': timing_info['ai_skipped'],
                    },
                    'cache_info': {
                        'hit': timing_info['cache_hit'],
                        'similarity': cache_result.get('similarity', 0.0) if cache_result.get('found') else 0.0,
                        'cached_chandas': cache_result.get('cached_data', {}).get('chandas', '')
                        if cache_result.get('found')
                        else '',
                        'source_dataset': cache_result.get('cached_data', {}).get('dataset', '')
                        if cache_result.get('found')
                        else '',
                    },
                    'timing': timing_info,
                    'input': {
                        'text': text,
                        'output_scheme': output_scheme,
                        'text_mode': text_mode,
                        'identification_mode': identification_mode,
                        'enable_sandhi': enable_sandhi,
                    },
                }
            )

        except Exception as e:
            logger.exception(f"Error in identify_text: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route(f'{settings.API_PREFIX}/identify/dandaka', methods=['POST'])
    def identify_dandaka():
        """
        Identify Dandaka verses and Rajashyamala Stotram.

        Request JSON:
            {
                "text": "Sanskrit text in Devanagari or other scheme"
            }

        Returns:
            JSON with dandaka and rajashyamala analysis results
        """
        try:
            from backend.core.dandaka_detector import analyze_dandaka_mode

            data = request.get_json()

            if not data or 'text' not in data:
                return jsonify({'error': 'Missing required field: text'}), 400

            text = data['text']

            logger.info("Analyzing text in Dandaka mode")

            # Call the dandaka analyzer
            result = analyze_dandaka_mode(text)

            return jsonify({'success': True, 'result': result})

        except Exception as e:
            logger.exception(f"Error in identify_dandaka: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

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
                    return jsonify({'error': 'Missing image_data in JSON request'}), 400
            else:
                # Handle multipart form data
                if 'image_file' not in request.files:
                    return jsonify({'error': 'No image file provided'}), 400

                file = request.files['image_file']
                if file.filename == '':
                    return jsonify({'error': 'Empty filename'}), 400

                if not allowed_file(file.filename, settings.ALLOWED_IMAGE_EXTENSIONS):
                    return jsonify({'error': f'Invalid file type. Allowed: {settings.ALLOWED_IMAGE_EXTENSIONS}'}), 400

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
                    return jsonify({'success': False, 'error': f'OCR extraction failed: {e}'}), 500

            if text is None:
                return jsonify({'error': 'No OCR engine available'}), 503

            logger.info(f"Extracted text via {engine_used}: {text[:100] if text else '(empty)'}...")

            # Perform meter identification
            verse_mode = text_mode == 'verse'
            result = app.chanda.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=True,
                save_path=settings.RESULTS_DIR,
                scheme=output_scheme,
                use_sandhi=enable_sandhi,
                mode=identification_mode,
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

            return jsonify(
                {
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
                        'identification_mode': identification_mode,
                    },
                }
            )

        except Exception as e:
            logger.exception(f"Error in identify_image: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

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
                return jsonify({'success': False, 'error': 'No file provided', 'error_code': 'NO_FILE'}), 400

            file = request.files['text_file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'Empty filename', 'error_code': 'EMPTY_FILENAME'}), 400

            # Check extension first (fast validation)
            if not allowed_file(file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
                return jsonify(
                    {
                        'success': False,
                        'error': 'Unsupported file type. Allowed: PDF, DOCX, TXT',
                        'error_code': 'INVALID_TYPE',
                    }
                ), 400

            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = settings.TEXTS_DIR / filename
            file.save(filepath)

            # Use file processor for text extraction
            processor = get_processor()

            try:
                extraction_result = processor.process_file(filepath, validate_sanskrit=True)
            except FileProcessingError as e:
                return jsonify(
                    {'success': False, 'error': e.message, 'error_code': e.error_code, 'details': e.details}
                ), 400

            text = extraction_result.text

            # Get parameters
            output_scheme = request.form.get('output_scheme', None)
            text_mode = request.form.get('text_mode', 'line')
            enable_sandhi = request.form.get('enable_sandhi', 'false').lower() == 'true'
            identification_mode = request.form.get('identification_mode', 'auto')

            logger.info(
                f"Analyzing file: {filename} ({extraction_result.file_type.value}, {extraction_result.page_count} pages)"
            )

            # NOTE: AI validation is SKIPPED for file uploads (batch mode)
            # This is intentional to save API quota and reduce latency for large files
            # The rule-based validation in chanda.py still applies

            # Perform meter identification
            verse_mode = text_mode == 'verse'
            result = app.chanda.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=True,
                save_path=settings.RESULTS_DIR,
                scheme=output_scheme,
                use_sandhi=enable_sandhi,
                mode=identification_mode,
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

            return jsonify(
                {
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
                        'encoding': extraction_result.encoding,
                    },
                    'input': {
                        'filename': filename,
                        'output_scheme': output_scheme,
                        'text_mode': text_mode,
                        'enable_sandhi': enable_sandhi,
                        'identification_mode': identification_mode,
                    },
                }
            )

        except Exception as e:
            logger.exception(f"Error in identify_file: {e}")
            return jsonify({'success': False, 'error': str(e), 'error_code': 'INTERNAL_ERROR'}), 500

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
                return jsonify({'success': False, 'error': 'No file provided', 'error_code': 'NO_FILE'}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'Empty filename', 'error_code': 'EMPTY_FILENAME'}), 400

            # Check extension first (fast validation)
            if not allowed_file(file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
                return jsonify(
                    {
                        'success': False,
                        'error': 'Unsupported file type. Allowed: PDF, DOCX, TXT',
                        'error_code': 'INVALID_TYPE',
                    }
                ), 400

            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = settings.TEXTS_DIR / filename
            file.save(filepath)

            logger.info(f"Extracting text from file: {filename}")

            # Use file processor for text extraction
            processor = get_processor()

            try:
                extraction_result = processor.process_file(filepath, validate_sanskrit=True)
            except FileProcessingError as e:
                return jsonify(
                    {'success': False, 'error': e.message, 'error_code': e.error_code, 'details': e.details}
                ), 400

            logger.info(f"Extracted {len(extraction_result.text)} characters from {filename}")

            response_data = {
                'success': True,
                'text': extraction_result.text,
                'file_info': {
                    'filename': filename,
                    'file_type': extraction_result.file_type.value,
                    'page_count': extraction_result.page_count,
                    'encoding': extraction_result.encoding,
                },
            }

            # Include warnings if any (e.g., CID encoding issues)
            if extraction_result.warnings:
                response_data['warnings'] = extraction_result.warnings

            return jsonify(response_data)

        except Exception as e:
            logger.exception(f"Error in extract_file: {e}")
            return jsonify({'success': False, 'error': str(e), 'error_code': 'INTERNAL_ERROR'}), 500

    @app.route(f'{settings.API_PREFIX}/download/<filename>', methods=['GET'])
    def download_result(filename):
        """
        Download a result file.

        Args:
            filename: Name of the file to download
        """
        try:
            return send_from_directory(settings.RESULTS_DIR, filename, as_attachment=True)
        except Exception as e:
            logger.exception(f"Error downloading file: {e}")
            return jsonify({'error': 'File not found'}), 404

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
                for _ds_id, ds_data in catalog.get('datasets', {}).items():
                    if ds_data.get('filename') == filename:
                        dataset_info = ds_data
                        break

                if dataset_info and dataset_info.get('chandasColumn'):
                    chandas_col = dataset_info['chandasColumn']
                    chandas_filter_lower = chandas_filter.lower()
                    all_rows = [
                        row
                        for row in all_rows
                        if chandas_col in row and chandas_filter_lower in row[chandas_col].lower()
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
                        unique_chandas = get_unique_chandas(ds_data.get('filename', ''), chandas_column)

                datasets.append(
                    {
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
                        'uniqueChandas': unique_chandas[:100],  # Limit to first 100 for UI
                    }
                )

            # Get all unique sources for filtering
            sources = list(set(ds.get('source') for ds in datasets if ds.get('source')))

            return jsonify(
                {
                    'success': True,
                    'datasets': datasets,
                    'sources': sorted(sources),
                    'sourceDescriptions': catalog.get('sourceDescriptions', {}),
                }
            )

        except Exception as e:
            logger.exception(f"Error listing datasets: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

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
                return jsonify({'success': False, 'error': f'Dataset not found: {dataset_id}'}), 404

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
                paginated_rows = all_rows[offset : offset + limit]

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
                        'raw': {k: v for k, v in row.items() if not k.startswith('_')},
                    }
                    formatted_rows.append(formatted_row)

                columns = sorted(list(all_columns))
            else:
                # Single file dataset
                filename = ds_data.get('filename', '')

                # Read data with filters
                rows, total_count, columns = read_csv_data(
                    filename, limit=limit, offset=offset, chandas_filter=chandas_filter if chandas_filter else None
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
                        'raw': row,  # Include all original columns
                    }
                    formatted_rows.append(formatted_row)

            return jsonify(
                {
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
                    'hasMore': offset + len(formatted_rows) < total_count,
                }
            )

        except ValueError as e:
            return jsonify({'success': False, 'error': f'Invalid parameter: {e}'}), 400
        except Exception as e:
            logger.exception(f"Error getting dataset {dataset_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================
    # SLOKA SEARCH API - Fast fuzzy search for verse validation
    # ============================================================

    # Cache for sloka search index (loaded on first request)
    _sloka_search_cache = {
        'initialized': False,
        'slokas': [],  # List of (sloka_text, dataset_id, chandas, row_data)
        'normalized_map': {},  # normalized_text -> original indices
    }

    def build_sloka_search_index():
        """
        Build search index from all datasets containing slokas.
        Called once on first search request.
        """
        if _sloka_search_cache['initialized']:
            return

        logger.info("Building sloka search index...")
        catalog = load_dataset_catalog()
        slokas = []

        for ds_id, ds_data in catalog.get('datasets', {}).items():
            sloka_col = ds_data.get('slokaColumn')
            chandas_col = ds_data.get('chandasColumn')

            if not sloka_col:
                continue  # Skip datasets without slokas

            # Handle merged datasets
            if 'files' in ds_data:
                continue  # Skip merged datasets (they contain meter definitions, not verses)

            filename = ds_data.get('filename', '')
            filepath = SOURCE_DIR / filename

            if not filepath.exists():
                continue

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row_idx, row in enumerate(reader):
                        sloka_text = row.get(sloka_col, '').strip()
                        if sloka_text:
                            chandas = row.get(chandas_col, '') if chandas_col else ''
                            slokas.append(
                                {
                                    'text': sloka_text,
                                    'normalized': normalize_sanskrit_text(sloka_text),
                                    'dataset_id': ds_id,
                                    'dataset_name': ds_data.get('name', ds_id),
                                    'chandas': chandas.strip(),
                                    'source': ds_data.get('source', ''),
                                    'row_index': row_idx,
                                    'raw': row,
                                }
                            )
            except Exception as e:
                logger.warning(f"Error loading dataset {ds_id} for search index: {e}")

        _sloka_search_cache['slokas'] = slokas
        _sloka_search_cache['initialized'] = True
        logger.info(f"Sloka search index built with {len(slokas)} entries")

    # ============================================================
    # VERSE CACHE LOOKUP - Skip AI for known verses
    # ============================================================

    # Configurable thresholds for cache-based AI skipping
    CACHE_EXACT_MATCH_THRESHOLD = 0.98  # Skip AI + use cached meter directly
    CACHE_CLOSE_MATCH_THRESHOLD = 0.90  # Skip AI, but still run rule engine

    def find_cached_verse_match(text, threshold=CACHE_CLOSE_MATCH_THRESHOLD):
        """
        Search the verse cache for an exact or close match.
        If found, we can skip AI validation and potentially use cached meter info.

        Args:
            text: Input Sanskrit text
            threshold: Minimum similarity score to consider a match (default 0.90)

        Returns:
            dict with:
                - found: bool
                - similarity: float (0-1)
                - cached_data: dict with meter info if found
                - skip_ai: bool (whether to skip AI validation)
                - use_cached_meter: bool (whether cached meter can be used directly)
        """
        # Build index if not already done
        build_sloka_search_index()

        if not _sloka_search_cache['slokas']:
            return {'found': False, 'similarity': 0.0, 'skip_ai': False, 'use_cached_meter': False}

        # Normalize input for comparison
        normalized_input = normalize_sanskrit_text(text)

        if not normalized_input:
            return {'found': False, 'similarity': 0.0, 'skip_ai': False, 'use_cached_meter': False}

        best_match = None
        best_similarity = 0.0

        # Search through cached verses
        for sloka_data in _sloka_search_cache['slokas']:
            similarity = calculate_similarity(normalized_input, sloka_data['normalized'])

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = sloka_data

                # Early exit for exact match (optimization)
                if similarity >= CACHE_EXACT_MATCH_THRESHOLD:
                    break

        if best_match and best_similarity >= threshold:
            return {
                'found': True,
                'similarity': best_similarity,
                'cached_data': {
                    'text': best_match['text'],
                    'chandas': best_match.get('chandas', ''),
                    'lg_pattern': best_match.get('raw', {}).get('lg_pattern', ''),
                    'syllable_count': best_match.get('raw', {}).get('syllable_count', ''),
                    'dataset': best_match.get('dataset_name', ''),
                    'source': best_match.get('source', ''),
                },
                'skip_ai': True,  # Skip AI validation for close matches
                'use_cached_meter': best_similarity >= CACHE_EXACT_MATCH_THRESHOLD,
            }

        return {'found': False, 'similarity': best_similarity, 'skip_ai': False, 'use_cached_meter': False}

    @app.route(f'{settings.API_PREFIX}/sloka/search', methods=['POST'])
    def search_sloka():
        """
        Search for a sloka in the datasets to find matches and identify errors.

        Request JSON:
            {
                "text": "Sloka text to search for",
                "threshold": 0.7,  // Minimum similarity (0-1), default 0.7
                "limit": 10        // Max results, default 10
            }

        Returns:
            JSON with matching slokas sorted by similarity
        """
        try:
            # Build index if not already done
            build_sloka_search_index()

            data = request.get_json()

            if not data or 'text' not in data:
                return jsonify({'success': False, 'error': 'Missing required field: text'}), 400

            query_text = data['text'].strip()
            if not query_text:
                return jsonify({'success': False, 'error': 'Search text cannot be empty'}), 400

            threshold = float(data.get('threshold', 0.7))
            limit = min(int(data.get('limit', 10)), 50)  # Cap at 50 results

            # Normalize query for comparison
            query_normalized = normalize_sanskrit_text(query_text)

            if not query_normalized:
                return jsonify({'success': False, 'error': 'Query text is empty after normalization'}), 400

            # Search through all slokas
            matches = []

            for sloka_data in _sloka_search_cache['slokas']:
                # Calculate similarity on normalized text
                similarity = calculate_similarity(query_normalized, sloka_data['normalized'])

                if similarity >= threshold:
                    matches.append(
                        {
                            'original_text': sloka_data['text'],
                            'dataset_id': sloka_data['dataset_id'],
                            'dataset_name': sloka_data['dataset_name'],
                            'chandas': sloka_data['chandas'],
                            'source': sloka_data['source'],
                            'similarity': round(similarity, 4),
                            'is_exact_match': similarity >= 0.99,
                        }
                    )

            # Sort by similarity descending
            matches.sort(key=lambda x: x['similarity'], reverse=True)

            # Limit results
            matches = matches[:limit]

            # Determine if input appears to have errors
            has_exact_match = any(m['is_exact_match'] for m in matches)
            best_match = matches[0] if matches else None

            # Generate diff hints for the best match
            diff_hints = []
            if best_match and not best_match['is_exact_match']:
                # Simple character-level diff hints
                original = best_match['original_text']
                query = query_text

                # Find potential differences
                if len(query) != len(original):
                    diff_hints.append(
                        f"Length difference: your input has {len(query)} chars, original has {len(original)} chars"
                    )

            return jsonify(
                {
                    'success': True,
                    'query': query_text,
                    'query_normalized': query_normalized,
                    'matches': matches,
                    'match_count': len(matches),
                    'has_exact_match': has_exact_match,
                    'best_similarity': best_match['similarity'] if best_match else 0,
                    'diff_hints': diff_hints,
                    'total_slokas_indexed': len(_sloka_search_cache['slokas']),
                }
            )

        except ValueError as e:
            return jsonify({'success': False, 'error': f'Invalid parameter: {e}'}), 400
        except Exception as e:
            logger.exception(f"Error in sloka search: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route(f'{settings.API_PREFIX}/sloka/validate', methods=['POST'])
    def validate_sloka():
        """
        Validate a sloka and identify specific errors/differences from the dataset.
        Uses difflib for smart diff that doesn't cascade errors.

        Request JSON:
            {
                "text": "Sloka text to validate"
            }

        Returns:
            JSON with validation results including:
            - highlighted_text: User's text with error positions marked
            - differences: List of actual differences (not cascading)
        """
        try:
            import difflib

            # Build index if not already done
            build_sloka_search_index()

            data = request.get_json()

            if not data or 'text' not in data:
                return jsonify({'success': False, 'error': 'Missing required field: text'}), 400

            query_text = data['text'].strip()
            if not query_text:
                return jsonify({'success': False, 'error': 'Text cannot be empty'}), 400

            # Normalize query for finding best match
            query_normalized = normalize_sanskrit_text(query_text)

            # Find best match using similarity
            best_match = None
            best_similarity = 0

            for sloka_data in _sloka_search_cache['slokas']:
                similarity = calculate_similarity(query_normalized, sloka_data['normalized'])
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = sloka_data

            if not best_match or best_similarity < 0.5:
                return jsonify(
                    {
                        'success': True,
                        'found': False,
                        'message': 'No similar sloka found in the database. This verse may not be in our collection.',
                        'query': query_text,
                    }
                )

            original = best_match['text']

            # Normalize both texts for comparison (remove line breaks, extra spaces)
            # but keep track of original for display
            query_clean = ' '.join(query_text.split())
            original_clean = ' '.join(original.split())

            # If user's input is shorter, they might have entered partial sloka
            # In that case, only compare up to user's input length in original
            # Find the best matching substring in original
            if len(query_clean) < len(original_clean) * 0.7:
                # User entered a partial sloka - find the matching portion
                # Use get_close_matches on chunks to find best alignment
                matcher = difflib.SequenceMatcher(None, query_clean, original_clean)

                # Find longest matching block
                blocks = matcher.get_matching_blocks()
                if blocks:
                    # Take the portion of original that aligns with user input
                    # For simplicity, compare from the beginning
                    original_portion = original_clean[: len(query_clean) + 20]  # Add some buffer
                else:
                    original_portion = original_clean
            else:
                original_portion = original_clean

            # Use SequenceMatcher to find the real differences
            matcher = difflib.SequenceMatcher(None, query_clean, original_portion)

            # Get the opcodes which tell us what operations transform query into original
            opcodes = matcher.get_opcodes()

            differences = []
            error_positions = set()  # Track positions in user's text that are wrong

            for tag, i1, i2, j1, j2 in opcodes:
                if tag == 'equal':
                    # These characters match, no error
                    continue
                elif tag == 'replace':
                    # Characters at these positions are different
                    user_segment = query_clean[i1:i2]
                    correct_segment = original_portion[j1:j2]
                    differences.append(
                        {
                            'type': 'replace',
                            'position': i1,
                            'end_position': i2,
                            'your_text': user_segment,
                            'correct_text': correct_segment,
                            'description': f"'{user_segment}' should be '{correct_segment}'",
                        }
                    )
                    # Mark all positions in this range as errors
                    for pos in range(i1, i2):
                        error_positions.add(pos)
                elif tag == 'delete':
                    # Extra characters in user's input (not in original)
                    extra_segment = query_clean[i1:i2]
                    differences.append(
                        {
                            'type': 'extra',
                            'position': i1,
                            'end_position': i2,
                            'your_text': extra_segment,
                            'correct_text': '',
                            'description': f"Extra: '{extra_segment}'",
                        }
                    )
                    for pos in range(i1, i2):
                        error_positions.add(pos)
                elif tag == 'insert':
                    # Missing characters (in original but not in user's input)
                    missing_segment = original_portion[j1:j2]
                    # Only report missing if it's not just trailing text (user entered partial)
                    if i1 < len(query_clean) - 5:  # Not at the end
                        differences.append(
                            {
                                'type': 'missing',
                                'position': i1,
                                'end_position': i1,
                                'your_text': '',
                                'correct_text': missing_segment,
                                'description': f"Missing: '{missing_segment}'",
                            }
                        )

            # Build highlighted segments for the frontend
            # Each segment is either normal or an error
            highlighted_segments = []

            i = 0
            while i < len(query_clean):
                if i in error_positions:
                    # Find the end of this error run
                    start = i
                    while i < len(query_clean) and i in error_positions:
                        i += 1
                    highlighted_segments.append({'text': query_clean[start:i], 'isError': True})
                else:
                    # Find the end of this normal run
                    start = i
                    while i < len(query_clean) and i not in error_positions:
                        i += 1
                    highlighted_segments.append({'text': query_clean[start:i], 'isError': False})

            is_valid = len(differences) == 0

            # Recalculate similarity on cleaned texts for more accurate percentage
            final_similarity = difflib.SequenceMatcher(None, query_clean, original_clean).ratio()

            return jsonify(
                {
                    'success': True,
                    'found': True,
                    'is_valid': is_valid,
                    'similarity': round(final_similarity, 4),
                    'similarity_percentage': round(final_similarity * 100, 1),
                    'original_text': original,  # Keep original with line breaks for display
                    'your_text': query_text,
                    'highlighted_segments': highlighted_segments,
                    'chandas': best_match['chandas'],
                    'dataset_name': best_match['dataset_name'],
                    'source': best_match['source'],
                    'differences': differences,
                    'difference_count': len(differences),
                    'message': 'Perfect match!' if is_valid else f'Found {len(differences)} difference(s).',
                }
            )

        except Exception as e:
            logger.exception(f"Error in sloka validation: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route(f'{settings.API_PREFIX}/tts/generate', methods=['POST'])
    def generate_tts():
        """
        Generate text-to-speech audio for Sanskrit/Hindi text.

        Request JSON:
            {
                "text": "Sanskrit text to convert to speech",
                "voice": "male|female" // (optional, defaults to "female")
            }

        Returns:
            JSON with audio file URL
        """
        if not EDGE_TTS_AVAILABLE and not GTTS_AVAILABLE and not GOOGLE_TTS_AVAILABLE and not PYTTSX3_AVAILABLE:
            return jsonify(
                {
                    'success': False,
                    'error': 'Text-to-speech functionality is not available. Please install edge-tts, gTTS, pyttsx3, or google-cloud-texttospeech.',
                }
            ), 503

        try:
            data = request.get_json()

            if not data or 'text' not in data:
                return jsonify({'success': False, 'error': 'Missing required field: text'}), 400

            text = data['text'].strip()
            if not text:
                return jsonify({'success': False, 'error': 'Text cannot be empty'}), 400

            logger.info(f"TTS request received - text length: {len(text)} chars")

            # Voice selection
            voice_type = data.get('voice', 'male')
            logger.info(f"TTS voice requested: {voice_type}")

            # Generate unique filename
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            output_path = settings.AUDIO_DIR / filename

            # Ensure audio directory exists
            settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

            # Try Google Cloud TTS first (best quality with proper voice selection)
            generation_success = False
            used_engine = None

            if GOOGLE_TTS_AVAILABLE:
                try:
                    logger.info("Attempting TTS generation with Google Cloud TTS...")
                    client = texttospeech.TextToSpeechClient()

                    # Configure voice selection - Google Cloud TTS with Chirp3-HD voices for Sanskrit
                    voice_configs = {
                        "male": {
                            "language_code": "hi-IN",
                            "name": "hi-IN-Chirp3-HD-Algieba",  # Male Chirp3-HD voice for Sanskrit
                            "ssml_gender": texttospeech.SsmlVoiceGender.MALE,
                        },
                        "female": {
                            "language_code": "hi-IN",
                            "name": "hi-IN-Wavenet-A",  # Female voice (Google Cloud TTS)
                            "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE,
                        },
                    }

                    voice_config = voice_configs.get(voice_type, voice_configs['male'])

                    # Set up synthesis input
                    synthesis_input = texttospeech.SynthesisInput(text=text)

                    # Select voice parameters
                    voice = texttospeech.VoiceSelectionParams(
                        language_code=voice_config["language_code"],
                        name=voice_config["name"],
                        ssml_gender=voice_config["ssml_gender"],
                    )

                    # Select audio config
                    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

                    # Perform TTS request
                    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

                    # Write audio to file
                    with open(str(output_path), 'wb') as out:
                        out.write(response.audio_content)

                    if output_path.exists() and output_path.stat().st_size > 0:
                        generation_success = True
                        used_engine = f"Google Cloud TTS ({voice_config['name']})"
                        logger.info(f"TTS generated successfully with Google Cloud TTS ({voice_type} voice)")
                    else:
                        logger.warning("Google Cloud TTS created empty file")
                        if output_path.exists():
                            output_path.unlink()
                except Exception as e:
                    logger.warning(f"Google Cloud TTS failed: {e}. Falling back to edge-tts...")
                    if output_path.exists():
                        output_path.unlink()

            # Try edge-tts second, fallback to gTTS
            if not generation_success and EDGE_TTS_AVAILABLE:
                try:
                    logger.info("Attempting TTS generation with edge-tts...")
                    # Hindi neural voices work well for Sanskrit
                    voices = {"female": "hi-IN-SwaraNeural", "male": "hi-IN-MadhurNeural"}
                    voice = voices.get(voice_type, voices['male'])
                    logger.info(f"TTS using edge-tts voice: {voice}")

                    async def generate_speech():
                        communicate = edge_tts.Communicate(text, voice)
                        await communicate.save(str(output_path))

                    # Run async function
                    asyncio.run(generate_speech())

                    # Check if file was created successfully
                    if output_path.exists() and output_path.stat().st_size > 0:
                        generation_success = True
                        used_engine = "edge-tts"
                        logger.info("TTS generated successfully with edge-tts")
                    else:
                        logger.warning("edge-tts created empty file, falling back to gTTS")
                        if output_path.exists():
                            output_path.unlink()
                except Exception as e:
                    logger.warning(f"edge-tts failed: {e}. Falling back to gTTS...")
                    if output_path.exists():
                        output_path.unlink()

            # Fallback to gTTS if edge-tts failed or not available
            if not generation_success and GTTS_AVAILABLE:
                try:
                    logger.info(f"Attempting TTS generation with gTTS (voice: {voice_type})...")
                    # gTTS doesn't support different voices natively, but we can adjust parameters
                    # Use 'hi' for Hindi which works well for Sanskrit
                    # Note: gTTS uses a single voice per language, so male/female selection isn't supported
                    # We'll use slow=False for male (normal speed) and could adjust other params
                    tts = gTTS(text=text, lang='hi', slow=False)
                    tts.save(str(output_path))

                    if output_path.exists() and output_path.stat().st_size > 0:
                        generation_success = True
                        used_engine = "gTTS (Note: Voice selection not supported in fallback mode)"
                        logger.info("TTS generated successfully with gTTS")
                        logger.warning("gTTS doesn't support voice selection - using default Hindi voice")
                except Exception as e:
                    logger.error(f"gTTS also failed: {e}")
                    if output_path.exists():
                        output_path.unlink()

            # Verify file was created and has content
            if not generation_success or not output_path.exists():
                logger.error("Audio file was not created")
                return jsonify(
                    {'success': False, 'error': 'Failed to generate audio file with all available engines'}
                ), 500

            file_size = output_path.stat().st_size
            if file_size == 0:
                logger.error(f"Audio file is empty: {output_path}")
                output_path.unlink()  # Clean up empty file
                return jsonify({'success': False, 'error': 'Generated audio file is empty'}), 500

            logger.info(f"TTS audio generated successfully using {used_engine}: {filename} ({file_size} bytes)")

            return jsonify(
                {
                    'success': True,
                    'audio_url': f'{settings.API_PREFIX}/tts/audio/{filename}',
                    'filename': filename,
                    'engine': used_engine,
                    'voice': voice_type,
                }
            )

        except Exception as e:
            logger.exception(f"Error in generate_tts: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

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
                return jsonify({'success': False, 'error': 'Audio file not found'}), 404

            # Check if download is requested
            download = request.args.get('download', 'false').lower() == 'true'

            response = send_from_directory(
                settings.AUDIO_DIR,
                filename,
                mimetype='audio/mpeg',
                as_attachment=download,
                download_name='sanskrit_recitation.mp3' if download else None,
            )

            # Add explicit headers for better browser compatibility
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Cache-Control'] = 'no-cache'
            response.headers['Access-Control-Allow-Origin'] = '*'

            return response

        except Exception as e:
            logger.exception(f"Error serving TTS audio: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

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
                        examples_array.append({'meter': meter_name, 'lines': lines, 'text': '\n'.join(lines)})
                elif isinstance(content, dict):
                    # Format: meter_name: {description: ..., examples: [...]}
                    if 'examples' in content and isinstance(content['examples'], list):
                        for example_text in content['examples']:
                            examples_array.append(
                                {
                                    'meter': meter_name,
                                    'text': example_text,
                                    'lines': example_text.split('\n'),
                                    'description': content.get('description', ''),
                                }
                            )

            return jsonify({'success': True, 'examples': examples_array})
        except Exception as e:
            logger.exception(f"Error loading examples: {e}")
            return jsonify({'success': False, 'error': str(e), 'examples': []}), 500

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
            {"value": "telugu", "label": "Telugu"},
        ]

        return jsonify({'success': True, 'schemes': schemes})

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
                return jsonify({'success': False, 'error': 'No image file provided'}), 400

            file = request.files['image_file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'Empty filename'}), 400

            if not allowed_file(file.filename, settings.ALLOWED_IMAGE_EXTENSIONS):
                return jsonify(
                    {'success': False, 'error': f'Invalid file type. Allowed: {settings.ALLOWED_IMAGE_EXTENSIONS}'}
                ), 400

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
                    return jsonify({'success': False, 'error': f'OCR extraction failed: {e}'}), 500

            if text is None:
                return jsonify({'success': False, 'error': 'No OCR engine available'}), 503

            logger.info(f"OCR extraction complete via {engine_used}: {len(text)} chars")

            return jsonify({'success': True, 'text': text})

        except Exception as e:
            logger.exception(f"Error in ocr_extract: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route(f'{settings.API_PREFIX}/audio/transcribe', methods=['POST'])
    def audio_transcribe():
        """
        Transcribe Sanskrit audio using IndicConformer ASR.

        Accepts audio files (WAV, MP3, WebM) and returns transcribed Sanskrit text.
        Uses AI4Bharat's IndicConformerASR model via external API.
        WebM files (from browser recording) are automatically converted to WAV.

        Request: Multipart form data with 'audio_file' field

        Returns:
            JSON with transcribed text
        """
        import subprocess

        import requests as http_requests

        ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'webm', 'ogg', 'm4a', 'flac'}

        try:
            # Handle multipart form data
            if 'audio_file' not in request.files:
                return jsonify({'success': False, 'error': 'No audio file provided'}), 400

            file = request.files['audio_file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'Empty filename'}), 400

            if not allowed_file(file.filename, ALLOWED_AUDIO_EXTENSIONS):
                return jsonify(
                    {'success': False, 'error': f'Invalid file type. Allowed: {ALLOWED_AUDIO_EXTENSIONS}'}
                ), 400

            filename = secure_filename(file.filename)
            filepath = settings.AUDIO_DIR / filename
            file.save(filepath)

            logger.info(f"Audio transcription requested for: {filename}")

            # Check if we need to convert WebM to WAV (browser recordings are WebM/Opus)
            file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            audio_filepath = filepath
            converted_filepath = None

            if file_ext in ('webm', 'ogg', 'm4a'):
                # Convert to WAV using ffmpeg
                converted_filepath = settings.AUDIO_DIR / f"{filename.rsplit('.', 1)[0]}.wav"
                logger.info(f"Converting {file_ext.upper()} to WAV: {converted_filepath}")

                try:
                    # Use ffmpeg to convert to 16kHz mono WAV (optimal for ASR)
                    result = subprocess.run(
                        [
                            'ffmpeg',
                            '-y',
                            '-i',
                            str(filepath),
                            '-ar',
                            '16000',  # 16kHz sample rate
                            '-ac',
                            '1',  # Mono
                            '-f',
                            'wav',
                            str(converted_filepath),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )

                    if result.returncode != 0:
                        logger.error(f"ffmpeg conversion failed: {result.stderr}")
                        return jsonify(
                            {
                                'success': False,
                                'error': 'Audio format conversion failed. Please upload a WAV or MP3 file.',
                            }
                        ), 400

                    audio_filepath = converted_filepath

                    # Get audio duration using ffprobe
                    try:
                        probe_result = subprocess.run(
                            [
                                'ffprobe',
                                '-v',
                                'error',
                                '-show_entries',
                                'format=duration',
                                '-of',
                                'default=noprint_wrappers=1:nokey=1',
                                str(converted_filepath),
                            ],
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )
                        duration = float(probe_result.stdout.strip()) if probe_result.stdout.strip() else 0
                        logger.info(f"Conversion successful: {converted_filepath} (duration: {duration:.2f}s)")

                        if duration < 1.0:
                            logger.warning(f"Audio too short: {duration:.2f}s")
                            return jsonify(
                                {
                                    'success': False,
                                    'error': 'Recording is too short. Please record at least 1 second of audio.',
                                }
                            ), 400
                    except Exception as e:
                        logger.warning(f"Could not get audio duration: {e}")
                        logger.info(f"Conversion successful: {converted_filepath}")

                except FileNotFoundError:
                    logger.error("ffmpeg not found. Cannot convert WebM to WAV.")
                    return jsonify(
                        {
                            'success': False,
                            'error': 'Audio conversion not available. Please upload a WAV or MP3 file instead.',
                        }
                    ), 400
                except subprocess.TimeoutExpired:
                    logger.error("ffmpeg conversion timed out")
                    return jsonify(
                        {'success': False, 'error': 'Audio conversion timed out. Please try a shorter recording.'}
                    ), 400

            # Call IndicConformer ASR API
            asr_url = settings.INDIC_ASR_URL
            if not asr_url:
                logger.warning("INDIC_ASR_URL is not set; speech recognition is disabled")
                return jsonify({'success': False, 'error': 'Speech recognition is not configured on this server.'}), 503
            send_filename = audio_filepath.name

            try:
                with open(audio_filepath, 'rb') as audio_file:
                    files = {'file': (send_filename, audio_file)}
                    data = {'decoder': 'rnnt'}

                    logger.info(f"Calling IndicConformer ASR at: {asr_url} with file: {send_filename}")
                    response = http_requests.post(
                        asr_url,
                        files=files,
                        data=data,
                        timeout=120,  # 2 minute timeout for large audio files
                    )

                    if response.status_code != 200:
                        logger.error(f"ASR API returned status {response.status_code}: {response.text}")
                        return jsonify({'success': False, 'error': f'ASR service error: {response.status_code}'}), 502

                    result = response.json()
                    logger.info(f"ASR API response: {result}")

                    # Extract transcription from response
                    transcription = result.get('transcription', [])
                    logger.info(f"Transcription field: {transcription}, type: {type(transcription)}")

                    if isinstance(transcription, list) and len(transcription) > 0:
                        text = transcription[0].strip()
                    elif isinstance(transcription, str):
                        text = transcription.strip()
                    else:
                        text = ''

                    if not text:
                        logger.warning("ASR returned empty transcription - audio may be silent or too short")
                        return jsonify(
                            {
                                'success': False,
                                'error': 'No speech detected in the audio. Please ensure you are speaking clearly into the microphone and try recording again.',
                            }
                        ), 400

                    logger.info(f"ASR transcription complete: {len(text)} chars")

                    return jsonify({'success': True, 'text': text, 'decoder_used': result.get('decoder_used', 'rnnt')})

            except http_requests.exceptions.Timeout:
                logger.error("ASR API request timed out")
                return jsonify(
                    {'success': False, 'error': 'Audio transcription timed out. Please try a shorter audio file.'}
                ), 504
            except http_requests.exceptions.ConnectionError as e:
                logger.error(f"ASR API connection error: {e}")
                return jsonify(
                    {'success': False, 'error': 'Could not connect to transcription service. Please try again later.'}
                ), 503
            finally:
                # Clean up uploaded and converted files
                try:
                    filepath.unlink()
                except Exception:
                    pass
                if converted_filepath:
                    try:
                        converted_filepath.unlink()
                    except Exception:
                        pass

        except Exception as e:
            logger.exception(f"Error in audio_transcribe: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
