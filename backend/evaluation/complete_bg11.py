#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete analysis of Bhagavad Gita 1.1"""

import sys

sys.path.insert(0, '/home/harevasu/Projects/meru-coders/backend')

from config import settings
from core import Chanda

chanda = Chanda(data_path=str(settings.DATA_DIR))

verse = """धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः
मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय"""

print("=" * 70)
print("Bhagavad Gita 1.1 - Complete Prosody Analysis")
print("=" * 70)
print()
print(verse)
print()

for i, line in enumerate(verse.strip().split('\n')):
    print(f"Line {i + 1}: {line}")
    syllables, lg_marks = chanda.mark_lg(line)

    # Flatten syllables
    flat_syls = syllables[0][0] if isinstance(syllables[0][0], list) else syllables[0]

    print(f"  Syllables: {' '.join(flat_syls)}")
    print(f"  L-G Pattern: {' '.join(lg_marks)}")
    print(f"  Combined: {''.join(lg_marks)}")

    # Show syllable-by-syllable
    print("  Breakdown:")
    for j, (syl, lg) in enumerate(zip(flat_syls, lg_marks)):
        print(f"    {j + 1:2}. {syl:6} → {lg}")
    print()

print("=" * 70)
print("Prosody Rules Applied:")
print("=" * 70)
print("""
1. Long vowels (आ, ई, ऊ, ए, ऐ, ओ, औ) → Guru
2. Anusvara (ं) or Visarga (ः) → Guru  
3. Short vowel + conjunct consonant following → Guru by position

For युयुत्सवः:
  - यु₁: short उ, followed by single य → Laghu ✓
  - यु₂: short उ, followed by conjunct त्स → Guru by position ✓
  - त्स: inherent अ, followed by single व → Laghu ✓
  - वः: has visarga ः → Guru ✓
  
Pattern: L G L G (CORRECT!)
""")
