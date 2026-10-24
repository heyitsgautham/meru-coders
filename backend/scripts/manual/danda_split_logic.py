#!/usr/bin/env python3
"""
Simple standalone test for danda-separated verse handling
"""

# Simulate the danda splitting logic from chatbot.py
text = "शालिन्युक्ता म्तौ तगौ गोऽब्धिलोकैः। माता रामो मत्पिता रामचन्द्रः स्वामी रामो मत्सखा रामचन्द्रः। सर्वस्वं मे रामचन्द्रो दयालुर् नान्यं‌ जाने नैव जाने न जाने॥"

print("=" * 80)
print("Testing Danda Splitting Logic")
print("=" * 80)
print(f"Original text:\n{text}\n")

# Check if text has multiple lines (split by newlines OR danda separators)
lines = [line.strip() for line in text.split('\n') if line.strip()]

print(f"Step 1 - Split by newlines: {len(lines)} lines")
for i, line in enumerate(lines, 1):
    print(f"  Line {i}: {line[:50]}...")

# If only one line, check for danda separators (।)
if len(lines) == 1 and '।' in text:
    print("\n👉 Only 1 line found, checking for danda separators...")
    # Split by danda and clean up
    lines = [line.strip() for line in text.replace('॥', '।').split('।') if line.strip()]
    print(f"Step 2 - Split by danda: {len(lines)} lines")

print(f"\nFinal result: {len(lines)} lines/padas\n")
for i, line in enumerate(lines, 1):
    print(f"Pada {i}: {line}")

print("\n" + "=" * 80)
print("Expected: 5 padas")
print("Actual: {} padas".format(len(lines)))
if len(lines) == 5:
    print("✅ SUCCESS! Danda splitting is working correctly!")
else:
    print("❌ FAILED! Expected 5 padas but got {}".format(len(lines)))
