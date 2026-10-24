#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to analyze युयुत्सवः syllable marking"""

import sys
sys.path.insert(0, '/home/harevasu/Projects/meru-coders/backend')

from core import Chanda
from config import settings

chanda = Chanda(data_path=str(settings.DATA_DIR))

print("=" * 60)
print("Debugging युयुत्सवः syllable marking")
print("=" * 60)

# Test the word युयुत्सवः
text = 'युयुत्सवः'
syllables, lg_marks = chanda.mark_lg(text)
print(f'\nWord: {text}')
print(f'Syllables: {syllables}')
print(f'LG marks: {lg_marks}')

# Flatten and show each syllable
if syllables:
    flat_syls = syllables[0][0] if isinstance(syllables[0][0], list) else syllables[0]
    print("\nDetailed syllable breakdown:")
    for i, syl in enumerate(flat_syls):
        mark = lg_marks[i] if i < len(lg_marks) else '?'
        print(f"  {i+1}. '{syl}' -> {mark}")

print("\n" + "=" * 60)
print("Testing full first line of Bhagavad Gita")
print("=" * 60)

# Test the full line
line1 = 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः'
syllables, lg_marks = chanda.mark_lg(line1)
print(f'\nLine: {line1}')

# Flatten and show each syllable
if syllables:
    flat_syls = syllables[0][0] if isinstance(syllables[0][0], list) else syllables[0]
    print("\nDetailed syllable breakdown:")
    for i, syl in enumerate(flat_syls):
        mark = lg_marks[i] if i < len(lg_marks) else '?'
        print(f"  {i+1}. '{syl}' -> {mark} ({'Laghu' if mark == 'L' else 'Guru'})")

print("\n" + "=" * 60)
print("Expected: यु = L (short vowel उ), यु = L (short vowel उ)")
print("The word युयुत्सवः should have both 'यु' syllables as Laghu")
print("=" * 60)
