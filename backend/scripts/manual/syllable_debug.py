#!/usr/bin/env python3
"""
Debug syllable breakdown mismatch
"""

import os
import sys

sys.path.insert(0, '/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend')
os.chdir('/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend')

from core.chanda import Chanda

# Initialize Chanda engine
chanda = Chanda(data_path='/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend/data')

# Test text
text = "शालिन्युक्ता म्तौ तगौ गोऽब्धिलोकैः। माता रामो मत्पिता रामचन्द्रः स्वामी रामो मत्सखा रामचन्द्रः। सर्वस्वं मे रामचन्द्रो दयालुर् नान्यं‌ जाने नैव जाने न जाने॥"

print("Analyzing syllable breakdown...")

test_result = chanda.identify_line(text)
syllables = test_result.get('display_syllables', [])
lg_marks = test_result.get('display_lg', [])

print(f"\nTotal syllables in breakdown: {len(syllables)}")
print(f"Total L-G marks: {len(lg_marks)}")

# Filter out empty/non-syllable items
valid_syllables = [s for s in syllables if s and s.strip() and s not in ['।', '॥', ' ']]
valid_lg = [lg for lg in lg_marks if lg and lg.strip()]

print(f"Valid syllables (non-empty): {len(valid_syllables)}")
print(f"Valid L-G marks (non-empty): {len(valid_lg)}")

print("\nFirst 15 syllables:")
for i in range(min(15, len(syllables))):
    print(f"  {i + 1}: '{syllables[i]}' → LG: '{lg_marks[i] if i < len(lg_marks) else '?'}'")

print("\nLast 10 syllables:")
for i in range(max(0, len(syllables) - 10), len(syllables)):
    print(f"  {i + 1}: '{syllables[i]}' → LG: '{lg_marks[i] if i < len(lg_marks) else '?'}'")
