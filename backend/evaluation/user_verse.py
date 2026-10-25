#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test for user-provided Vedic verse"""

from backend.config.settings import settings
from backend.core.chanda import Chanda


def test_vedic_verse():
    """Test the user's Vedic verse in auto-detect mode"""

    # Initialize Chanda
    chanda = Chanda(data_path=str(settings.DATA_DIR))

    # User's verse (appears to be from Rigveda - Tristubh meter)
    verse_text = """दिश॒श्चत॑स्रोऽश्वत॒र्यो देवर॒थस्य॑ पुरो॒डाशाः॑ श॒फा अन्तरि॑क्षमु॒द्धिः ।
द्यावा॑पृथि॒वी पक्ष॑सी ऋ॒तवो॒ऽभीश॑वोऽन्तर्दे॒शाः किं॑क॒रा वाक् परि॑रथ्यम् ॥"""

    print("=" * 80)
    print("TESTING VEDIC VERSE IN AUTO-DETECT MODE")
    print("=" * 80)
    print(f"\nInput verse:\n{verse_text}\n")

    # Test line-by-line mode (auto-detect)
    print("\n" + "=" * 80)
    print("LINE-BY-LINE MODE (Default)")
    print("=" * 80)

    lines = verse_text.strip().split('\n')
    for i, line in enumerate(lines, 1):
        # Remove danda and other punctuation
        clean_line = line.replace('।', '').replace('॥', '').strip()

        print(f"\n--- Line {i} ---")
        print(f"Text: {clean_line}")

        result = chanda.identify_line(clean_line)

        if result.get('found'):
            print("\n✅ METER IDENTIFIED")
            print(f"   Primary Meter: {result.get('display_chanda_primary', 'N/A')}")
            print(f"   Display: {result.get('display_chanda', 'N/A')}")
            print(f"   L-G Pattern: {''.join(result.get('display_lg', []))}")
            print(f"   Gana Pattern: {result.get('display_gana', 'N/A')}")
            print(f"   Syllables: {result.get('display_length', 0)}")
            print(f"   Matras: {result.get('display_matra', 0)}")

            # Show all matches with confidence
            if 'matches' in result:
                print("\n   All Matches:")
                for match in result['matches'][:5]:  # Top 5
                    print(f"     - {match.get('name', 'N/A')} (confidence: {match.get('confidence', 0):.1f})")

            # Show fuzzy matches if any
            if result.get('fuzzy'):
                print("\n   Fuzzy Matches:")
                for fuzzy_match in result['fuzzy'][:3]:  # Top 3
                    print(f"     - {fuzzy_match[0]} (similarity: {fuzzy_match[1]:.2f})")
        else:
            print("\n❌ NO METER IDENTIFIED")
            print(f"   Syllables: {result.get('display_length', 0)}")
            print(f"   L-G Pattern: {''.join(result.get('display_lg', []))}")

    # Test verse mode
    print("\n" + "=" * 80)
    print("VERSE MODE (Holistic Analysis)")
    print("=" * 80)

    verse_result = chanda.identify_verse_holistically(lines)

    if verse_result:
        print("\n✅ VERSE METER IDENTIFIED (Holistic)")
        print(f"   Meter: {verse_result.get('meter', 'N/A')}")
        print(f"   Confidence: {verse_result.get('confidence', 0):.1f}")
        print(f"   Reason: {verse_result.get('reason', 'N/A')}")
    else:
        print("\n❌ NO HOLISTIC METER IDENTIFIED")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    test_vedic_verse()
