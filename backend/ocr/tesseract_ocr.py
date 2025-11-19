#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tesseract OCR integration for Sanskrit text recognition
"""

import pytesseract
from pathlib import Path


class TesseractOCR:
    """
    Wrapper for Tesseract OCR with support for Indian language scripts.
    Optimized for Sanskrit, Hindi, Marathi, Bengali, and other Indic languages.
    """
    
    def __init__(self, languages='san+mar+hin+ben+tel+guj+tam+mal+kan'):
        """
        Initialize Tesseract OCR.
        
        Args:
            languages: Plus-separated list of language codes (default includes major Indic languages)
        """
        self.languages = languages
        self.config = f'-l {languages}'
    
    def extract_text(self, image_path):
        """
        Extract text from an image using Tesseract OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text as string
        """
        return pytesseract.image_to_string(str(image_path), config=self.config)
    
    def extract_to_file(self, image_path, output_path):
        """
        Extract text from image and save to file.
        
        Args:
            image_path: Path to the image file
            output_path: Path where extracted text will be saved
        """
        text = self.extract_text(image_path)
        output_path = Path(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return text
