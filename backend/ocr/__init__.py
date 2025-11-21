"""OCR integration modules."""

from .tesseract_ocr import TesseractOCR
from .google_ocr import GoogleOCR

__all__ = ['TesseractOCR', 'GoogleOCR']
