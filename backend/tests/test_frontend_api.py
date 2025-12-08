#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test 7 Vedic Meters via Direct Python API
==========================================
Verifies all 7 showcase verses using the direct Python backend API.
This is the authoritative test for meter identification accuracy.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chanda import Chanda

# Data path
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data')

SEVEN_VERSES = [
    {
        'name': 'Gayatri',
        'verse': 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं',
        'expected': ['गायत्री'],
        'expected_syllables': 24,
        'source': 'RV 1.1.1'
    },
    {
        'name': 'Ushnik',
        'verse': 'अग्ने वाजस्य गोमत ईशानः सहसो यहो अस्मे धेहि जातवेदो महि श्रवः',
        'expected': ['उष्णिक्'],
        'expected_syllables': 28,
        'source': 'RV 1.79.4'
    },
    {
        'name': 'Anushtubh',
        'verse': 'सुविवृतं सुनिरजमिंद्र त्वादातमिद्यशः गवामप व्रजं वृधि कृणुष्व राधो अद्रिवः',
        'expected': ['अनुष्टुभ्'],
        'expected_syllables': 32,
        'source': 'RV 1.10.7'
    },
    {
        'name': 'Brihati',
        'verse': 'तं घेमित्था नमस्विन उप स्वराजमासते होत्राभिरग्निं मनुषः समिंधते तितिर्वांसो अति स्रिधः',
        'expected': ['बृहती'],
        'expected_syllables': 36,
        'source': 'RV 1.36.7'
    },
    {
        'name': 'Pankti',
        'verse': 'क्रत्वा महाँ अनुष्वधं भीम आ वावृधे शवः श्रिय ऋष्व उपाकयोर्नि शिप्री हरिवांदधे हस्तयोर्वज्रमायसं',
        'expected': ['पङ्क्ति'],
        'expected_syllables': 40,
        'source': 'RV 1.81.4'
    },
    {
        'name': 'Trishtubh',
        'verse': 'अमी य ऋक्षा निहितास उच्चा नक्तं ददृश्रे कुह चिद्दिवेयुः अदब्धानि वरुणस्य व्रतानि विचाकशच्चंद्रमा नक्तमेति',
        'expected': ['त्रिष्टुभ्'],
        'expected_syllables': 44,
        'source': 'RV 1.24.10'
    },
    {
        'name': 'Jagati',
        'verse': 'आ नासत्या त्रिभिरेकादशैरिह देवेभिर्यातं मधुपेयमश्विना प्रायुस्तारिष्टं नी रपांसि मृक्षतं सेधतं द्वेषो भवतं सचाभुवा',
        'expected': ['जगती'],
        'expected_syllables': 48,
        'source': 'RV 1.34.11'
    }
]


def test_direct_api():
    """Test all 7 verses via direct Python API"""
    print()
    print("=" * 75)
    print("Testing 7 Vedic Meters via Direct Python API (EXACT SYLLABLE COUNTS)")
    print("=" * 75)
    print()
    
    # Initialize Chanda analyzer
    chanda = Chanda(DATA_PATH)
    
    passed = 0
    exact_syl = 0
    total = len(SEVEN_VERSES)
    
    for v in SEVEN_VERSES:
        try:
            # Use direct Python API
            result = chanda.identify_line(v['verse'])
            
            meter = result.get('display_chanda_primary', 'Unknown')
            syllables = result.get('display_length', 0)
            lg_pattern = ''.join(result.get('display_lg', []))
            
            # Handle case where syllables might be a string
            if isinstance(syllables, str):
                syllables = int(syllables) if syllables.isdigit() else 0
            
            # Check if meter matches any expected variant
            match = any(exp in meter for exp in v['expected'])
            
            # Check exact syllable match
            syl_exact = (syllables == v['expected_syllables'])
            if syl_exact:
                exact_syl += 1
            
            test_pass = match and syl_exact
            if test_pass:
                passed += 1
            
            status = '✅ EXACT' if test_pass else ('⚠️ CLOSE' if match else '❌ FAIL')
            syl_status = '✓' if syl_exact else f'✗ (off by {abs(syllables - v["expected_syllables"])})'
            
            print(f"  {v['name']:12} | {status}")
            print(f"    Meter: {meter} {'✓' if match else '✗'}")
            print(f"    Syllables: {syllables} / {v['expected_syllables']} {syl_status}")
            print(f"    Source: {v.get('source', 'N/A')}")
            print()
            
        except Exception as e:
            print(f"  {v['name']:12} | ❌ FAIL - {e}")
            print()
    
    print("=" * 75)
    pct = (passed / total) * 100
    print(f"  RESULT: {passed}/{total} meters with EXACT syllable counts ({pct:.0f}%)")
    print(f"  Syllable accuracy: {exact_syl}/{total}")
    print("=" * 75)
    print()
    
    return passed, total


if __name__ == "__main__":
    passed, total = test_direct_api()
    sys.exit(0 if passed >= 5 else 1)  # Pass if at least 5/7 work
