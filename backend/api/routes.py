#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REST API Routes

API endpoints for the Sanskrit Meter Identification System.
All routes return JSON responses.
"""

import base64
from flask import request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from pathlib import Path

from backend.config import settings


def register_routes(app):
    """
    Register all API routes.
    
    Args:
        app: Flask application instance
    """
    
    @app.route(f'{settings.API_PREFIX}/identify/text', methods=['POST'])
    def identify_from_text():
        """
        Identify meter from plain text input.
        
        Request JSON:
            {
                "text": "Sanskrit text to analyze",
                "mode": "line" or "verse",
                "output_scheme": "devanagari|iast|itrans|..." (optional)
            }
        
        Response JSON:
            {
                "success": true,
                "result": [...],
                "summary": {...},
                "result_path": "filename.txt"
            }
        """
        try:
            data = request.get_json()
            
            if not data or 'text' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing required field: text'
                }), 400
            
            text = data['text']
            mode = data.get('mode', 'line')
            output_scheme = data.get('output_scheme', settings.DEFAULT_OUTPUT_SCHEME)
            verse_mode = mode == 'verse'
            
            # Convert 'auto' to None for auto-detection
            if output_scheme == 'auto':
                output_scheme = None
            
            current_app.logger.info(f"Analyzing text in {mode} mode")
            
            # Perform meter identification
            answer = current_app.meter_analyzer.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=settings.FUZZY_MATCHING,
                save_path=settings.RESULTS_PATH,
                scheme=output_scheme
            )
            
            result = answer['result']
            result_paths = answer.get('path', {})
            
            # Generate summary
            summary = current_app.meter_analyzer.summarize_results(result)
            
            return jsonify({
                'success': True,
                'result': result,
                'summary': summary,
                'result_paths': result_paths
            })
            
        except Exception as e:
            current_app.logger.exception(f"Error in identify_from_text: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/identify/image', methods=['POST'])
    def identify_from_image():
        """
        Identify meter from uploaded image using OCR.
        
        Request Form Data:
            - image: image file
            - ocr_engine: "tesseract" or "google"
            - mode: "line" or "verse"
            - output_scheme: transliteration scheme (optional)
        
        Response JSON:
            {
                "success": true,
                "ocr_text": "extracted text",
                "result": [...],
                "summary": {...},
                "image_preview": "base64_encoded_image"
            }
        """
        try:
            if 'image' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No image file provided'
                }), 400
            
            image_file = request.files['image']
            if image_file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'Empty filename'
                }), 400
            
            # Save uploaded image
            filename = secure_filename(image_file.filename)
            filepath = settings.PHOTOS_PATH / filename
            image_file.save(str(filepath))
            
            # Get parameters
            ocr_engine = request.form.get('ocr_engine', 'tesseract')
            mode = request.form.get('mode', 'line')
            output_scheme = request.form.get('output_scheme', settings.DEFAULT_OUTPUT_SCHEME)
            verse_mode = mode == 'verse'
            
            # Convert 'auto' to None for auto-detection
            if output_scheme == 'auto':
                output_scheme = None
            
            current_app.logger.info(f"Processing image with {ocr_engine} OCR")
            
            # Perform OCR
            if ocr_engine == 'google' and current_app.google_ocr:
                output_path = filepath.with_suffix('.google.txt')
                ocr_text = current_app.google_ocr.extract_text(filepath, output_path)
            elif ocr_engine == 'tesseract':
                ocr_text = current_app.tesseract_ocr.extract_text(filepath)
            else:
                return jsonify({
                    'success': False,
                    'error': f'OCR engine "{ocr_engine}" not available'
                }), 400
            
            if not ocr_text:
                return jsonify({
                    'success': False,
                    'error': 'No text extracted from image'
                }), 400
            
            # Perform meter identification
            answer = current_app.meter_analyzer.identify_from_text(
                ocr_text,
                verse=verse_mode,
                fuzzy=settings.FUZZY_MATCHING,
                save_path=settings.RESULTS_PATH,
                scheme=output_scheme
            )
            
            result = answer['result']
            result_paths = answer.get('path', {})
            summary = current_app.meter_analyzer.summarize_results(result)
            
            # Encode image as base64 for preview
            with open(filepath, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'ocr_text': ocr_text,
                'result': result,
                'summary': summary,
                'image_preview': image_base64,
                'result_paths': result_paths
            })
            
        except Exception as e:
            current_app.logger.exception(f"Error in identify_from_image: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/identify/file', methods=['POST'])
    def identify_from_file():
        """
        Identify meter from uploaded text file.
        
        Request Form Data:
            - file: text file
            - mode: "line" or "verse"
            - output_scheme: transliteration scheme (optional)
        
        Response JSON:
            {
                "success": true,
                "text": "file contents",
                "result": [...],
                "summary": {...}
            }
        """
        try:
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No file provided'
                }), 400
            
            text_file = request.files['file']
            if text_file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'Empty filename'
                }), 400
            
            # Save uploaded file
            filename = secure_filename(text_file.filename)
            filepath = settings.TEXTS_PATH / filename
            text_file.save(str(filepath))
            
            # Read file contents
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Get parameters
            mode = request.form.get('mode', 'line')
            output_scheme = request.form.get('output_scheme', settings.DEFAULT_OUTPUT_SCHEME)
            verse_mode = mode == 'verse'
            
            # Convert 'auto' to None for auto-detection
            if output_scheme == 'auto':
                output_scheme = None
            
            current_app.logger.info(f"Processing file: {filename}")
            
            # Perform meter identification
            answer = current_app.meter_analyzer.identify_from_text(
                text,
                verse=verse_mode,
                fuzzy=settings.FUZZY_MATCHING,
                save_path=settings.RESULTS_PATH,
                scheme=output_scheme
            )
            
            result = answer['result']
            result_paths = answer.get('path', {})
            summary = current_app.meter_analyzer.summarize_results(result)
            
            return jsonify({
                'success': True,
                'text': text,
                'result': result,
                'summary': summary,
                'result_paths': result_paths
            })
            
        except Exception as e:
            current_app.logger.exception(f"Error in identify_from_file: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/download/<string:filename>', methods=['GET'])
    def download_result(filename):
        """
        Download a result file.
        
        Args:
            filename: Name of the result file
        """
        try:
            return send_from_directory(
                settings.RESULTS_PATH,
                filename,
                as_attachment=True
            )
        except Exception as e:
            current_app.logger.exception(f"Error downloading file: {e}")
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
    
    @app.route(f'{settings.API_PREFIX}/examples', methods=['GET'])
    def get_examples():
        """
        Get pre-loaded example verses.
        
        Response JSON:
            {
                "success": true,
                "examples": [...]
            }
        """
        try:
            examples_dict = current_app.meter_analyzer.read_examples()
            # Convert dict to array format for frontend
            examples = [
                {
                    'meter': meter,
                    'lines': lines
                }
                for meter, lines in examples_dict.items()
            ]
            return jsonify({
                'success': True,
                'examples': examples
            })
        except Exception as e:
            current_app.logger.exception(f"Error loading examples: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route(f'{settings.API_PREFIX}/schemes', methods=['GET'])
    def get_schemes():
        """
        Get available transliteration schemes.
        
        Response JSON:
            {
                "success": true,
                "schemes": [...]
            }
        """
        schemes = [
            {'value': 'auto', 'label': 'Auto-detect'},
            {'value': 'devanagari', 'label': 'Devanagari (देवनागरी)'},
            {'value': 'iast', 'label': 'IAST (International)'},
            {'value': 'itrans', 'label': 'ITRANS'},
            {'value': 'velthuis', 'label': 'Velthuis'},
            {'value': 'slp1', 'label': 'SLP1'},
            {'value': 'wx', 'label': 'WX Notation'},
            {'value': 'hk', 'label': 'Harvard-Kyoto'},
            {'value': 'kolkata', 'label': 'Kolkata'},
            {'value': 'iso', 'label': 'ISO 15919'},
            {'value': 'telugu', 'label': 'Telugu (తెలుగు)'},
            {'value': 'tamil', 'label': 'Tamil (தமிழ்)'},
            {'value': 'kannada', 'label': 'Kannada (ಕನ್ನಡ)'},
            {'value': 'malayalam', 'label': 'Malayalam (മലയാളം)'},
            {'value': 'bengali', 'label': 'Bengali (বাংলা)'},
            {'value': 'gujarati', 'label': 'Gujarati (ગુજરાતી)'},
            {'value': 'gurmukhi', 'label': 'Gurmukhi (ਗੁਰਮੁਖੀ)'},
            {'value': 'oriya', 'label': 'Oriya (ଓଡ଼ିଆ)'}
        ]
        return jsonify({
            'success': True,
            'schemes': schemes
        })
