#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test to reproduce the उष्णिक् confidence issue
where it shows "14 syllables" instead of "28 syllables"
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from core.chanda import Chanda

def test_usnik_confidence():
    """Test उष्णिक् confidence reporting"""
    data_path = os.path.join(os.path.dirname(__file__), 'data')
    chanda = Chanda(data_path)
    
    # Your test verse (उष्णिक् - 28 syllables = 4×7)
    verse = "यत्र द्वा विव ज घ ना धिष वण्या कृता। उ लू ख ल सु ता ना म वे द्विं द्र ज ल्गुलः"
    
    print("=" * 80)
    print("Testing उष्णिक् Confidence Issue")
    print("=" * 80)
    print(f"\nInput verse: {verse}")
    
    # Identify the verse
    result = chanda.identify_line(verse)
    
    print(f"\n✓ Found: {result.get('found')}")
    print(f"✓ Primary Meter: {result.get('display_chanda_primary')}")
    
    # Check syllable count
    lg_pattern = ''.join(result.get('lg', []))
    actual_syllable_count = len(lg_pattern)
    print(f"✓ Actual syllable count: {actual_syllable_count}")
    
    # Check confidence scores
    confidence_scores = result.get('confidence_scores', {})
    print(f"\n📊 Confidence Scores:")
    for meter, (conf, match_type) in confidence_scores.items():
        print(f"   - {meter}: {conf:.1f} ({match_type})")
    
    # Check primary confidence reason
    primary_reason = result.get('primary_confidence_reason')
    if primary_reason:
        print(f"\n🔍 Primary Confidence Reason:")
        print(f"   Match Type: {primary_reason.get('match_type')}")
        print(f"   Confidence: {primary_reason.get('confidence')}")
        print(f"   Level: {primary_reason.get('level')}")
        print(f"   Reason Text: {primary_reason.get('reason')}")
        
        # Check technical details for syllable count
        tech_details = primary_reason.get('technical_details', {})
        reported_syllables = tech_details.get('syllable_count')
        print(f"\n⚠️  ISSUE CHECK:")
        print(f"   Reported syllable count in confidence: {reported_syllables}")
        print(f"   Actual syllable count: {actual_syllable_count}")
        
        if reported_syllables != actual_syllable_count:
            print(f"\n❌ BUG CONFIRMED!")
            print(f"   Expected: {actual_syllable_count} syllables")
            print(f"   Got: {reported_syllables} syllables")
            print(f"   Difference: {actual_syllable_count - reported_syllables} syllables missing")
        else:
            print(f"\n✅ No bug - syllable count is correct")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_usnik_confidence()
