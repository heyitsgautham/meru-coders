#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Configuration

Configuration settings for the Flask REST API backend.
"""

import os
from pathlib import Path

# Base directory (backend folder)
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
UPLOAD_FOLDER = BASE_DIR / "uploads"
PHOTOS_PATH = UPLOAD_FOLDER / "photos"
TEXTS_PATH = UPLOAD_FOLDER / "texts"
RESULTS_PATH = UPLOAD_FOLDER / "results"

# Create directories if they don't exist
for path in [PHOTOS_PATH, TEXTS_PATH, RESULTS_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# Flask configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

# CORS configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
]

# Google OCR configuration (optional)
CLIENT_SECRET = PROJECT_ROOT / "client_secret.json"
if not CLIENT_SECRET.exists():
    CLIENT_SECRET = None

# API configuration
API_PREFIX = "/api"
API_VERSION = "v1"

# OCR configuration
TESSERACT_LANGUAGES = "san+mar+hin+ben+tel+guj+tam+mal+kan"
TESSERACT_CONFIG = "--psm 6"

# Meter identification configuration
FUZZY_MATCHING = True
DEFAULT_OUTPUT_SCHEME = "devanagari"

# Logging configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
