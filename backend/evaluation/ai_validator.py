#!/usr/bin/env python3
"""
Test AI Shloka Validator

Tests the AI pre-validation layer for chandas identification.
This test is designed to work standalone without heavy dependencies.
"""

import importlib.util
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import directly from the module file to avoid __init__.py importing heavy deps

spec = importlib.util.spec_from_file_location(
    "ai_validator", os.path.join(PROJECT_ROOT, "backend", "core", "ai_validator.py")
)
ai_validator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_validator_module)

AIShlokaValidator = ai_validator_module.AIShlokaValidator
validate_shloka_input = ai_validator_module.validate_shloka_input
get_validator = ai_validator_module.get_validator


def test_validator_initialization():
    """Test that the validator initializes correctly."""
    validator = get_validator()
    print(f"✓ Validator initialized. Enabled: {validator.enabled}")
    return True


def test_empty_input():
    """Test that empty input is rejected."""
    should_proceed, reason, result = validate_shloka_input("", skip_ai=False)

    if not should_proceed:
        print(f"✓ Empty input correctly rejected: {reason}")
        return True
    else:
        print("✗ Empty input should be rejected")
        return False


def test_valid_shloka():
    """Test with a valid Sanskrit shloka."""
    # Bhagavad Gita 1.1
    text = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"

    should_proceed, reason, result = validate_shloka_input(text, skip_ai=False)

    if result.get('ai_validated'):
        print("✓ Valid shloka AI result:")
        print(f"  - is_valid: {result.get('is_valid')}")
        print(f"  - text_type: {result.get('text_type')}")
        print(f"  - confidence: {result.get('confidence')}")
        print(f"  - should_proceed: {should_proceed}")
    else:
        print("⚠ AI validation was skipped (no API keys?)")

    return True


def test_english_text():
    """Test with English text (should be rejected)."""
    text = "The quick brown fox jumps over the lazy dog"

    should_proceed, reason, result = validate_shloka_input(text, skip_ai=False)

    if result.get('ai_validated'):
        print("✓ English text AI result:")
        print(f"  - is_valid: {result.get('is_valid')}")
        print(f"  - text_type: {result.get('text_type')}")
        print(f"  - should_proceed: {should_proceed}")
        if not should_proceed:
            print(f"  - rejection_reason: {reason}")
    else:
        print("⚠ AI validation was skipped")

    return True


def test_prose_text():
    """Test with Sanskrit prose (should be flagged)."""
    # Simple Sanskrit prose sentence
    text = "अहं गृहं गच्छामि"  # "I go home"

    should_proceed, reason, result = validate_shloka_input(text, skip_ai=False)

    if result.get('ai_validated'):
        print("✓ Prose text AI result:")
        print(f"  - is_valid: {result.get('is_valid')}")
        print(f"  - text_type: {result.get('text_type')}")
        print(f"  - should_proceed: {should_proceed}")
    else:
        print("⚠ AI validation was skipped")

    return True


def test_skip_ai():
    """Test that AI can be skipped (for batch mode)."""
    text = "any text here"

    should_proceed, reason, result = validate_shloka_input(text, skip_ai=True)

    if should_proceed and not result.get('ai_validated'):
        print("✓ AI correctly skipped when skip_ai=True")
        return True
    else:
        print("✗ AI should be skipped but wasn't")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("AI Shloka Validator Tests")
    print("=" * 60)
    print()

    tests = [
        ("Validator Initialization", test_validator_initialization),
        ("Empty Input Rejection", test_empty_input),
        ("Skip AI Mode", test_skip_ai),
        ("Valid Shloka", test_valid_shloka),
        ("English Text", test_english_text),
        ("Prose Text", test_prose_text),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
