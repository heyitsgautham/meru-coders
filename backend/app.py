#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask REST API Application

This module creates and configures the Flask REST API for the
Sanskrit Meter Identification System backend.
"""

from flask import Flask
from flask_cors import CORS
from pathlib import Path
import logging

from backend.config import settings
from backend.core import Chanda
from backend.ocr import TesseractOCR, CloudVisionOCR


def create_app():
    """
    Create and configure the Flask REST API application.
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__,
                static_folder=None,  # No static files in API
                template_folder=None)  # No templates in API
    
    # Load configuration
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = settings.MAX_CONTENT_LENGTH
    app.config['DEBUG'] = settings.DEBUG
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT
    )
    app.logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Enable CORS for frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": settings.CORS_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Initialize core components
    app.logger.info("Initializing Chanda Analyzer...")
    app.chanda = Chanda(
        data_path=str(settings.DATA_DIR),
        syllabization_method=settings.SYLLABIZATION_METHOD
    )
    
    # Initialize Tesseract OCR
    app.logger.info("Initializing Tesseract OCR...")
    try:
        app.tesseract_ocr = TesseractOCR(
            languages=settings.TESSERACT_LANGUAGES
        )
        app.logger.info("Tesseract OCR initialized successfully")
    except Exception as e:
        app.logger.warning(f"Tesseract OCR not available: {e}")
        app.tesseract_ocr = None
    
    # Initialize Cloud Vision OCR (primary OCR, with Tesseract as fallback)
    app.logger.info("Initializing Cloud Vision OCR...")
    try:
        # Check if credentials file exists
        gcp_creds = settings.GCP_CREDENTIALS
        if gcp_creds and Path(gcp_creds).exists():
            app.cloud_vision_ocr = CloudVisionOCR(credentials_path=gcp_creds)
            app.logger.info("Cloud Vision OCR initialized successfully")
        else:
            app.logger.warning(f"GCP credentials not found at: {gcp_creds}")
            app.cloud_vision_ocr = None
    except Exception as e:
        app.logger.warning(f"Cloud Vision OCR not available: {e}")
        app.cloud_vision_ocr = None
    
    # Register API routes
    from backend.api import register_routes
    register_routes(app)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for monitoring."""
        return {
            'status': 'healthy',
            'service': 'Sanskrit Meter Identification API',
            'version': '2.0.0'
        }
    
    # API info endpoint
    @app.route(f'{settings.API_PREFIX}/info', methods=['GET'])
    def api_info():
        """API information endpoint."""
        return {
            'name': 'Sanskrit Meter Identification API (Chandas-Integrated)',
            'version': '2.0.0',
            'api_prefix': settings.API_PREFIX,
            'endpoints': {
                'identify_text': f'{settings.API_PREFIX}/identify/text',
                'identify_image': f'{settings.API_PREFIX}/identify/image',
                'identify_file': f'{settings.API_PREFIX}/identify/file',
                'ocr_extract': f'{settings.API_PREFIX}/ocr/extract',
                'download': f'{settings.API_PREFIX}/download/<filename>',
                'examples': f'{settings.API_PREFIX}/examples'
            },
            'ocr_available': {
                'tesseract': app.tesseract_ocr is not None,
                'cloud_vision': app.cloud_vision_ocr is not None
            },
            'features': {
                'sandhi_splitting': True,
                'fuzzy_matching': True,
                'verse_mode': True,
                'multiple_schemes': True
            }
        }
    
    app.logger.info("Flask REST API application initialized successfully")
    return app
