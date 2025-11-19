#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google OCR integration using Google Drive API
"""

from google_drive_ocr import GoogleOCRApplication
from pathlib import Path


class GoogleOCR:
    """
    Wrapper for Google Drive OCR with OAuth authentication.
    Requires Google Cloud Platform credentials.
    """
    
    def __init__(self, credentials_path, temporary_upload=True):
        """
        Initialize Google OCR client.
        
        Args:
            credentials_path: Path to Google OAuth2 client_secret.json
            temporary_upload: If True, uploads are temporary and auto-deleted
        """
        self.credentials_path = Path(credentials_path)
        self.client = None
        
        if self.credentials_path.exists():
            try:
                self.client = GoogleOCRApplication(
                    client_secret=self.credentials_path,
                    temporary_upload=temporary_upload
                )
            except Exception as e:
                print(f"Failed to initialize Google OCR: {e}")
                self.client = None
    
    def is_available(self):
        """Check if Google OCR is properly configured and available."""
        return self.client is not None
    
    def extract_text(self, image_path, output_path):
        """
        Extract text from image using Google Drive OCR.
        
        Args:
            image_path: Path to the image file
            output_path: Path where extracted text will be saved
            
        Returns:
            Extracted text as string
        """
        if not self.is_available():
            raise RuntimeError("Google OCR is not configured")
        
        status = self.client.perform_ocr(image_path, output_path=output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            return f.read()
