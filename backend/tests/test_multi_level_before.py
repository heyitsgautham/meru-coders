#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BEFORE Test - Multi-level Matching Implementation
Tests meter identification accuracy before implementing multi-level matching

This captures baseline performance metrics to compare against after implementation.
"""

from backend.core.chanda import Chanda
import sanskrit_text as skt

c = Chanda('backend/data/')

# Test cases covering different scenarios
test_cases = [
    {
        'name': 'Anushtubh (Classical)',
        'text': 'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।\nमा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥',
        'expected_meters': ['अनुष्टुभ्'],
        'level': 'verse',
        'type': 'exact_match'
    },
    {
        'name': 'Vasantatilaka',
        'text': 'मानसं प्रमदानां प्रथमसमागमे यत् प्रवृत्तम्',
        'expected_meters': ['वसन्ततिलका'],
        'level': 'line',
        'type': 'exact_match'
    },
    {
        'name': 'Mandakranta',
        'text': 'काश्चित्कान्ता समुपेत्य यस्तया सह मोदते',
        'expected_meters': ['मन्दाक्रान्ता'],
        'level': 'line',
        'type': 'exact_match'
    },
    {
        'name': 'Gayatri (Vedic - 24 syllables)',
        'text': 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्',
        'expected_meters': ['गायत्री'],
        'level': 'line',
        'type': 'vedic_syllable'
    },
    {
        'name': 'Mixed Meter Verse',
        'text': 'यदा यदा हि धर्मस्य ग्लानिर्भवति भारत ।\nअभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम् ॥',
        'expected_meters': ['अनुष्टुभ्'],
        'level': 'verse',
        'type': 'verse_aggregation'
    },
    {
        'name': 'Pada-level Fragment (8 syllables)',
        'text': 'समवेता युयुत्सवः',
        'expected_meters': ['गायत्री', 'अनुष्टुभ्'],
        'level': 'pada',
        'type': 'pada_match'
    },
    {
        'name': 'Short Fragment (4 syllables)',
        'text': 'धर्मक्षेत्रे',
        'expected_meters': [],  # Too short for reliable identification
        'level': 'fragment',
        'type': 'short_fragment'
    }
]

def run_test_case(test):
    """Run a single test case and return results"""
    print(f"\n{'='*80}")
    print(f"TEST: {test['name']}")
    print(f"Type: {test['type']} | Level: {test['level']}")
    print(f"{'='*80}")
    print(f"Input: {test['text'][:70]}...")
    
    # Get syllable count
    syllables = skt.get_syllables(test['text'])
    flat = [s for ln in syllables for w in ln for s in w]
    syllable_count = len(flat)
    
    # Identify meter
    if test['level'] == 'verse':
        result = c.identify_from_text(test['text'], verse=True)
        if result.get('verse') and len(result['verse']) > 0:
            verse_result = result['verse'][0]
            identified_meters = verse_result['chanda'][0] if verse_result['chanda'] else []
            confidence = verse_result['chanda'][1] if verse_result['chanda'] else 0
        else:
            identified_meters = []
            confidence = 0
    else:
        result = c.identify_line(test['text'], fuzzy=True)
        identified_meters = [name for name, pada in result.get('chanda', [])]
        confidence = len(identified_meters)
    
    # Check if expected meters are found
    found = False
    if test['expected_meters']:
        for expected in test['expected_meters']:
            if any(expected in str(m) for m in identified_meters):
                found = True
                break
    else:
        # For fragments with no expected meter, just check if system handled it
        found = True
    
    status = "✓ PASS" if found else "✗ FAIL"
    
    print(f"Syllables: {syllable_count}")
    print(f"Expected: {test['expected_meters']}")
    print(f"Identified (top 3): {identified_meters[:3] if isinstance(identified_meters, list) else identified_meters}")
    print(f"Confidence: {confidence}")
    print(f"Result: {status}")
    
    return {
        'name': test['name'],
        'type': test['type'],
        'syllables': syllable_count,
        'expected': test['expected_meters'],
        'identified': identified_meters[:3] if isinstance(identified_meters, list) else identified_meters,
        'confidence': confidence,
        'passed': found
    }

if __name__ == '__main__':
    print("="*80)
    print("BEFORE IMPLEMENTATION - Multi-level Matching Baseline Test")
    print("="*80)
    
    results = []
    for test in test_cases:
        results.append(run_test_case(test))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY - BEFORE MULTI-LEVEL MATCHING")
    print("="*80)
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    for r in results:
        status = "✓" if r['passed'] else "✗"
        print(f"{status} {r['name']}: {r['type']}")
    
    print(f"\nAccuracy: {passed}/{total} ({100*passed/total:.1f}%)")
    print("\nKey Metrics:")
    print(f"- Exact matches: {sum(1 for r in results if r['type'] == 'exact_match' and r['passed'])}/3")
    print(f"- Vedic syllable match: {sum(1 for r in results if r['type'] == 'vedic_syllable' and r['passed'])}/1")
    print(f"- Verse aggregation: {sum(1 for r in results if r['type'] == 'verse_aggregation' and r['passed'])}/1")
    print(f"- Pada-level match: {sum(1 for r in results if r['type'] == 'pada_match' and r['passed'])}/1")
    print(f"- Fragment handling: {sum(1 for r in results if r['type'] == 'short_fragment' and r['passed'])}/1")
    print("="*80)
