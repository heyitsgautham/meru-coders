#!/usr/bin/env python3
"""
Test smart pada splitting based on syllable count
"""

import os
import sys

sys.path.insert(0, '/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend')
os.chdir('/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend')

from core.chanda import Chanda

# Initialize Chanda engine
chanda = Chanda(data_path='/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend/data')

# Test text (55 syllables = 5 padas of 11 each)
text = "शालिन्युक्ता म्तौ तगौ गोऽब्धिलोकैः। माता रामो मत्पिता रामचन्द्रः स्वामी रामो मत्सखा रामचन्द्रः। सर्वस्वं मे रामचन्द्रो दयालुर् नान्यं‌ जाने नैव जाने न जाने॥"

print("=" * 80)
print("Testing Smart Pada Splitting (syllable-based)")
print("=" * 80)

# Analyze the whole line
test_result = chanda.identify_line(text)
lg_pattern = ''.join([char for char in test_result.get('display_lg', []) if char])
total_syllables = len(lg_pattern)

print(f"Total syllables: {total_syllables}")
print(f"L-G Pattern: {lg_pattern}\n")

# Common pada lengths
common_pada_lengths = [8, 11, 12, 14, 17, 19, 21]

lines = []
for pada_length in common_pada_lengths:
    if total_syllables % pada_length == 0:
        num_padas = total_syllables // pada_length
        print(f"✓ Divisible by {pada_length} → {num_padas} padas\n")

        # Get syllable breakdown
        syllables = test_result.get('display_syllables', [])
        lg_marks = test_result.get('display_lg', [])

        # Filter to only include items with valid L-G marks (actual syllables)
        valid_syllables = []
        for i, (syl, lg) in enumerate(zip(syllables, lg_marks)):
            if lg and lg.strip():  # Only include if has L-G mark
                valid_syllables.append(syl)

        print(f"Valid syllables (with L-G marks): {len(valid_syllables)}")

        if len(valid_syllables) == total_syllables:
            # Split based on syllable positions
            lines = []
            for pada_idx in range(num_padas):
                start = pada_idx * pada_length
                end = start + pada_length
                pada_syllables = valid_syllables[start:end]
                pada_text = ''.join(pada_syllables)
                lines.append(pada_text)
                print(f"  Pada {pada_idx + 1}: {pada_text} ({len(pada_syllables)} syllables)")

            if len(lines) == num_padas:
                print(f"\n✅ Successfully split into {num_padas} padas of {pada_length} syllables each!")
                break
        else:
            print(f"  ❌ Syllable count mismatch: {len(valid_syllables)} != {total_syllables}")
    else:
        print(f"✗ Not divisible by {pada_length}")

if not lines:
    print("\n❌ Could not split into padas")
else:
    print("\n" + "=" * 80)
    print(f"Final Result: {len(lines)} padas")
    print("=" * 80)
    for i, line in enumerate(lines, 1):
        print(f"Pada {i}: {line}")
