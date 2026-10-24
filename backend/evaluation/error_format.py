#!/usr/bin/env python3
"""Test that error messages match the consistent format."""

import sys
sys.path.insert(0, '/home/harevasu/Projects/meru-coders/backend')

from core.ai_validator import validate_shloka_input, AIShlokaValidator, _rule_based_validation

def main():
    print("=" * 60)
    print("Testing Error Message Format Consistency")
    print("=" * 60)
    
    # Test with empty input - this doesn't require AI call
    # Empty input is rejected before AI is called
    validator = AIShlokaValidator(enabled=True)
    result = validator.validate_shloka('')
    should_proceed, rejection_reason = validator.should_proceed_with_identification(result)
    
    expected_prefix = "अमान्य आदान:"
    expected_contains = "(Invalid input:"
    
    print("\nTest 1: Empty input rejection format")
    if rejection_reason and rejection_reason.startswith(expected_prefix) and expected_contains in rejection_reason:
        print(f"✓ PASS: Empty input rejected with correct format")
        print(f"  Message: {rejection_reason}")
    else:
        print(f"✗ FAIL: Wrong format")
        print(f"  Got: {rejection_reason}")
    
    # Test rule-based validation directly
    print("\nTest 2: Rule-based validation format (English text)")
    rule_result = _rule_based_validation('hello world')
    _, rule_rejection = validator.should_proceed_with_identification(rule_result)
    
    if rule_rejection and rule_rejection.startswith(expected_prefix) and expected_contains in rule_rejection:
        print(f"✓ PASS: Rule-based rejection has correct format")
        print(f"  Message: {rule_rejection}")
    else:
        print(f"✗ FAIL: Wrong format")
        print(f"  Got: {rule_rejection}")
    
    # Test "aditya aditya" with rule-based validation
    print("\nTest 3: Rule-based validation format ('aditya aditya')")
    rule_result2 = _rule_based_validation('aditya aditya')
    _, rule_rejection2 = validator.should_proceed_with_identification(rule_result2)
    
    if rule_rejection2:
        if rule_rejection2.startswith(expected_prefix) and expected_contains in rule_rejection2:
            print(f"✓ PASS: 'aditya aditya' rejected with correct format")
            print(f"  Message: {rule_rejection2}")
        else:
            print(f"✗ FAIL: Wrong format")
            print(f"  Got: {rule_rejection2}")
    else:
        print(f"✗ FAIL: 'aditya aditya' was not rejected by rule-based validation")
        print(f"  Result: {rule_result2}")
    
    # Test "pratap pratap" - the bug case!
    print("\nTest 4: Rule-based validation format ('pratap pratap')")
    rule_result3 = _rule_based_validation('pratap pratap')
    _, rule_rejection3 = validator.should_proceed_with_identification(rule_result3)
    
    if rule_rejection3:
        if rule_rejection3.startswith(expected_prefix) and expected_contains in rule_rejection3:
            print(f"✓ PASS: 'pratap pratap' rejected with correct format")
            print(f"  Message: {rule_rejection3}")
        else:
            print(f"✗ FAIL: Wrong format")
            print(f"  Got: {rule_rejection3}")
    else:
        print(f"✗ FAIL: 'pratap pratap' was NOT rejected - BUG!")
        print(f"  Result: {rule_result3}")
    
    # Test valid Devanagari - should pass
    print("\nTest 5: Valid Devanagari input (should be accepted)")
    rule_result4 = _rule_based_validation('धर्मक्षेत्रे कुरुक्षेत्रे')
    _, rule_rejection4 = validator.should_proceed_with_identification(rule_result4)
    
    if not rule_rejection4:
        print(f"✓ PASS: Valid Devanagari accepted")
    else:
        print(f"✗ FAIL: Valid Devanagari was rejected!")
        print(f"  Reason: {rule_rejection4}")
    
    # Test valid IAST - should pass
    print("\nTest 6: Valid IAST input (should be accepted)")
    rule_result5 = _rule_based_validation('dharmakṣetre kurukṣetre')
    _, rule_rejection5 = validator.should_proceed_with_identification(rule_result5)
    
    if not rule_rejection5:
        print(f"✓ PASS: Valid IAST accepted")
    else:
        print(f"✗ FAIL: Valid IAST was rejected!")
        print(f"  Reason: {rule_rejection5}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
