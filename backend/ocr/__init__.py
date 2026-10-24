"""OCR integration modules."""

from .cloud_vision_ocr import CloudVisionOCR
from .tesseract_ocr import TesseractOCR

__all__ = ['TesseractOCR', 'CloudVisionOCR']
