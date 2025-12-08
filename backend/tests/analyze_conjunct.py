#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze the conjunct consonant त्स"""

text = 'त्स'
print('Characters in त्स:')
for i, c in enumerate(text):
    print(f'  {i}: {c} (U+{ord(c):04X})')
print()
print('त्स is त + ् + स (ta + virama + sa)')
print('This is a conjunct consonant')
print()

# Check the word युयुत्सवः
word = 'युयुत्सवः'
print(f'Word: {word}')
print('Characters:')
for i, c in enumerate(word):
    print(f'  {i}: {c} (U+{ord(c):04X})')
