#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test with full sloka containing errors"""

import requests

# Full sloka with 2 errors:
# 1. मटपिता instead of मत्पिता (missing ्)
# 2. रामचन्दरः instead of रामचन्द्रः (missing ्)
test = """माता रामो मटपिता रामचन्दरः
स्वामी रामो मत्सखा रामचन्द्रः ।
सर्वस्वं मे रामचन्द्रो दयालु-
र्नान्यं जाने नैव जाने न जाने ॥"""

print("Input sloka with 2 intentional errors:")
print(test)
print("-" * 60)

response = requests.post('http://localhost:5000/api/sloka/validate', json={'text': test})
data = response.json()

print(f"Success: {data.get('success')}")
print(f"Found: {data.get('found')}")
print(f"Similarity: {data.get('similarity_percentage')}%")
print(f"Is Valid: {data.get('is_valid')}")
print(f"Difference Count: {data.get('difference_count')}")

print("\nDifferences:")
for diff in data.get('differences', []):
    dtype = diff.get('type')
    your_text = diff.get('your_text', '')
    correct_text = diff.get('correct_text', '')
    print(f"  • {dtype}: '{your_text}' → '{correct_text}'")

print("\nHighlighted segments:")
for seg in data.get('highlighted_segments', []):
    marker = "❌" if seg['isError'] else "✓"
    text = seg['text'].replace('\n', '\\n')
    if len(text) > 60:
        text = text[:60] + "..."
    print(f"  {marker} '{text}'")
