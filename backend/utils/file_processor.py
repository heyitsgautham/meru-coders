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
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Tuple

logger = logging.getLogger(__name__)


class FileType(Enum):
    """Supported file types."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    UNKNOWN = "unknown"


class FileProcessingError(Exception):
    """Custom exception for file processing errors."""

    def __init__(self, message: str, error_code: str, details: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

    def to_dict(self):
        return {"error": self.message, "error_code": self.error_code, "details": self.details}


@dataclass
class ExtractionResult:
    """Result of text extraction from a file."""

    text: str
    file_type: FileType
    page_count: int
    encoding: Optional[str] = None
    warnings: Optional[list] = None


class FileProcessor:
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

    def get_file_extension(self, filename: str) -> str:
        """Extract and normalize file extension."""
        if '.' not in filename:
            return ''
        return filename.rsplit('.', 1)[1].lower()

    def detect_file_type(self, filepath: Path) -> FileType:
        """
        Detect the actual file type using magic numbers.

        Falls back to extension-based detection if python-magic unavailable.
        """
        if self._has_magic:
            try:
                import magic

                mime = magic.from_file(str(filepath), mime=True)

                if mime in self.MIME_TYPE_MAP:
                    return self.MIME_TYPE_MAP[mime]

                # Handle edge cases
                if mime.startswith('text/'):
                    return FileType.TXT

            except Exception as e:
                logger.warning(f"Magic detection failed: {e}, falling back to extension")

        # Fallback to extension
        ext = self.get_file_extension(filepath.name)
        if ext == 'pdf':
            return FileType.PDF
        elif ext == 'docx':
            return FileType.DOCX
        elif ext in ('txt', 'text'):
            return FileType.TXT

        return FileType.UNKNOWN

    def validate_file(self, filepath: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate file before processing.

        Checks:
        - File exists
        - File size within limit
        - Extension is allowed

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filepath.exists():
            return False, "File not found"

        # Check file size
        file_size = filepath.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            return False, f"File too large ({size_mb:.1f}MB). Maximum allowed: 10MB"

        if file_size == 0:
            return False, "File is empty"

        # Check extension
        ext = self.get_file_extension(filepath.name)
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"Unsupported file type '.{ext}'. Allowed: PDF, DOCX, TXT"

        return True, None

    def validate_sanskrit_content(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that extracted text contains Sanskrit/Devanagari content.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "No text content extracted from file"

        # Count Devanagari characters
        devanagari_chars = len(self.DEVANAGARI_PATTERN.findall(text))

        # Count IAST characters
        iast_matches = len(self.IAST_PATTERN.findall(text))

        total_sanskrit_indicators = devanagari_chars + iast_matches

        # Check minimum character count
        if total_sanskrit_indicators < self.MIN_SANSKRIT_CHARS:
            return False, (
                f"No Sanskrit content detected. Found only {total_sanskrit_indicators} "
                f"Sanskrit/Devanagari characters. Please upload a file containing "
                f"Sanskrit text in Devanagari script or IAST transliteration."
            )

        # Check ratio (for longer texts)
        text_length = len(text.strip())
        if text_length > 100:
            ratio = total_sanskrit_indicators / text_length
            if ratio < self.MIN_SANSKRIT_RATIO:
                return False, (
                    f"Insufficient Sanskrit content ({ratio * 100:.1f}% Sanskrit characters). "
                    f"The file appears to contain mostly non-Sanskrit text. "
                    f"Please upload a file with Sanskrit content."
                )

        return True, None

    def check_cid_encoding(self, text: str) -> Tuple[bool, float]:
        """
        Check if extracted text contains CID (Character ID) markers.

        CID markers like (cid:XX) appear when PDF fonts use custom encodings
        that pdfplumber/pdfminer cannot decode. This is common with:
        - Sanskrit PDFs with embedded Devanagari fonts
        - PDFs created with certain Indian language typesetting software
        - Scanned PDFs with OCR that used custom font mappings

        Args:
            text: Extracted text to check

        Returns:
            Tuple of (has_cid_issues, cid_ratio)
            - has_cid_issues: True if significant CID markers found
            - cid_ratio: Ratio of CID markers to total text length
        """
        if not text:
            return False, 0.0

        cid_matches = self.CID_PATTERN.findall(text)
        cid_count = len(cid_matches)

        if cid_count == 0:
            return False, 0.0

        # Calculate the ratio of CID markers
        text_length = len(text)
        # Each CID marker is ~8 chars like "(cid:12)"
        cid_char_count = sum(len(m) for m in cid_matches)
        cid_ratio = cid_char_count / text_length if text_length > 0 else 0

        # If more than 10% of the text is CID markers, consider it problematic
        has_issues = cid_ratio > 0.10 or cid_count > 20

        logger.debug(f"CID check: {cid_count} markers, {cid_ratio:.2%} of text")

        return has_issues, cid_ratio

    def clean_cid_text(self, text: str) -> str:
        """
        Remove CID markers from text and clean up resulting whitespace.

        Args:
            text: Text with potential CID markers

        Returns:
            Cleaned text with CID markers removed
        """
        # Remove CID markers
        cleaned = self.CID_PATTERN.sub('', text)

        # Clean up multiple spaces
        cleaned = re.sub(r' +', ' ', cleaned)

        # Clean up multiple newlines
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)

        return cleaned.strip()

    def extract_from_pdf(
        self, filepath: Path, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ExtractionResult:
        """
        Extract text from a PDF file.

        Args:
            filepath: Path to the PDF file
            progress_callback: Optional callback(current_page, total_pages)

        Raises:
            FileProcessingError: If PDF is corrupted, password-protected, or image-based
        """
        if not self._has_pdfplumber and not self._has_pymupdf:
            raise FileProcessingError(
                "PDF processing not available", "PDF_UNAVAILABLE", "No PDF library is installed (pdfplumber or PyMuPDF)"
            )

        # Try pdfplumber first if available
        if self._has_pdfplumber:
            result = self._extract_pdf_pdfplumber(filepath, progress_callback)

            # If we got CID issues and have PyMuPDF, try that instead
            if result.warnings and self._has_pymupdf:
                has_cid_warning = any(
                    'could not be extracted' in w.lower() or 'text loss' in w.lower() for w in result.warnings
                )
                if has_cid_warning:
                    logger.info("Trying PyMuPDF as fallback due to CID encoding issues")
                    try:
                        pymupdf_result = self._extract_pdf_pymupdf(filepath, progress_callback)
                        # Compare results - use PyMuPDF if it got more Devanagari chars
                        pdfplumber_devanagari = len(self.DEVANAGARI_PATTERN.findall(result.text))
                        pymupdf_devanagari = len(self.DEVANAGARI_PATTERN.findall(pymupdf_result.text))

                        if pymupdf_devanagari > pdfplumber_devanagari:
                            logger.info(
                                f"PyMuPDF extracted more Sanskrit text ({pymupdf_devanagari} vs {pdfplumber_devanagari} Devanagari chars)"
                            )
                            return pymupdf_result
                        else:
                            logger.info(
                                f"pdfplumber result kept ({pdfplumber_devanagari} vs {pymupdf_devanagari} Devanagari chars)"
                            )
                    except Exception as e:
                        logger.warning(f"PyMuPDF fallback failed: {e}")

            return result

        # Fall back to PyMuPDF only
        return self._extract_pdf_pymupdf(filepath, progress_callback)

    def _extract_pdf_pdfplumber(
        self, filepath: Path, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ExtractionResult:
        """
        Extract text from PDF using pdfplumber.

        Args:
            filepath: Path to the PDF file
            progress_callback: Optional callback(current_page, total_pages)
        """
        import pdfplumber

        try:
            text_parts = []
            page_count = 0

            with pdfplumber.open(str(filepath)) as pdf:
                page_count = len(pdf.pages)

                if page_count == 0:
                    raise FileProcessingError(
                        "PDF file has no pages", "PDF_EMPTY", "The uploaded PDF file contains no pages"
                    )

                for i, page in enumerate(pdf.pages):
                    # Report progress
                    if progress_callback:
                        progress_callback(i + 1, page_count)

                    # Extract text from page
                    page_text = page.extract_text()

                    if page_text:
                        text_parts.append(page_text)
                    else:
                        # Page has no extractable text - might be image-based
                        logger.warning(f"Page {i + 1} has no extractable text")

            # Combine all pages
            full_text = '\n\n'.join(text_parts)

            # Check if we got any text
            if not full_text.strip():
                raise FileProcessingError(
                    "No text could be extracted from PDF",
                    "PDF_NO_TEXT",
                    "This appears to be an image-based or scanned PDF. "
                    "Please upload a text-based PDF or use the Image OCR feature.",
                )

            # Check for CID encoding issues (common with Sanskrit/Devanagari PDFs)
            has_cid_issues, cid_ratio = self.check_cid_encoding(full_text)

            if has_cid_issues:
                # Always try to clean and salvage what we can
                cleaned_text = self.clean_cid_text(full_text)

                # Check what we have after cleaning
                devanagari_chars = len(self.DEVANAGARI_PATTERN.findall(cleaned_text))
                cleaned_length = len(cleaned_text.strip())

                # Calculate what % of the CLEANED text is actual Devanagari/Sanskrit
                # This tells us if we got good content or not
                devanagari_ratio = devanagari_chars / cleaned_length if cleaned_length > 0 else 0

                logger.info(
                    f"PDF CID cleanup: {cid_ratio:.1%} was CID markers. "
                    f"After cleaning: {cleaned_length} chars, {devanagari_chars} Devanagari chars ({devanagari_ratio:.1%})"
                )

                # Only reject if we have almost nothing left
                if devanagari_chars < 3 and cleaned_length < 20:
                    raise FileProcessingError(
                        "PDF text extraction failed",
                        "PDF_CID_ENCODING",
                        "This PDF uses custom font encoding that could not be decoded. "
                        "After attempting recovery, no usable Sanskrit text remained.\n\n"
                        "**Recommended:** Use the 'Image OCR' feature:\n"
                        "1. Open the PDF in a viewer\n"
                        "2. Take a screenshot of the text\n"
                        "3. Upload the screenshot using 'Image OCR'",
                    )

                # We have some usable text! Return it with appropriate warning
                full_text = cleaned_text

                # Determine warning severity based on content quality, not just CID ratio
                # If we have good Devanagari content (>30%), the CID markers were likely just noise
                if devanagari_ratio > 0.30:
                    # Good extraction - CID markers were mostly font metadata/noise
                    if cid_ratio > 0.30:
                        warning_msg = (
                            "ℹ️ Some font metadata was cleaned from the PDF. "
                            "The Sanskrit text appears to be extracted successfully. "
                            "Please verify the text looks correct before analysis."
                        )
                    else:
                        warning_msg = "Minor cleanup was performed on the extracted text."
                elif devanagari_ratio > 0.15:
                    # Moderate - some content may be missing
                    warning_msg = (
                        "⚠️ Some characters could not be extracted due to PDF font encoding. "
                        "The text may have minor gaps. Review carefully before analysis."
                    )
                else:
                    # Poor extraction - significant content loss likely
                    warning_msg = (
                        "⚠️ Significant text extraction issues detected. "
                        "Many characters could not be extracted due to PDF font encoding. "
                        "For complete text, use 'Image OCR' with a screenshot of the PDF."
                    )

                return ExtractionResult(
                    text=full_text.strip(), file_type=FileType.PDF, page_count=page_count, warnings=[warning_msg]
                )

            return ExtractionResult(text=full_text.strip(), file_type=FileType.PDF, page_count=page_count)

        except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as e:
            raise FileProcessingError(
                "Corrupted PDF file", "PDF_CORRUPTED", f"The PDF file appears to be corrupted: {str(e)}"
            ) from e
        except Exception as e:
            error_str = str(e).lower()

            if 'password' in error_str or 'encrypted' in error_str:
                raise FileProcessingError(
                    "Password-protected PDF",
                    "PDF_PASSWORD_PROTECTED",
                    "This PDF is password-protected. Please remove the password and try again.",
                ) from e

            if 'invalid' in error_str or 'corrupt' in error_str:
                raise FileProcessingError(
                    "Invalid PDF file", "PDF_INVALID", f"The file does not appear to be a valid PDF: {str(e)}"
                ) from e

            raise FileProcessingError("Failed to process PDF", "PDF_ERROR", str(e)) from e

    def _extract_pdf_pymupdf(
        self, filepath: Path, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ExtractionResult:
        """
        Extract text from PDF using PyMuPDF (fitz).

        PyMuPDF often handles Sanskrit/Devanagari PDFs better than pdfplumber,
        especially when fonts use custom CID encodings.

        Args:
            filepath: Path to the PDF file
            progress_callback: Optional callback(current_page, total_pages)
        """
        import fitz  # PyMuPDF

        try:
            text_parts = []
            page_count = 0

            with fitz.open(str(filepath)) as pdf:
                page_count = len(pdf)

                if page_count == 0:
                    raise FileProcessingError(
                        "PDF file has no pages", "PDF_EMPTY", "The uploaded PDF file contains no pages"
                    )

                for i, page in enumerate(pdf):
                    # Report progress
                    if progress_callback:
                        progress_callback(i + 1, page_count)

                    # Extract text - PyMuPDF has better Unicode handling
                    page_text = page.get_text("text")

                    if page_text and page_text.strip():
                        text_parts.append(page_text)
                    else:
                        logger.warning(f"Page {i + 1} has no extractable text (PyMuPDF)")

            # Combine all pages
            full_text = '\n\n'.join(text_parts)

            # Check if we got any text
            if not full_text.strip():
                raise FileProcessingError(
                    "No text could be extracted from PDF",
                    "PDF_NO_TEXT",
                    "This appears to be an image-based or scanned PDF. "
                    "Please upload a text-based PDF or use the Image OCR feature.",
                )

            # Still check for CID issues (PyMuPDF can also have them, but less often)
            has_cid_issues, cid_ratio = self.check_cid_encoding(full_text)

            if has_cid_issues:
                cleaned_text = self.clean_cid_text(full_text)
                devanagari_chars = len(self.DEVANAGARI_PATTERN.findall(cleaned_text))
                cleaned_length = len(cleaned_text.strip())
                devanagari_ratio = devanagari_chars / cleaned_length if cleaned_length > 0 else 0

                if devanagari_chars < 3 and cleaned_length < 20:
                    raise FileProcessingError(
                        "PDF text extraction failed",
                        "PDF_CID_ENCODING",
                        "This PDF uses custom font encoding that could not be decoded. "
                        "Please use the 'Image OCR' feature with a screenshot of the PDF.",
                    )

                full_text = cleaned_text

                # Use content-based warning (same logic as pdfplumber)
                if devanagari_ratio > 0.30:
                    if cid_ratio > 0.30:
                        warning_msg = (
                            "ℹ️ Some font metadata was cleaned from the PDF. "
                            "The Sanskrit text appears to be extracted successfully."
                        )
                    else:
                        warning_msg = "Minor cleanup was performed on the extracted text."

                    return ExtractionResult(
                        text=full_text.strip(), file_type=FileType.PDF, page_count=page_count, warnings=[warning_msg]
                    )
                elif devanagari_ratio > 0.15:
                    return ExtractionResult(
                        text=full_text.strip(),
                        file_type=FileType.PDF,
                        page_count=page_count,
                        warnings=["⚠️ Some characters could not be extracted. Review carefully before analysis."],
                    )

            return ExtractionResult(text=full_text.strip(), file_type=FileType.PDF, page_count=page_count)

        except fitz.FileDataError as e:
            raise FileProcessingError(
                "Corrupted PDF file", "PDF_CORRUPTED", f"The PDF file appears to be corrupted: {str(e)}"
            ) from e
        except Exception as e:
            error_str = str(e).lower()

            if 'password' in error_str or 'encrypted' in error_str:
                raise FileProcessingError(
                    "Password-protected PDF",
                    "PDF_PASSWORD_PROTECTED",
                    "This PDF is password-protected. Please remove the password and try again.",
                ) from e

            raise FileProcessingError("Failed to process PDF with PyMuPDF", "PDF_ERROR", str(e)) from e

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
