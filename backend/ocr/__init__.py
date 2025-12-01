"""OCR integration modules."""

from .tesseract_ocr import TesseractOCR
from .cloud_vision_ocr import CloudVisionOCR

__all__ = ['TesseractOCR', 'CloudVisionOCR']
