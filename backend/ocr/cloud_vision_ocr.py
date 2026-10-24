#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Cloud Vision OCR Integration

Direct integration with Google Cloud Vision API for text extraction from images.
Based on the implementation in ocr.ipynb notebook.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union

try:
    from google.cloud import vision
    CLOUD_VISION_AVAILABLE = True
except ImportError:
    CLOUD_VISION_AVAILABLE = False
    vision = None


logger = logging.getLogger(__name__)


class CloudVisionOCR:
    """
    Google Cloud Vision OCR for extracting Sanskrit text from images.
    
    Uses the Google Cloud Vision API directly for text detection.
    Requires either:
    - GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to service account JSON
    - Or explicit credentials_path parameter
    
    This is a more reliable and faster approach compared to the google-drive-ocr library.
    """

    def __init__(self, credentials_path: Optional[Union[str, Path]] = None):
        """
        Initialize Cloud Vision OCR.
        
        Args:
            credentials_path: Path to service account JSON credentials file.
                            If None, uses GOOGLE_APPLICATION_CREDENTIALS env var.
        """
        if not CLOUD_VISION_AVAILABLE:
            raise ImportError(
                "Google Cloud Vision is not available. "
                "Please install: pip install google-cloud-vision"
            )

        # Set credentials if path provided (otherwise uses env var)
        if credentials_path:
            credentials_path = Path(credentials_path)
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"Credentials file not found: {credentials_path}"
                )
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)
            logger.info(f"Using credentials from: {credentials_path}")
        elif not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            raise ValueError(
                "Google Cloud Vision requires credentials. "
                "Set GOOGLE_APPLICATION_CREDENTIALS env var or provide credentials_path"
            )

        try:
            self.client = vision.ImageAnnotatorClient()
            logger.info("Google Cloud Vision OCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Vision client: {e}")
            raise RuntimeError(f"Cloud Vision initialization failed: {e}") from e

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

        try:
            # Read image content
            with open(image_path, "rb") as img_file:
                content = img_file.read()

            # Create Vision API image object
            image = vision.Image(content=content)

            # Perform text detection
            logger.info(f"Performing OCR on: {image_path.name}")
            response = self.client.text_detection(image=image)

            # Check for errors
            if response.error.message:
                raise RuntimeError(f"Cloud Vision API error: {response.error.message}")

            # Extract text from annotations
            texts = response.text_annotations

            if texts:
                extracted_text = texts[0].description.strip()
                logger.info(f"Successfully extracted {len(extracted_text)} characters from: {image_path.name}")
                return extracted_text
            else:
                logger.warning(f"No text detected in: {image_path.name}")
                return ""

        except Exception as e:
            logger.error(f"Failed to extract text from {image_path}: {e}")
            raise RuntimeError(f"Cloud Vision OCR extraction failed: {e}") from e

    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        """
        Extract text from image bytes using Google Cloud Vision.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Extracted text as string
        """
        try:
            image = vision.Image(content=image_bytes)
            response = self.client.text_detection(image=image)

            if response.error.message:
                raise RuntimeError(f"Cloud Vision API error: {response.error.message}")

            texts = response.text_annotations

            if texts:
                return texts[0].description.strip()
            else:
                return ""

        except Exception as e:
            logger.error(f"Failed to extract text from bytes: {e}")
            raise RuntimeError(f"Cloud Vision OCR extraction failed: {e}") from e

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

        text = self.extract_text(image_path)
        output_path.write_text(text, encoding='utf-8')

        logger.info(f"Saved extracted text to: {output_path}")
        return output_path
