#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Cloud Vision OCR Integration

Wrapper for Google Cloud Vision API to extract text from images.
"""

import logging
from pathlib import Path
from typing import Union, Optional

try:
    from google_drive_ocr import GoogleOCRApplication
    GOOGLE_OCR_AVAILABLE = True
except ImportError:
    GOOGLE_OCR_AVAILABLE = False
    GoogleOCRApplication = None


logger = logging.getLogger(__name__)


class GoogleOCR:
    """
    Google Cloud Vision OCR wrapper for extracting Sanskrit text from images.
    
    Requires Google Cloud Platform credentials (client_secret.json).
    See: https://pypi.org/project/google-drive-ocr/
    """
    
    def __init__(self, credentials_path: Optional[Union[str, Path]] = None):
        """
        Initialize Google OCR.
        
        Args:
            credentials_path: Path to client_secret.json credentials file
                            If None, looks for CLIENT_SECRET environment variable
        """
        if not GOOGLE_OCR_AVAILABLE:
            raise ImportError(
                "Google OCR is not available. "
                "Please install: pip install google-drive-ocr"
            )
        
        if credentials_path is None:
            raise ValueError(
                "Google OCR requires credentials. "
                "Please provide path to client_secret.json"
            )
        
        self.credentials_path = Path(credentials_path)
        
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_path}"
            )
        
        try:
            self.ocr = GoogleOCRApplication(
                client_secret=str(self.credentials_path),
                temporary_upload=True
            )
            logger.info("Google OCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google OCR: {e}")
            raise RuntimeError(f"Google OCR initialization failed: {e}")
    
    def extract_text(self, image_path: Union[str, Path]) -> str:
        """
        Extract text from an image file using Google Cloud Vision.
        
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
        
        # Create temporary output file
        output_path = image_path.with_suffix('.google.txt')
        
        try:
            # Perform OCR
            status = self.ocr.perform_ocr(
                str(image_path),
                output_path=str(output_path)
            )
            
            # Read extracted text
            if output_path.exists():
                text = output_path.read_text(encoding='utf-8')
                logger.info(f"Successfully extracted text from: {image_path.name}")
                return text.strip()
            else:
                raise RuntimeError("OCR completed but output file was not created")
                
        except Exception as e:
            logger.error(f"Failed to extract text from {image_path}: {e}")
            raise RuntimeError(f"Google OCR extraction failed: {e}")
        finally:
            # Clean up temporary file
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
    
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
        
        try:
            # Perform OCR directly to output file
            status = self.ocr.perform_ocr(
                str(image_path),
                output_path=str(output_path)
            )
            
            logger.info(f"Saved extracted text to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save extracted text: {e}")
            raise RuntimeError(f"Google OCR save failed: {e}")
