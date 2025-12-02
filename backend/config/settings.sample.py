#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sample Settings

Copy this file to settings.py and customize as needed:
    cp settings.sample.py settings.py
"""

import os
import tempfile
from pathlib import Path


class Settings:
    """Application settings and configuration."""
    
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
    DATA_DIR = BASE_DIR / "data"
    UPLOADS_DIR = BASE_DIR / "uploads"
    PHOTOS_DIR = UPLOADS_DIR / "photos"
    TEXTS_DIR = UPLOADS_DIR / "texts"
    RESULTS_DIR = UPLOADS_DIR / "results"
    TMP_PATH = Path(tempfile.gettempdir()) / "CHANDA_TMP"
    
    # Flask configuration
    APPLICATION_NAME = "Sanskrit Meter Identification System"
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file upload
    
    # API configuration
    API_PREFIX = "/api"
    
    # CORS configuration
    # Set to "*" for development, restrict in production
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    
    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # OCR configuration
    TESSERACT_LANGUAGES = ["san", "hin", "eng"]
    # GCP credentials for Cloud Vision OCR (service account JSON)
    GCP_CREDENTIALS = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS",
        str(BASE_DIR / "secrets" / "gcp-credentials.json")
    )
    
    # Chanda configuration
    # Options: "auto" (uses ICU if available), "icu", "sanskrit_text"
    SYLLABIZATION_METHOD = "auto"
    
    # File upload restrictions
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    ALLOWED_TEXT_EXTENSIONS = {'txt', 'text'}
    
    def __init__(self):
        """Initialize settings and create necessary directories."""
        # Create upload directories if they don't exist
        for directory in [self.UPLOADS_DIR, self.PHOTOS_DIR, self.TEXTS_DIR, self.RESULTS_DIR, self.TMP_PATH]:
            directory.mkdir(parents=True, exist_ok=True)


# Legacy module-level variables for backwards compatibility
BASE_DIR = Settings.BASE_DIR
DATA_PATH = Settings.DATA_DIR
TMP_PATH = Settings.TMP_PATH
APPLICATION_NAME = Settings.APPLICATION_NAME
SECRET_KEY = Settings.SECRET_KEY
GCP_CREDENTIALS = Settings.GCP_CREDENTIALS