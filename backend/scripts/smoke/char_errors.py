#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the improved sloka validation with actual character errors"""

import requests

# Test 1: Wrong characters (not missing)
# Original: माता रामो मत्पिता रामचन्द्रः
# Changed:  माता रामो मटपिता रामचन्दरः  (त्→ट, न्द्र→न्दर)

print("=" * 70)
print("TEST 1: Wrong characters (replacements)")
print("=" * 70)

test1 = "माता रामो मटपिता रामचन्दरः"
print(f"Input: {test1}")

response = requests.post('http://localhost:5000/api/sloka/validate', json={'text': test1})
data = response.json()

if data.get('success') and data.get('found'):
    print(f"Similarity: {data.get('similarity_percentage')}%")
    print(f"Differences: {data.get('difference_count')}")
    for diff in data.get('differences', []):
        print(f"  • {diff['type']}: {diff['description']}")
    print("\nHighlighted segments:")
    for seg in data.get('highlighted_segments', []):
        marker = "❌" if seg['isError'] else "✓"
        text_preview = seg['text'][:50] + "..." if len(seg['text']) > 50 else seg['text']
        print(f"  {marker} '{text_preview}'")


# Test 2: Exact first line
print("\n" + "=" * 70)
print("TEST 2: Exact first line")
print("=" * 70)

test2 = "माता रामो मत्पिता रामचन्द्रः"
print(f"Input: {test2}")

response = requests.post('http://localhost:5000/api/sloka/validate', json={'text': test2})
data = response.json()

if data.get('success') and data.get('found'):
    print(f"Similarity: {data.get('similarity_percentage')}%")
    print(f"Is Valid: {data.get('is_valid')}")
    print(f"Differences: {data.get('difference_count')}")


# Test 3: Rigveda first verse with 1 error
print("\n" + "=" * 70)
print("TEST 3: Rigveda verse with 1 wrong character")
print("=" * 70)

# Original: अग्निमीळे
# Changed:  अग्निमीले  (ळ→ल)
test3 = "अग्निमीले पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं"
print(f"Input: {test3}")

response = requests.post('http://localhost:5000/api/sloka/validate', json={'text': test3})
data = response.json()

if data.get('success') and data.get('found'):
    print(f"Similarity: {data.get('similarity_percentage')}%")
    print(f"Differences: {data.get('difference_count')}")
    for diff in data.get('differences', []):
        print(f"  • {diff['type']}: '{diff.get('your_text', '')}' → '{diff.get('correct_text', '')}'")
    print("\nHighlighted segments:")
    for seg in data.get('highlighted_segments', []):
        marker = "❌" if seg['isError'] else "✓"
        print(f"  {marker} '{seg['text']}'")
