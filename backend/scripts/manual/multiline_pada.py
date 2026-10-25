#!/usr/bin/env python3
"""
Test script to verify multi-line pada display in chatbot
"""

from backend.config import settings
from backend.core.chanda import Chanda

# Initialize Chanda engine
chanda = Chanda(data_path=str(settings.DATA_DIR))

# Test with the problematic verse (as user typed it - single line with danda separators)
test_verse_single_line = "शालिन्युक्ता म्तौ तगौ गोऽब्धिलोकैः। माता रामो मत्पिता रामचन्द्रः स्वामी रामो मत्सखा रामचन्द्रः। सर्वस्वं मे रामचन्द्रो दयालुर् नान्यं‌ जाने नैव जाने न जाने॥"

# Test with the same verse split into multiple lines
test_verse_multi_line = """शालिन्युक्ता म्तौ तगौ गोऽब्धिलोकैः।
माता रामो मत्पिता रामचन्द्रः
स्वामी रामो मत्सखा रामचन्द्रः।
सर्वस्वं मे रामचन्द्रो दयालुर्
नान्यं‌ जाने नैव जाने न जाने॥"""

print("=" * 80)
print("TEST 1: Single Line Input (with danda separators)")
print("=" * 80)
print(f"Input: {test_verse_single_line[:80]}...\n")

# Test as single line
result1 = chanda.identify_line(test_verse_single_line)
lg1 = ''.join([char for char in result1.get('display_lg', []) if char])
print(f"Meter: {result1.get('display_chanda_primary', 'Unknown')}")
print(f"Total Syllables: {len(lg1)}")
print(f"L-G Pattern: {lg1}\n")

print("=" * 80)
print("TEST 2: Multi-Line Input (properly split)")
print("=" * 80)
print(f"Input:\n{test_verse_multi_line}\n")

# Test as multi-line
lines = [line.strip() for line in test_verse_multi_line.split('\n') if line.strip()]
print(f"Number of lines: {len(lines)}\n")

response = chanda.identify_from_text(test_verse_multi_line, text_mode='verse')
result2 = response.get('result', {})

# Check if we have line-by-line results
if 'line' in result2:
    print(f"Line-by-line analysis found: {len(result2['line'])} lines\n")
    for idx, line_result in enumerate(result2['line'], 1):
        line_data = line_result.get('result', {})
        line_lg = ''.join([char for char in line_data.get('display_lg', []) if char])
        print(f"Line {idx}:")
        print(f"  Text: {line_result.get('line', '')[:50]}...")
        print(f"  L-G Pattern: {line_lg}")
        print(f"  Meter: {line_data.get('display_chanda_primary', 'Unknown')}")
        print()
else:
    print("No line-by-line analysis found!")

print("=" * 80)
print("EXPECTED OUTPUT:")
print("=" * 80)
print("The chatbot should show 5 separate padas (one for each line):")
print("- Pada 1: (line 1 L-G pattern)")
print("- Pada 2: (line 2 L-G pattern)")
print("- Pada 3: (line 3 L-G pattern)")
print("- Pada 4: (line 4 L-G pattern)")
print("- Pada 5: (line 5 L-G pattern)")
