#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tesseract OCR Integration

Wrapper for Tesseract OCR to extract text from images.
"""

import logging
from pathlib import Path
from typing import Union, Optional

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None
    Image = None


logger = logging.getLogger(__name__)


class TesseractOCR:
    """
    Tesseract OCR wrapper for extracting Sanskrit text from images.
    
    Supports multiple Indian languages including Sanskrit, Hindi, Marathi,
    Bengali, Telugu, Gujarati, Tamil, Malayalam, and Kannada.
    """
    
    def __init__(self, languages=None):
        """
        Initialize Tesseract OCR.
        
        Args:
            languages: List of language codes (e.g., ['san', 'hin', 'mar'])
                      If None, uses default set of Indian languages
        """
        if not TESSERACT_AVAILABLE:
            raise ImportError(
                "Tesseract OCR is not available. "
                "Please install: pip install pytesseract pillow"
            )
        
        self.languages = languages or ['san', 'mar', 'hin', 'ben', 'tel', 
                                      'guj', 'tam', 'mal', 'kan']
        self.config = self._build_config()
        
        # Test Tesseract availability
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR initialized with languages: {', '.join(self.languages)}")
        except Exception as e:
            logger.error(f"Tesseract is not properly installed: {e}")
            raise RuntimeError(
                "Tesseract OCR is not installed or not in PATH. "
                "Please install Tesseract: https://github.com/tesseract-ocr/tesseract"
            )
    
    def _build_config(self):
        """Build Tesseract configuration string."""
        lang_string = '+'.join(self.languages)
        return f'-l {lang_string}'
    
    def extract_text(self, image_path: Union[str, Path]) -> str:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text as string
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            RuntimeError: If OCR extraction fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # Open image and perform OCR
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, config=self.config)
            
            logger.info(f"Successfully extracted text from: {image_path.name}")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from {image_path}: {e}")
            raise RuntimeError(f"OCR extraction failed: {e}")
    
    def extract_text_with_confidence(self, image_path: Union[str, Path]) -> dict:
        """
        Extract text with confidence scores.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with 'text' and 'confidence' information
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            image = Image.open(image_path)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(image, config=self.config, output_type=pytesseract.Output.DICT)
            
            # Extract text and confidence
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if conf != -1:  # -1 means no confidence
                    text_parts.append(data['text'][i])
                    confidences.append(conf)
            
            text = ' '.join(text_parts).strip()
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': text,
                'confidence': avg_confidence,
                'word_count': len(text_parts)
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text with confidence from {image_path}: {e}")
            raise RuntimeError(f"OCR extraction failed: {e}")
    
    def save_text_to_file(self, image_path: Union[str, Path], 
                         output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Extract text from image and save to a text file.
        
        Args:
            image_path: Path to the image file
            output_path: Path for output text file (optional)
                        If None, creates a .txt file with same name as image
            
        Returns:
            Path to the output text file
        """
        image_path = Path(image_path)
        
        if output_path is None:
            output_path = image_path.with_suffix('.txt')
        else:
            output_path = Path(output_path)
        
        # Extract text
        text = self.extract_text(image_path)
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding='utf-8')
        
        logger.info(f"Saved extracted text to: {output_path}")
        return output_path
