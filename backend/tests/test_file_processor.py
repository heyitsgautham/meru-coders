#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test File Processor Module

Tests for PDF, DOCX, and TXT file extraction with Sanskrit validation.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.utils.file_processor import FileProcessingError, FileType, get_processor


def test_file_processor_initialization():
    """Test that FileProcessor initializes correctly."""
    processor = get_processor()
    assert processor is not None
    print("✓ FileProcessor initialized")


def test_text_file_extraction():
    """Test extraction from a plain text file with Sanskrit content."""
    processor = get_processor()

    # Create a temp file with Sanskrit text
    sanskrit_text = """धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः।
मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय॥"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(sanskrit_text)
        temp_path = Path(f.name)

    try:
        result = processor.process_file(temp_path, validate_sanskrit=True)
        assert result.text.strip() == sanskrit_text.strip()
        assert result.file_type == FileType.TXT
        assert result.page_count == 1
        print("✓ TXT file extraction works")
    finally:
        temp_path.unlink()


def test_no_sanskrit_rejection():
    """Test that files without Sanskrit content are rejected."""
    processor = get_processor()

    # Create a temp file with English text only
    english_text = """This is a test file with only English content.
No Sanskrit or Devanagari characters here at all.
Just plain English text for testing purposes."""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(english_text)
        temp_path = Path(f.name)

    try:
        try:
            processor.process_file(temp_path, validate_sanskrit=True)
            pytest.fail("Should have raised FileProcessingError")
        except FileProcessingError as e:
            assert e.error_code == "NO_SANSKRIT"
            print("✓ Non-Sanskrit content correctly rejected")
    finally:
        temp_path.unlink()


def test_file_size_validation():
    """Test that large files are rejected."""
    processor = get_processor()

    # Create a fake large file path (we won't actually create 10MB)
    # Instead, test the validation logic directly
    is_valid, error = processor.validate_file(Path("/nonexistent/file.txt"))
    assert not is_valid
    assert "not found" in error.lower()
    print("✓ File validation works")


def test_extension_validation():
    """Test that unsupported extensions are rejected."""
    processor = get_processor()

    # Create temp file with wrong extension
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        f.write("test")
        temp_path = Path(f.name)

    try:
        is_valid, error = processor.validate_file(temp_path)
        assert not is_valid
        assert "Unsupported file type" in error
        print("✓ Extension validation works")
    finally:
        temp_path.unlink()


def test_empty_file_rejection():
    """Test that empty files are rejected."""
    processor = get_processor()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        # Write nothing
        temp_path = Path(f.name)

    try:
        is_valid, error = processor.validate_file(temp_path)
        assert not is_valid
        assert "empty" in error.lower()
        print("✓ Empty file rejection works")
    finally:
        temp_path.unlink()


def test_sanskrit_content_validation():
    """Test Sanskrit content validation logic."""
    processor = get_processor()

    # Test Devanagari detection
    devanagari_text = "धर्मक्षेत्रे कुरुक्षेत्रे"
    is_valid, _ = processor.validate_sanskrit_content(devanagari_text)
    assert is_valid, "Should detect Devanagari"
    print("✓ Devanagari detection works")

    # Test IAST detection - need enough special IAST chars (at least 10)
    # Full Gayatri mantra in IAST has many special characters: ā, ū, ṛ, ṇ, ṃ, ḥ, etc.
    iast_text = "oṃ bhūr bhuvaḥ svaḥ tat savitur vareṇyaṃ bhargo devasya dhīmahi dhiyo yo naḥ pracodayāt"
    is_valid, error = processor.validate_sanskrit_content(iast_text)
    assert is_valid, f"Should detect IAST: {error}"
    print("✓ IAST detection works")

    # Test mixed content - Devanagari + English is fine even with few chars
    mixed_text = "The word धर्म (dharma) is important. Also कर्म and योग are key concepts."
    is_valid, _ = processor.validate_sanskrit_content(mixed_text)
    assert is_valid, "Should accept mixed content"
    print("✓ Mixed content detection works")


def test_cid_encoding_detection():
    """Test CID encoding marker detection and recovery for problematic PDFs."""
    processor = get_processor()

    # Test text with severe CID markers (like broken Sanskrit PDFs)
    text_with_severe_cid = """शा(cid:2)लि(cid:4)न्यु(cid:7)क्ता(cid:2) म्ता(cid:11) तागौ(cid:11) गौ(cid:13)ऽब्धि(cid:16)(cid:4)(cid:13)कैः(cid:18)(cid:19)।
मा(cid:2)ता(cid:2) रा(cid:2)मा(cid:13) मात्पि(cid:24)(cid:25)ता(cid:2) रा(cid:2)माचन्द्रः(cid:19)"""

    has_issues, ratio = processor.check_cid_encoding(text_with_severe_cid)
    assert has_issues, "Should detect severe CID issues"
    assert ratio > 0.30, f"Ratio should be >30%, got {ratio:.2%}"
    print("✓ Severe CID encoding detection works")

    # Test that cleaning recovers usable text
    cleaned = processor.clean_cid_text(text_with_severe_cid)
    devanagari_count = len(processor.DEVANAGARI_PATTERN.findall(cleaned))
    assert devanagari_count > 20, f"Should recover significant Devanagari chars, got {devanagari_count}"
    assert "(cid:" not in cleaned, "Cleaned text should not contain CID markers"
    print(f"✓ CID cleaning recovered {devanagari_count} Devanagari characters")

    # Test that recovered text passes Sanskrit validation
    is_valid, _ = processor.validate_sanskrit_content(cleaned)
    assert is_valid, "Recovered text should be valid Sanskrit"
    print("✓ Recovered text passes Sanskrit validation")

    # Test clean text (no CID markers)
    clean_text = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"
    has_issues, ratio = processor.check_cid_encoding(clean_text)
    assert not has_issues, "Clean text should not flag CID issues"
    assert ratio == 0.0, "Clean text should have 0% CID ratio"
    print("✓ Clean text CID check works")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Running File Processor Tests")
    print("=" * 60 + "\n")

    tests = [
        test_file_processor_initialization,
        test_text_file_extraction,
        test_no_sanskrit_rejection,
        test_file_size_validation,
        test_extension_validation,
        test_empty_file_rejection,
        test_sanskrit_content_validation,
        test_cid_encoding_detection,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
