#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the improved sloka validation with difflib"""


import requests

# Test with a slightly modified sloka (3 intentional changes)
# Original: माता रामो मत्पिता रामचन्द्रः स्वामी रामो मत्सखा रामचन्द्रः
# Changed: माता रामो मतपिता रामचन्द्र स्वामी रामो मत्सखा रामचन्द्र
#                    ^ missing ्             ^ missing ः                        ^ missing ः

test_text = "माता रामो मतपिता रामचन्द्र स्वामी रामो मत्सखा रामचन्द्र"

print("Testing sloka validation with difflib algorithm...")
print(f"\nInput: {test_text}")
print("-" * 60)

response = requests.post('http://localhost:5000/api/sloka/validate', json={
    'text': test_text
})

print(f"Status: {response.status_code}")
data = response.json()

if data.get('success') and data.get('found'):
    print("\n✓ Found match!")
    print(f"  Similarity: {data.get('similarity_percentage')}%")
    print(f"  Chandas: {data.get('chandas')}")
    print(f"  Source: {data.get('dataset_name')}")
    print(f"  Difference Count: {data.get('difference_count')}")

    print(f"\n📝 Original text:\n  {data.get('original_text')}")

    print("\n🔍 Differences found:")
    for diff in data.get('differences', []):
        print(f"  • {diff['type'].upper()}: {diff['description']}")

    print("\n🎨 Highlighted segments:")
    for seg in data.get('highlighted_segments', []):
        marker = "❌" if seg['isError'] else "✓"
        print(f"  {marker} '{seg['text']}'")
else:
    print(f"Error or not found: {data}")

# Also test with exact match
print("\n" + "=" * 60)
print("Testing with exact match...")

exact_text = "माता रामो मत्पिता रामचन्द्रः स्वामी रामो मत्सखा रामचन्द्रः । सर्वस्वं मे रामचन्द्रो दयालु- र्नान्यं जाने नैव जाने न जाने ॥"

response2 = requests.post('http://localhost:5000/api/sloka/validate', json={
    'text': exact_text
})

data2 = response2.json()
if data2.get('success') and data2.get('found'):
    print(f"✓ Similarity: {data2.get('similarity_percentage')}%")
    print(f"✓ Is Valid: {data2.get('is_valid')}")
    print(f"✓ Differences: {data2.get('difference_count')}")
