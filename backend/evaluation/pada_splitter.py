#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Pada Splitter

Run with: python -m pytest backend/evaluation/pada_splitter.py -v
Or directly: python backend/evaluation/pada_splitter.py
"""

import sys

from backend.utils.pada_splitter import PadaSplitter


def test_syllable_counting():
    """Test syllable counting for various inputs"""
    splitter = PadaSplitter()

    test_cases = [
        # (text, expected_syllables, description)
        ("धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः", 16, "First line of Gita 1.1"),
        ("अ", 1, "Single vowel"),
        ("क", 1, "Single consonant with inherent a"),
        ("का", 1, "Consonant + ā mātrā"),
        ("कर्म", 2, "karma = kar + ma"),
        ("योग", 2, "yoga = yo + ga"),
        ("धर्म", 2, "dharma = dhar + ma"),
        ("ॐ", 1, "Om"),
        ("नमः", 2, "namaḥ = na + maḥ"),
        ("कृष्ण", 2, "kṛṣṇa = kṛṣ + ṇa"),
        ("स्वामी", 2, "svāmī = svā + mī"),
    ]

    print("\n" + "=" * 70)
    print("TEST: Syllable Counting")
    print("=" * 70)

    passed = 0
    failed = 0

    for text, expected, description in test_cases:
        actual = splitter.count_syllables(text)
        status = "✓" if actual == expected else "✗"

        if actual == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} {description}: '{text}' -> {actual} (expected {expected})")

    print(f"\nResult: {passed}/{passed + failed} passed")
    return failed == 0


def test_anushtubh_splitting():
    """Test Anushtubh (8-8-8-8) meter splitting"""
    splitter = PadaSplitter()

    test_verses = [
        "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः मामकाः पाण्डवाश्चैव किमकुर्वत संजय",
        "वसुदेवसुतं देवं कंसचाणूरमर्दनम् देवकीपरमानन्दं कृष्णं वन्दे जगद्गुरुम्",
        "कृष्णाय वासुदेवाय देवकीनन्दनाय च नन्दगोपकुमाराय गोविन्दाय नमो नमः",
    ]

    print("\n" + "=" * 70)
    print("TEST: Anushtubh (8-8-8-8) Splitting")
    print("=" * 70)

    passed = 0
    failed = 0

    for verse in test_verses:
        result = splitter.split_verse(verse, meter='anushtubh')

        # Check success and pada count
        pada_success = result.success and len(result.padas) == 4
        syllable_success = all(pada.syllable_count == 8 for pada in result.padas) if result.success else False

        if pada_success and syllable_success:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"

        print(f"\n{status} Verse: {verse[:50]}...")
        print(f"   Total syllables: {result.total_syllables}")
        print(f"   Success: {result.success}")

        if result.success:
            for pada in result.padas:
                syl_status = "✓" if pada.syllable_count == 8 else "✗"
                print(f"   {syl_status} {pada}")
        else:
            print(f"   Message: {result.message}")

    print(f"\nResult: {passed}/{passed + failed} passed")
    return failed == 0


def test_trishtubh_splitting():
    """Test Trishtubh (11-11-11-11) meter splitting"""
    splitter = PadaSplitter()

    test_verses = [
        "त्वमेव माता च पिता त्वमेव त्वमेव बन्धुश्च सखा त्वमेव त्वमेव विद्या द्रविणं त्वमेव त्वमेव सर्वं मम देव देव",
    ]

    print("\n" + "=" * 70)
    print("TEST: Trishtubh (11-11-11-11) Splitting")
    print("=" * 70)

    passed = 0
    failed = 0

    for verse in test_verses:
        result = splitter.split_verse(verse, meter='trishtubh')

        # Check success and pada count
        pada_success = result.success and len(result.padas) == 4
        syllable_success = all(pada.syllable_count == 11 for pada in result.padas) if result.success else False

        if pada_success and syllable_success:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"

        print(f"\n{status} Verse: {verse[:50]}...")
        print(f"   Total syllables: {result.total_syllables}")
        print(f"   Success: {result.success}")

        if result.success:
            for pada in result.padas:
                syl_status = "✓" if pada.syllable_count == 11 else "✗"
                print(f"   {syl_status} {pada}")
        else:
            print(f"   Message: {result.message}")

    print(f"\nResult: {passed}/{passed + failed} passed")
    return failed == 0


def test_auto_detection():
    """Test automatic meter detection"""
    splitter = PadaSplitter()

    test_cases = [
        # (verse, expected_meter)
        ("धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः मामकाः पाण्डवाश्चैव किमकुर्वत संजय", "anushtubh"),
        ("वसुदेवसुतं देवं कंसचाणूरमर्दनम् देवकीपरमानन्दं कृष्णं वन्दे जगद्गुरुम्", "anushtubh"),
    ]

    print("\n" + "=" * 70)
    print("TEST: Automatic Meter Detection")
    print("=" * 70)

    passed = 0
    failed = 0

    for verse, expected_meter in test_cases:
        result = splitter.auto_split(verse)

        if result.success and result.meter == expected_meter:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"

        print(f"\n{status} Verse: {verse[:50]}...")
        print(f"   Detected: {result.meter} (expected: {expected_meter})")
        print(f"   Success: {result.success}")

    print(f"\nResult: {passed}/{passed + failed} passed")
    return failed == 0


def test_iast_input():
    """Test IAST transliteration input"""
    splitter = PadaSplitter()

    test_cases = [
        ("dharmakṣetre kurukṣetre samavetā yuyutsavaḥ māmakāḥ pāṇḍavāścaiva kimakurvata saṃjaya", "anushtubh", 32),
    ]

    print("\n" + "=" * 70)
    print("TEST: IAST Transliteration Input")
    print("=" * 70)

    passed = 0
    failed = 0

    for iast_verse, meter, expected_syllables in test_cases:
        result = splitter.split_verse(iast_verse, meter=meter)

        syllables_match = abs(result.total_syllables - expected_syllables) <= 2

        if result.success and syllables_match:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"

        print(f"\n{status} IAST: {iast_verse[:50]}...")
        print(f"   Syllables: {result.total_syllables} (expected ~{expected_syllables})")
        print(f"   Success: {result.success}")

        if result.success:
            for pada in result.padas:
                print(f"   Pada {pada.position}: {pada.text}")

    print(f"\nResult: {passed}/{passed + failed} passed")
    return failed == 0


def test_custom_patterns():
    """Test custom syllable patterns"""
    splitter = PadaSplitter()

    print("\n" + "=" * 70)
    print("TEST: Custom Patterns")
    print("=" * 70)

    # Test half-verse (8-8)
    half_verse = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"
    result = splitter.split_verse(half_verse, pattern=[8, 8])

    success = result.success and len(result.padas) == 2
    status = "✓" if success else "✗"

    print(f"\n{status} Half-verse with pattern [8, 8]")
    print(f"   Verse: {half_verse}")
    print(f"   Success: {result.success}")

    if result.success:
        for pada in result.padas:
            print(f"   {pada}")

    return success


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "=" * 70)
    print("PADA SPLITTER TEST SUITE")
    print("=" * 70)

    results = []

    results.append(("Syllable Counting", test_syllable_counting()))
    results.append(("Anushtubh Splitting", test_anushtubh_splitting()))
    results.append(("Trishtubh Splitting", test_trishtubh_splitting()))
    results.append(("Auto Detection", test_auto_detection()))
    results.append(("IAST Input", test_iast_input()))
    results.append(("Custom Patterns", test_custom_patterns()))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nOverall: {passed}/{total} test groups passed")

    return all(r for _, r in results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
