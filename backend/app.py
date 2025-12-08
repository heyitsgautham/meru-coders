#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask REST API Application

This module creates and configures the Flask REST API for the
Sanskrit Meter Identification System backend.
"""

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
import logging
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from backend.config import settings

# Global SocketIO instance (for access from other modules)
socketio = None
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
    app.config['CORS_ORIGINS'] = settings.CORS_ORIGINS  # For SocketIO
    
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
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        },
        r"/socket.io/*": {
            "origins": settings.CORS_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Initialize WebSocket support
    global socketio
    app.logger.info("Initializing Flask-SocketIO...")
    try:
        from backend.api.websocket import init_socketio
        socketio = init_socketio(app)
        app.socketio = socketio
        app.logger.info("Flask-SocketIO initialized successfully")
    except Exception as e:
        app.logger.warning(f"Flask-SocketIO not available: {e}")
        app.socketio = None
    
    # Initialize rate limiter
    app.logger.info("Initializing rate limiter...")
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[settings.RATELIMIT_DEFAULT],
        storage_uri=settings.RATELIMIT_STORAGE_URL
    )
    app.limiter = limiter
    
    # Initialize Supabase client
    app.logger.info("Initializing Supabase client...")
    try:
        from supabase import create_client, Client
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
            app.supabase: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            # Expose via config for auth module
            app.config['SUPABASE_CLIENT'] = app.supabase
            app.logger.info("Supabase client initialized successfully")
        else:
            app.logger.warning("Supabase credentials not configured")
            app.supabase = None
            app.config['SUPABASE_CLIENT'] = None
    except Exception as e:
        app.logger.error(f"Failed to initialize Supabase client: {e}")
        app.supabase = None
        app.config['SUPABASE_CLIENT'] = None
    
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
                'file_extract': f'{settings.API_PREFIX}/file/extract',
                'ocr_extract': f'{settings.API_PREFIX}/ocr/extract',
                'download': f'{settings.API_PREFIX}/download/<filename>',
                'examples': f'{settings.API_PREFIX}/examples'
            },
            'ocr_available': {
                'tesseract': app.tesseract_ocr is not None,
                'cloud_vision': app.cloud_vision_ocr is not None,
                'primary': 'cloud_vision' if app.cloud_vision_ocr else ('tesseract' if app.tesseract_ocr else 'none')
            },
            'features': {
                'sandhi_splitting': True,
                'fuzzy_matching': True,
                'verse_mode': True,
                'multiple_schemes': True,
                'multi_format_upload': True  # DOCX, TXT support
            }
        }
    
    # Initialize background scheduler for upload cleanup
    app.logger.info("Initializing upload cleanup scheduler...")
    try:
        from backend.utils.cleanup import scheduled_cleanup_job
        
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            func=lambda: scheduled_cleanup_job(app),
            trigger='interval',
            minutes=settings.CLEANUP_INTERVAL_MINUTES,
            id='upload_cleanup',
            name='Upload files cleanup job',
            replace_existing=True
        )
        scheduler.start()
        app.scheduler = scheduler
        
        # Register shutdown handler
        atexit.register(lambda: scheduler.shutdown(wait=False))
        
        app.logger.info(
            f"Upload cleanup scheduler started "
            f"(interval: {settings.CLEANUP_INTERVAL_MINUTES}min, "
            f"max file age: {settings.FILE_MAX_AGE_MINUTES}min)"
        )
    except Exception as e:
        app.logger.warning(f"Failed to initialize cleanup scheduler: {e}")
        app.scheduler = None
    
    app.logger.info("Flask REST API application initialized successfully")
    return app
