"""File type detection, size and extension checks, Sanskrit content checks and
CID-encoding cleanup for FileProcessor.

Mixed into backend.utils.file_processor.FileProcessor, which defines the limits
and patterns these checks read.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple

from .file_types import FileType

logger = logging.getLogger(__name__)


class FileChecks:
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
