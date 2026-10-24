#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Authentic Sanskrit Verses
Tests the meter identification accuracy on well-known authentic verses
"""

from backend.core.chanda import Chanda

# Initialize Chanda
# Use 'data' directory at the project root, not in tests folder
c = Chanda('data')

def test_verse(test_num, verse, expected_meter, description):
    """Test a single verse and report results"""
    print(f"\n{'='*70}")
    print(f"TEST {test_num}: {description}")
    print(f"{'='*70}")
    print(f"Verse:\n{verse}")
    print(f"\nExpected: {expected_meter}")

    # Process the verse - returns (lines, scheme)
    lines, scheme = c.process_text(verse)

    if lines:
        print(f"\nLines found: {len(lines)}")
        all_passed = True

        for i, line in enumerate(lines, 1):
            print(f"\nLine {i}: {line}")

            # Identify the meter for this line
            result = c.identify_line(line, fuzzy=False)

            if result:
                syllables = result.get('syllables', [])
                lg = result.get('lg', [])
                gana = result.get('gana', '')
                length = result.get('length', 0)
                matra = result.get('matra', 0)
                chanda = result.get('chanda', [])
                found = result.get('found', False)

                print(f"  Syllables: {len(syllables)} - {' '.join(syllables)}")
                print(f"  Pattern (L-G): {' '.join(lg)}")
                print(f"  Gana: {gana}")
                print(f"  Length: {length}, Matra: {matra}")

                if chanda:
                    print(f"  Matches found: {len(chanda)}")
                    for j, (meter_name, pada) in enumerate(chanda[:5], 1):
                        print(f"    {j}. {meter_name} (pada: {pada})")

                    # Check if expected meter is in matches (flexible matching)
                    # Use c.matches_meter() for synonym-aware matching
                    meter_found = any(
                        c.matches_meter(expected_meter, name) or
                        expected_meter.lower() in name.lower() or
                        name.lower() in expected_meter.lower()
                        for name, _ in chanda
                    )
                    if meter_found:
                        print(f"  ✓ Line PASS: Found '{expected_meter}'")
                    else:
                        print(f"  ✗ Line FAIL: '{expected_meter}' NOT found")
                        all_passed = False
                else:
                    print("  ✗ Line FAIL: No matches found")
                    all_passed = False
            else:
                print("  ✗ Line FAIL: Could not identify meter")
                all_passed = False

        return all_passed
    else:
        print("  ✗ FAIL: Could not process verse")
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("AUTHENTICATING AND TESTING SANSKRIT VERSES")
    print("="*70)

    tests = []

    # TEST 1: Bhagavad Gita 2.47 (Anushtubh)
    verse1 = """कर्मण्येवाधिकारस्ते
मा फलेषु कदाचन"""
    tests.append(test_verse(1, verse1, "अनुष्टुभ्",
                           "भगवद्गीता 2.47 (Anuṣṭubh)"))

    # TEST 2: Bhagavad Gita 4.7 (Anushtubh)
    verse2 = """यदा यदा हि धर्मस्य
ग्लानिर्भवति भारत"""
    tests.append(test_verse(2, verse2, "अनुष्टुभ्",
                           "भगवद्गीता 4.7 (Anuṣṭubh)"))

    # TEST 3: Ramaraksha Stotra (Upajati)
    verse3 = """श्रीराम राम रघुनन्दन राम राम
श्रीराम राम भरताग्रज राम राम"""
    tests.append(test_verse(3, verse3, "उपजाति",
                           "रामरक्षास्तोत्रम् (Upajāti)"))

    # TEST 4: Shardulavikridita
    verse4 = """क्वणन्नूपुरमञ्जुभाषितरसं हारं पयोधेरिव
नत्वा भक्तिसुधारसं निजगणैः सेव्योऽस्मि सस्त्रैः शिवः"""
    tests.append(test_verse(4, verse4, "शार्दूलविक्रीडितम्",
                           "प्रसिद्ध श्लोक (Shardūlavikrīḍitam)"))

    # TEST 5: Gayatri Mantra (each line separately)
    verse5a = "ॐ भूर्भुवः स्वः"
    tests.append(test_verse("5a", verse5a, "गायत्री",
                           "गायत्री छन्दस् - Line 1 (8 syllables)"))

    verse5b = "तत्सवितुर्वरेण्यं"
    tests.append(test_verse("5b", verse5b, "गायत्री",
                           "गायत्री छन्दस् - Line 2 (8 syllables)"))

    verse5c = "भर्गो देवस्य धीमहि"
    tests.append(test_verse("5c", verse5c, "गायत्री",
                           "गायत्री छन्दस् - Line 3 (8 syllables)"))

    # TEST 6: Trishtubh (Vedic)
    verse6a = "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम्"
    tests.append(test_verse("6a", verse6a, "त्रिष्टुप्",
                           "त्रिष्टुप् (11-syllable Vedic metre)"))

    verse6b = "अभिव्याहरतप्राणाः समिद्धा होतृमन्त्रिणः"
    tests.append(test_verse("6b", verse6b, "त्रिष्टुप्",
                           "त्रिष्टुप् (11-syllable Vedic metre)"))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(tests)
    total = len(tests)
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"Failed: {total-passed}/{total}")

    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ {total-passed} TEST(S) FAILED")

    return passed, total

if __name__ == "__main__":
    passed, total = main()
