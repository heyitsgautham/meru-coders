"""Test dandaka_detector with real examples"""

import json

from backend.core.dandaka_detector import analyze_dandaka_mode

# Test 1: Rajashyamala title
print("=" * 80)
print("TEST 1: Rajashyamala Title")
print("=" * 80)
text1 = "राजश्यामला स्तोत्रम्"
result1 = analyze_dandaka_mode(text1)
print(json.dumps(result1, indent=2, ensure_ascii=False))

# Test 2: Rajashyamala with keywords
print("\n" + "=" * 80)
print("TEST 2: Rajashyamala with Keywords")
print("=" * 80)
text2 = """
श्री राजश्यामला स्तोत्रम्
नमामि मातङ्गी वाग्देवी श्यामला।
विद्यादात्री महाविद्या तन्त्र राज्यम्।
"""
result2 = analyze_dandaka_mode(text2)
print(json.dumps(result2, indent=2, ensure_ascii=False))

# Test 3: Long Dandaka verse (>108 aksaras)
print("\n" + "=" * 80)
print("TEST 3: Long Dandaka (Ati-dandakam)")
print("=" * 80)
text3 = "ध" * 120  # 120 syllables
result3 = analyze_dandaka_mode(text3)
print(json.dumps(result3, indent=2, ensure_ascii=False))

# Test 4: Medium Dandaka (Madhyama)
print("\n" + "=" * 80)
print("TEST 4: Medium Dandaka (Madhyama)")
print("=" * 80)
text4 = "ध" * 40  # 40 syllables
result4 = analyze_dandaka_mode(text4)
print(json.dumps(result4, indent=2, ensure_ascii=False))
