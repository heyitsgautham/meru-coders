#!/usr/bin/env python3
"""
Analyze the verse to understand its pada structure
"""

import os
import sys
sys.path.insert(0, '/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend')
os.chdir('/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend')

from core.chanda import Chanda

# Initialize Chanda engine
chanda = Chanda(data_path='/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend/data')

# The 5 lines as shown in home page
pada_lines = [
    "शालिन्युक्ता म्तौ तगौ गोऽब्धिलोकैः",
    "माता रामो मत्पिता रामचन्द्रः",
    "स्वामी रामो मत्सखा रामचन्द्रः",
    "सर्वस्वं मे रामचन्द्रो दयालुर्",
    "नान्यं‌ जाने नैव जाने न जाने"
]

print("=" * 80)
print("Analyzing Each Pada from Home Page Output")
print("=" * 80)

all_lg_patterns = []

for i, pada in enumerate(pada_lines, 1):
    result = chanda.identify_line(pada)
    lg = ''.join([char for char in result.get('display_lg', []) if char])
    syllables = len(lg)
    meter = result.get('display_chanda_primary', 'Unknown')
    
    print(f"\nPada {i}: {pada}")
    print(f"  L-G Pattern: {lg}")
    print(f"  Syllables: {syllables}")
    print(f"  Meter: {meter}")
    
    all_lg_patterns.append(lg)

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print(f"Total Padas: {len(pada_lines)}")
print(f"Syllables per pada: {[len(lg) for lg in all_lg_patterns]}")
print(f"All patterns identical: {all(lg == all_lg_patterns[0] for lg in all_lg_patterns)}")

if all_lg_patterns:
    print(f"\nPattern: {all_lg_patterns[0]} (repeats {len(all_lg_patterns)} times)")
    print(f"This is शालिनी (Śālinī) meter - 11 syllables per pada")
