#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test English text detection to ensure English text is rejected
while valid IAST transliteration is accepted.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.chanda import Chanda
from config.settings import Settings

def test_english_detection():
    """Test that English text is properly rejected"""
    
    # Initialize Chanda
    settings = Settings()
    chanda = Chanda(data_path=str(settings.DATA_DIR))
    
    print("=" * 80)
    print("TESTING ENGLISH TEXT DETECTION")
    print("=" * 80)
    
    # Test cases: (input_text, should_reject, description)
    test_cases = [
        # Plain English - should be REJECTED
        ("hello world", True, "Simple English greeting"),
        ("the quick brown fox jumps over the lazy dog", True, "English pangram"),
        ("this is a test", True, "Simple English sentence"),
        ("I am going to the store", True, "English sentence with verbs"),
        ("hello hello hello", True, "Repeated English word"),
        ("what is your name", True, "English question"),
        ("good morning everyone", True, "English greeting"),
        
        # Valid IAST transliteration - should be ACCEPTED
        ("dharma kṣetre kurukṣetre", False, "IAST with diacritics"),
        ("rāma rāma rāma", False, "IAST with macron (ā)"),
        ("śrī kṛṣṇa", False, "IAST with ś, ṛ, ṣ"),
        ("oṃ namaḥ śivāya", False, "IAST mantra"),
        ("bhūr bhuvaḥ svaḥ", False, "IAST Gayatri"),
        
        # Devanagari - should be ACCEPTED
        ("धर्मक्षेत्रे कुरुक्षेत्रे", False, "Devanagari script"),
        ("राम राम राम", False, "Devanagari repeated"),
        ("ॐ नमः शिवाय", False, "Devanagari mantra"),
        
        # Edge cases
        ("rama rama", False, "ASCII without diacritics - could be SLP1, accept"),
        ("krsna", True, "SLP1-like with low vowel ratio - reject as uncertain"),
        ("om", False, "Om is special case"),
        ("aum", False, "Aum is special case"),
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for text, should_reject, description in test_cases:
        result = chanda.identify_line(text)
        
        is_rejected = not result.get('is_valid_input', True)
        validation_error = result.get('validation_error', '')
        
        # Check if test passed
        test_passed = (is_rejected == should_reject)
        
        status = "✅ PASS" if test_passed else "❌ FAIL"
        if test_passed:
            passed += 1
        else:
            failed += 1
        
        result_str = f"{status} | Expected: {'REJECT' if should_reject else 'ACCEPT'} | Got: {'REJECT' if is_rejected else 'ACCEPT'}"
        
        print(f"\n{result_str}")
        print(f"  Input: {text}")
        print(f"  Description: {description}")
        if is_rejected:
            print(f"  Validation Error: {validation_error}")
        
        results.append({
            'text': text,
            'description': description,
            'should_reject': should_reject,
            'is_rejected': is_rejected,
            'validation_error': validation_error,
            'passed': test_passed
        })
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed}/{len(test_cases)} tests passed")
    print("=" * 80)
    
    if failed > 0:
        print(f"\n⚠️  {failed} test(s) FAILED:")
        for r in results:
            if not r['passed']:
                print(f"  - {r['text']} ({r['description']})")
    else:
        print("\n🎉 ALL TESTS PASSED!")
    
    return failed == 0

if __name__ == '__main__':
    success = test_english_detection()
    sys.exit(0 if success else 1)
