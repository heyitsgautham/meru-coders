#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REST API Routes

API endpoints for Sanskrit meter identification.
"""

import base64
import json
import logging
from pathlib import Path
from flask import request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename

from backend.config import settings


logger = logging.getLogger(__name__)


def allowed_file(filename, allowed_extensions):
    """Check if file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def register_routes(app):
    """
    Register all API routes with the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.route(f'{settings.API_PREFIX}/identify/text', methods=['POST'])
    def identify_text():
        """
        Identify meter from plain text.
        
        Request JSON:
            {
                "text": "Sanskrit text in Devanagari or other scheme",
                "output_scheme": "devanagari|iast|itrans|...",
                "text_mode": "verse|line",
                "enable_sandhi": true|false
            }
        
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
            text_mode = data.get('text_mode', 'line')
            enable_sandhi = data.get('enable_sandhi', False)
            verse_mode = (text_mode == 'verse')
            
            logger.info(f"Analyzing text (mode: {text_mode}, sandhi: {enable_sandhi})")
            
            # Perform meter identification
            result = app.chanda.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=True,
                save_path=settings.RESULTS_DIR,
                scheme=output_scheme,
                use_sandhi=enable_sandhi
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
            if request.is_json:
                data = request.get_json()
                ocr_engine = data.get('ocr_engine', 'tesseract')
                output_scheme = data.get('output_scheme', None)
                text_mode = data.get('text_mode', 'line')
                enable_sandhi = data.get('enable_sandhi', False)
                
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
            
            # Perform OCR
            if ocr_engine == 'google' and app.google_ocr:
                text = app.google_ocr.extract_text(filepath)
            elif app.tesseract_ocr:
                text = app.tesseract_ocr.extract_text(filepath)
            else:
                return jsonify({
                    'error': 'No OCR engine available'
                }), 503
            
            logger.info(f"Extracted text via {ocr_engine}: {text[:100]}...")
            
            # Perform meter identification
            verse_mode = (text_mode == 'verse')
            result = app.chanda.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=True,
                save_path=settings.RESULTS_DIR,
                scheme=output_scheme,
                use_sandhi=enable_sandhi
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
                    'enable_sandhi': enable_sandhi
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
        Identify meter from an uploaded text file.
        
        Request: Multipart form data with 'text_file' field
        Additional fields:
            output_scheme: transliteration scheme
            text_mode: "verse" or "line"
            enable_sandhi: boolean
        """
        try:
            if 'text_file' not in request.files:
                return jsonify({
                    'error': 'No text file provided'
                }), 400
            
            file = request.files['text_file']
            if file.filename == '':
                return jsonify({
                    'error': 'Empty filename'
                }), 400
            
            if not allowed_file(file.filename, settings.ALLOWED_TEXT_EXTENSIONS):
                return jsonify({
                    'error': f'Invalid file type. Allowed: {settings.ALLOWED_TEXT_EXTENSIONS}'
                }), 400
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = settings.TEXTS_DIR / filename
            file.save(filepath)
            
            # Read text content
            text = filepath.read_text(encoding='utf-8')
            
            # Get parameters
            output_scheme = request.form.get('output_scheme', None)
            text_mode = request.form.get('text_mode', 'line')
            enable_sandhi = request.form.get('enable_sandhi', 'false').lower() == 'true'
            
            logger.info(f"Analyzing file: {filename}")
            
            # Perform meter identification
            verse_mode = (text_mode == 'verse')
            result = app.chanda.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=True,
                save_path=settings.RESULTS_DIR,
                scheme=output_scheme,
                use_sandhi=enable_sandhi
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
                'input': {
                    'filename': filename,
                    'output_scheme': output_scheme,
                    'text_mode': text_mode,
                    'enable_sandhi': enable_sandhi
                }
            })
            
        except Exception as e:
            logger.exception(f"Error in identify_file: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
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
