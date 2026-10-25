"""PDF text extraction for FileProcessor, with pdfplumber first and PyMuPDF as the fallback for CID-encoded fonts.

Mixed into backend.utils.file_processor.FileProcessor, whose checks it calls through self."""

import logging
from pathlib import Path
from typing import Callable, Optional

from .file_types import ExtractionResult, FileProcessingError, FileType

logger = logging.getLogger(__name__)


class PdfExtraction:
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
