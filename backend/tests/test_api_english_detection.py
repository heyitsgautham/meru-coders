#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API endpoints for English text detection
"""

import sys
import os
import json

# Add parent (project root) to path so 'backend' module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app import create_app

def test_api_english_detection():
    """Test API endpoints with English and Sanskrit text"""
    
    print("=" * 80)
    print("TESTING API ENGLISH TEXT DETECTION")
    print("=" * 80)
    
    # Create test client
    app = create_app()
    client = app.test_client()
    
    # Test cases
    test_cases = [
        {
            "input": "hello world",
            "should_reject": True,
            "description": "English greeting"
        },
        {
            "input": "the quick brown fox jumps over the lazy dog",
            "should_reject": True,
            "description": "English pangram"
        },
        {
            "input": "dharma kṣetre kurukṣetre",
            "should_reject": False,
            "description": "Valid IAST"
        },
        {
            "input": "धर्मक्षेत्रे कुरुक्षेत्रे",
            "should_reject": False,
            "description": "Valid Devanagari"
        },
        {
            "input": "rāma rāma rāma",
            "should_reject": False,
            "description": "IAST with macron"
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        # Test /api/identify/text endpoint
        response = client.post('/api/identify/text',
                              data=json.dumps({"text": test["input"], "text_mode": "line"}),
                              content_type='application/json')
        
        data = json.loads(response.data)
        
        # Check if it was rejected
        is_rejected = False
        if data.get('success') == False:
            is_rejected = True
        elif 'result' in data and 'line' in data['result']:
            for line_result in data['result']['line']:
                if not line_result.get('result', {}).get('found', True):
                    is_rejected = True
                    break
        
        # Determine if test passed
        test_passed = (is_rejected == test["should_reject"])
        
        status = "✅ PASS" if test_passed else "❌ FAIL"
        if test_passed:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} | Expected: {'REJECT' if test['should_reject'] else 'ACCEPT'} | Got: {'REJECT' if is_rejected else 'ACCEPT'}")
        print(f"  Input: {test['input']}")
        print(f"  Description: {test['description']}")
        if is_rejected:
            print(f"  Error: {data.get('error', 'N/A')}")
    
    print("\n" + "=" * 80)
    print(f"API TEST RESULTS: {passed}/{len(test_cases)} tests passed")
    print("=" * 80)
    
    if failed > 0:
        print(f"\n⚠️  {failed} test(s) FAILED")
    else:
        print("\n🎉 ALL API TESTS PASSED!")
    
    return failed == 0

if __name__ == '__main__':
    success = test_api_english_detection()
    sys.exit(0 if success else 1)
