#!/usr/bin/env python3
"""
Test script to verify danda-separated verse handling in chatbot
"""

import os
import sys
sys.path.insert(0, '/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend')
os.chdir('/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend')

from api.chatbot import analyze_meter_agentic, format_meter_response

# Test with the problematic verse (as user typed it - single line with danda separators)
test_verse = "शालिन्युक्ता म्तौ तगौ गोऽब्धिलोकैः। माता रामो मत्पिता रामचन्द्रः स्वामी रामो मत्सखा रामचन्द्रः। सर्वस्वं मे रामचन्द्रो दयालुर् नान्यं‌ जाने नैव जाने न जाने॥"

print("=" * 80)
print("Testing Danda-Separated Verse (User's Input)")
print("=" * 80)
print(f"Input: {test_verse[:80]}...\n")

# Analyze the meter
meter_data = analyze_meter_agentic(test_verse)

print("Meter Analysis Result:")
print(f"  Success: {meter_data.get('success')}")
print(f"  Meter: {meter_data.get('meter')}")
print(f"  Is Multi-line: {meter_data.get('is_multi_line')}")
print(f"  Number of lines: {meter_data.get('verse_lines')}")
print(f"  Total Syllables: {meter_data.get('syllables')}")
print()

# Check lg_pattern_padas
lg_padas = meter_data.get('lg_pattern_padas', [])
print(f"L-G Pattern Padas (count: {len(lg_padas)}):")
for idx, pada in enumerate(lg_padas, 1):
    print(f"  Pada {idx}: {pada} ({len(pada)} syllables)")
print()

# Format the response as shown to user
print("=" * 80)
print("Formatted Response (as shown to user):")
print("=" * 80)
response = format_meter_response(meter_data, persona='default')
print(response)

print("\n" + "=" * 80)
print("EXPECTED OUTPUT:")
print("=" * 80)
print("Should show 5 separate padas (one for each line between dandas):")
print("- Pada 1: शालिन्युक्ता म्तौ तगौ गोऽब्धिलोकैः")
print("- Pada 2: माता रामो मत्पिता रामचन्द्रः")
print("- Pada 3: स्वामी रामो मत्सखा रामचन्द्रः")
print("- Pada 4: सर्वस्वं मे रामचन्द्रो दयालुर्")
print("- Pada 5: नान्यं‌ जाने नैव जाने न जाने")
print("\n✅ If this matches, the fix is working!")
