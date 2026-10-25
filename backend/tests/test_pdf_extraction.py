"""PDF extraction through pdfplumber and the PyMuPDF fallback, on PDFs built in the test."""

import fitz
import pytest

from backend.utils.file_processor import FileProcessingError, FileProcessor, FileType
from backend.utils.pdf_extraction import PdfExtraction

LINES = ["dharmaksetre kuruksetre samaveta yuyutsavah", "mamakah pandavascaiva kimakurvata sanjaya"]


def make_pdf(path, pages):
    """Write a PDF with one page per entry; an entry is a list of text lines, or None for a blank page."""
    doc = fitz.open()
    for lines in pages:
        page = doc.new_page()
        for i, line in enumerate(lines or []):
            page.insert_text((72, 72 + 20 * i), line)
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def processor():
    return FileProcessor()


def test_processor_includes_the_pdf_mixin():
    assert issubclass(FileProcessor, PdfExtraction)


@pytest.mark.parametrize("method", ["_extract_pdf_pdfplumber", "_extract_pdf_pymupdf"])
def test_both_backends_read_every_page(tmp_path, processor, method):
    pdf = make_pdf(tmp_path / "gita.pdf", [LINES, ["page two"]])
    result = getattr(processor, method)(pdf, None)
    assert result.file_type == FileType.PDF
    assert result.page_count == 2
    assert LINES[0] in result.text and "page two" in result.text


def test_progress_is_reported_per_page(tmp_path, processor):
    pdf = make_pdf(tmp_path / "gita.pdf", [LINES, LINES, LINES])
    seen = []
    processor.extract_from_pdf(pdf, progress_callback=lambda current, total: seen.append((current, total)))
    assert seen[-1] == (3, 3)


def test_a_corrupted_pdf_is_rejected(tmp_path, processor):
    pdf = tmp_path / "broken.pdf"
    pdf.write_bytes(b"%PDF-1.4\nthis is not a pdf body")
    with pytest.raises(FileProcessingError) as error:
        processor.extract_from_pdf(pdf)
    assert error.value.error_code in {"PDF_CORRUPTED", "PDF_ERROR", "PDF_EMPTY"}


def test_without_any_pdf_library_extraction_is_unavailable(tmp_path, processor):
    processor._has_pdfplumber = processor._has_pymupdf = False
    with pytest.raises(FileProcessingError) as error:
        processor.extract_from_pdf(make_pdf(tmp_path / "gita.pdf", [LINES]))
    assert error.value.error_code == "PDF_UNAVAILABLE"


def test_pymupdf_alone_still_extracts(tmp_path, processor):
    processor._has_pdfplumber = False
    result = processor.extract_from_pdf(make_pdf(tmp_path / "gita.pdf", [LINES]))
    assert LINES[1] in result.text


def test_a_pdf_without_text_is_rejected(tmp_path, processor):
    pdf = make_pdf(tmp_path / "scan.pdf", [None, None])
    with pytest.raises(FileProcessingError) as error:
        processor.extract_from_pdf(pdf)
    assert error.value.error_code == "PDF_NO_TEXT"


@pytest.mark.parametrize("method", ["_extract_pdf_pdfplumber", "_extract_pdf_pymupdf"])
def test_each_backend_keeps_its_specific_error(tmp_path, processor, method):
    pdf = make_pdf(tmp_path / "scan.pdf", [None])
    with pytest.raises(FileProcessingError) as error:
        getattr(processor, method)(pdf, None)
    assert error.value.error_code == "PDF_NO_TEXT"
    assert "Image OCR" in error.value.details
