#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Processor Module

Handles extraction of text from various file formats (PDF, DOCX, TXT)
with support for encoding detection, Sanskrit validation, and comprehensive
error handling.

Supported formats:
- PDF (text-based only, no OCR)
- DOCX (Microsoft Word 2007+)
- TXT/TEXT (plain text with auto-encoding detection)

Author: Meru Coders Team
Date: December 2025
"""

import logging
import re
from pathlib import Path
from typing import Callable, Optional

from .file_checks import FileChecks
from .file_types import ExtractionResult, FileProcessingError, FileType
from .pdf_extraction import PdfExtraction

logger = logging.getLogger(__name__)

__all__ = ['ExtractionResult', 'FileProcessingError', 'FileProcessor', 'FileType', 'get_processor']


class FileProcessor(FileChecks, PdfExtraction):
    """
    Processes various file formats and extracts text content.

    Features:
    - Multi-format support (PDF, DOCX, TXT)
    - Encoding auto-detection for text files
    - Sanskrit/Devanagari character validation
    - Comprehensive error handling for corrupted/protected files
    - Progress callbacks for large files
    """

    # File size limit: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # Supported extensions
    ALLOWED_EXTENSIONS = {'docx', 'txt', 'text'}

    # MIME type mapping (for magic number detection)
    MIME_TYPE_MAP = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileType.DOCX,
        'text/plain': FileType.TXT,
    }

    # Unicode ranges for Sanskrit/Devanagari characters
    # Devanagari: U+0900–U+097F
    # Devanagari Extended: U+A8E0–U+A8FF
    # Vedic Extensions: U+1CD0–U+1CFF
    DEVANAGARI_PATTERN = re.compile(r'[\u0900-\u097F\uA8E0-\uA8FF\u1CD0-\u1CFF]')

    # IAST/transliteration pattern (common Sanskrit romanization)
    IAST_PATTERN = re.compile(
        r'[āīūṛṝḷḹṃḥśṣṇṭḍñṅĀĪŪṚṜḶḸṂḤŚṢṆṬḌÑṄ]|'  # Special IAST characters
        r'\b(ca|cha|ja|jha|ña|ṭa|ṭha|ḍa|ḍha|ṇa|ta|tha|da|dha|na|pa|pha|ba|bha|ma|ya|ra|la|va|śa|ṣa|sa|ha)\b',
        re.IGNORECASE,
    )

    # Pattern to detect CID (Character ID) markers from PDFs with custom font encodings
    # These appear as (cid:XX) where XX is a number - indicates broken character mapping
    CID_PATTERN = re.compile(r'\(cid:\d+\)')

    # Minimum Sanskrit character ratio to consider content valid
    MIN_SANSKRIT_RATIO = 0.05  # At least 5% Sanskrit characters
    MIN_SANSKRIT_CHARS = 5  # At least 5 Sanskrit characters (lowered for IAST compatibility)

    def __init__(self):
        """Initialize the file processor."""
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required libraries are available."""
        self._has_pdfplumber = False
        self._has_pymupdf = False
        self._has_docx = False
        self._has_chardet = False
        self._has_magic = False

        try:
            import pdfplumber  # noqa: F401 - availability probe

            self._has_pdfplumber = True
        except ImportError:
            logger.warning("pdfplumber not installed")

        try:
            import fitz  # noqa: F401 - availability probe

            self._has_pymupdf = True
            logger.info("PyMuPDF available for enhanced PDF extraction")
        except ImportError:
            logger.warning("PyMuPDF not installed - fallback PDF extraction disabled")

        if not self._has_pdfplumber and not self._has_pymupdf:
            logger.warning("No PDF library available - PDF support disabled")

        try:
            import docx  # noqa: F401 - availability probe

            self._has_docx = True
        except ImportError:
            logger.warning("python-docx not installed - DOCX support disabled")

        try:
            import chardet  # noqa: F401 - availability probe

            self._has_chardet = True
        except ImportError:
            logger.warning("chardet not installed - encoding detection limited")

        try:
            import magic  # noqa: F401 - availability probe

            self._has_magic = True
        except ImportError:
            logger.warning("python-magic not installed - MIME detection by extension only")

    def extract_from_docx(
        self, filepath: Path, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ExtractionResult:
        """
        Extract text from a DOCX file.

        Args:
            filepath: Path to the DOCX file
            progress_callback: Optional callback(current_para, total_paras)
        """
        if not self._has_docx:
            raise FileProcessingError(
                "DOCX processing not available", "DOCX_UNAVAILABLE", "python-docx library is not installed"
            )

        from docx import Document
        from docx.opc.exceptions import PackageNotFoundError

        try:
            doc = Document(str(filepath))
            paragraphs = doc.paragraphs
            total_paras = len(paragraphs)

            text_parts = []
            for i, para in enumerate(paragraphs):
                if progress_callback:
                    progress_callback(i + 1, total_paras)

                if para.text.strip():
                    text_parts.append(para.text)

            full_text = '\n'.join(text_parts)

            if not full_text.strip():
                raise FileProcessingError(
                    "No text content in DOCX", "DOCX_EMPTY", "The Word document contains no text content"
                )

            return ExtractionResult(
                text=full_text.strip(),
                file_type=FileType.DOCX,
                page_count=1,  # DOCX doesn't have a simple page count
            )

        except PackageNotFoundError:
            raise FileProcessingError(
                "Invalid DOCX file",
                "DOCX_INVALID",
                "The file is not a valid Word document (.docx). Note: Legacy .doc files are not supported.",
            ) from None
        except Exception as e:
            error_str = str(e).lower()

            if 'corrupt' in error_str or 'invalid' in error_str:
                raise FileProcessingError(
                    "Corrupted DOCX file", "DOCX_CORRUPTED", f"The Word document appears to be corrupted: {str(e)}"
                ) from e

            raise FileProcessingError("Failed to process DOCX", "DOCX_ERROR", str(e)) from e

    def detect_encoding(self, filepath: Path) -> str:
        """
        Detect the encoding of a text file.

        Returns:
            Detected encoding string (default: 'utf-8')
        """
        if not self._has_chardet:
            return 'utf-8'

        import chardet

        try:
            # Read raw bytes for detection
            raw_bytes = filepath.read_bytes()

            # Detect encoding
            result = chardet.detect(raw_bytes)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)

            logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")

            # If low confidence, default to UTF-8
            if confidence < 0.5:
                return 'utf-8'

            return encoding or 'utf-8'

        except Exception as e:
            logger.warning(f"Encoding detection failed: {e}, defaulting to UTF-8")
            return 'utf-8'

    def extract_from_txt(
        self, filepath: Path, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ExtractionResult:
        """
        Extract text from a plain text file with encoding auto-detection.

        Args:
            filepath: Path to the text file
            progress_callback: Optional callback (not really used for txt)
        """
        # Detect encoding
        encoding = self.detect_encoding(filepath)

        try:
            text = filepath.read_text(encoding=encoding)

            if progress_callback:
                progress_callback(1, 1)

            if not text.strip():
                raise FileProcessingError("Empty text file", "TXT_EMPTY", "The text file is empty")

            return ExtractionResult(text=text.strip(), file_type=FileType.TXT, page_count=1, encoding=encoding)

        except UnicodeDecodeError:
            # Try with UTF-8 if detected encoding fails
            try:
                text = filepath.read_text(encoding='utf-8')
                return ExtractionResult(text=text.strip(), file_type=FileType.TXT, page_count=1, encoding='utf-8')
            except UnicodeDecodeError:
                raise FileProcessingError(
                    "Unable to read text file",
                    "TXT_ENCODING_ERROR",
                    f"Could not decode file with detected encoding ({encoding}) or UTF-8. "
                    "Please ensure the file is saved with UTF-8 encoding.",
                ) from None
        except Exception as e:
            raise FileProcessingError("Failed to read text file", "TXT_ERROR", str(e)) from e

    def process_file(
        self,
        filepath: Path,
        validate_sanskrit: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> ExtractionResult:
        """
        Main entry point for file processing.

        Args:
            filepath: Path to the file to process
            validate_sanskrit: Whether to validate Sanskrit content
            progress_callback: Optional callback for progress updates

        Returns:
            ExtractionResult with extracted text and metadata

        Raises:
            FileProcessingError: If file is invalid, corrupted, or has no Sanskrit
        """
        # Validate file basics
        is_valid, error = self.validate_file(filepath)
        if not is_valid:
            raise FileProcessingError(error, "VALIDATION_ERROR")

        # Detect actual file type
        file_type = self.detect_file_type(filepath)

        if file_type == FileType.UNKNOWN:
            ext = self.get_file_extension(filepath.name)
            raise FileProcessingError(
                "Unknown file type",
                "UNKNOWN_TYPE",
                f"Cannot determine how to process '.{ext}' file. Supported formats: PDF, DOCX, TXT",
            )

        # Verify extension matches content
        ext = self.get_file_extension(filepath.name)
        expected_type = {'pdf': FileType.PDF, 'docx': FileType.DOCX, 'txt': FileType.TXT, 'text': FileType.TXT}.get(ext)

        if expected_type and file_type != expected_type:
            raise FileProcessingError(
                "File content doesn't match extension",
                "TYPE_MISMATCH",
                f"File has .{ext} extension but content is {file_type.value}. "
                f"Please rename the file with the correct extension.",
            )

        # Extract text based on file type
        if file_type == FileType.PDF:
            result = self.extract_from_pdf(filepath, progress_callback)
        elif file_type == FileType.DOCX:
            result = self.extract_from_docx(filepath, progress_callback)
        elif file_type == FileType.TXT:
            result = self.extract_from_txt(filepath, progress_callback)
        else:
            raise FileProcessingError(
                "Unsupported file type", "UNSUPPORTED_TYPE", f"File type {file_type.value} is not supported"
            )

        # Validate Sanskrit content if requested
        if validate_sanskrit:
            is_valid, error = self.validate_sanskrit_content(result.text)
            if not is_valid:
                raise FileProcessingError("No Sanskrit content detected", "NO_SANSKRIT", error)

        return result


# Singleton instance for convenience
_processor = None


def get_processor() -> FileProcessor:
    """Get the singleton FileProcessor instance."""
    global _processor
    if _processor is None:
        _processor = FileProcessor()
    return _processor
