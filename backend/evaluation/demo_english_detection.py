#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick manual demonstration of English text detection
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import Settings
from core.chanda import Chanda


def demo():
    """Demonstrate English text detection with real examples"""

    settings = Settings()
    chanda = Chanda(data_path=str(settings.DATA_DIR))

    print("=" * 80)
    print("ENGLISH TEXT DETECTION - LIVE DEMONSTRATION")
    print("=" * 80)

    examples = [
        ("hello world", "❌ Should be REJECTED - Plain English"),
        ("dharma kṣetre kurukṣetre", "✅ Should be ACCEPTED - Valid IAST"),
        ("this is a test", "❌ Should be REJECTED - English sentence"),
        ("धर्मक्षेत्रे कुरुक्षेत्रे", "✅ Should be ACCEPTED - Devanagari"),
        ("the quick brown fox", "❌ Should be REJECTED - English pangram"),
        ("śrī kṛṣṇa govinda", "✅ Should be ACCEPTED - IAST with diacritics"),
    ]

    for text, expected in examples:
        result = chanda.identify_line(text)
        is_valid = result.get('is_valid_input', True)

        print(f"\n{'='*80}")
        print(f"Input: {text}")
        print(f"Expected: {expected}")
        print("-" * 80)

        if is_valid:
            print("✅ ACCEPTED")
            if result.get('found'):
                print(f"   Meter: {result.get('display_chanda_primary', 'N/A')}")
                print(f"   L-G Pattern: {''.join(result.get('display_lg', []))}")
                print(f"   Syllables: {result.get('display_length', 0)}")
        else:
            print("❌ REJECTED")
            print(f"   Reason: {result.get('validation_error', 'Unknown')}")

if __name__ == '__main__':
    demo()
