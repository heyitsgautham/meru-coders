#!/usr/bin/env python3
"""
Test script to verify pada splitting in chatbot responses
"""

import os
import sys

sys.path.insert(0, '/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend')
os.chdir('/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend')

from core.chanda import Chanda

# Initialize Chanda engine
chanda = Chanda(data_path='/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend/data')

# Test with a Bhagavad Gita verse (Anushtubh meter - 32 syllables = 4 padas of 8 each)
test_verse = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"

print("=" * 80)
print("Testing Pada Display for Single-Line Verse")
print("=" * 80)
print(f"\nInput: {test_verse}\n")

# Identify the meter
result = chanda.identify_line(test_verse)

# Get the full L-G pattern
lg_pattern = ''.join([char for char in result.get('display_lg', []) if char])

# Split into padas
lg_padas = []
total_syllables = len(lg_pattern)
if total_syllables > 0:
    if total_syllables % 4 == 0:
        pada_length = total_syllables // 4
        for i in range(4):
            start = i * pada_length
            end = start + pada_length
            lg_padas.append(lg_pattern[start:end])
    elif total_syllables % 2 == 0:
        pada_length = total_syllables // 2
        lg_padas.append(lg_pattern[:pada_length])
        lg_padas.append(lg_pattern[pada_length:])
    else:
        lg_padas.append(lg_pattern)

print("Identification Result:")
print(f"  Meter: {result.get('display_chanda_primary', 'Unknown')}")
print(f"  Total Syllables: {result.get('display_length', 0)}")
print(f"  L-G Pattern (full): {lg_pattern}")
print("\n  L-G Pattern by Pada:")
for i, pada in enumerate(lg_padas, 1):
    print(f"    Pada {i}: {pada} ({len(pada)} syllables)")

# Test formatting function
print("\n" + "=" * 80)
print("Formatted Display (as shown to user):")
print("=" * 80)
print("\n**L-G Pattern (by Pada):**")
for i, pada in enumerate(lg_padas, 1):
    print(f"- **Pada {i}:** {pada}")

# Test with a 64-syllable pattern
print("\n" + "=" * 80)
print("Testing with a 64-syllable pattern")
print("=" * 80)
long_pattern = "गगलगगललगलगगगगलगगललगलगगगगलगगललगलगगगगलггللगलगगगगلггललगलगг" * 2
long_pattern = long_pattern[:64]  # Ensure exactly 64
print(f"Input L-G pattern length: {len(long_pattern)} syllables\n")

lg_padas_long = []
if len(long_pattern) % 4 == 0:
    pada_length = len(long_pattern) // 4
    for i in range(4):
        start = i * pada_length
        end = start + pada_length
        lg_padas_long.append(long_pattern[start:end])

print("**L-G Pattern (by Pada):**")
for i, pada in enumerate(lg_padas_long, 1):
    print(f"- **Pada {i}:** {pada} ({len(pada)} syllables)")

print("\n✅ Test complete!")
