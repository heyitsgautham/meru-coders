#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentic Verses Performance Comparison
=======================================
Compares Our Model vs IITK Model using authentic Sanskrit verses
from traditional texts (Bhagavad Gita, Rigveda, etc.)

Our Model: 2055 meters database
IITK Model: 398 meters database
"""

import os
import time

from backend.core.chanda import Chanda as OurChanda
from reference.alternative_implementations.chanda_iitk import Chanda as IITKChanda

# Authentic test verses with known meters
# Using single pada (quarter) for fair comparison since IITK model works per-pada
AUTHENTIC_VERSES = [
    {
        'name': 'Anushtubh (BG 1.1) - Pada 1',
        'expected': 'अनुष्टुभ्',
        'verse': 'धर्मक्षेत्रे कुरुक्षेत्रे',
        'source': 'Bhagavad Gita 1.1',
    },
    {
        'name': 'Anushtubh (BG 1.1) - Pada 2',
        'expected': 'अनुष्टुभ्',
        'verse': 'समवेता युयुत्सवः',
        'source': 'Bhagavad Gita 1.1',
    },
    {
        'name': 'Anushtubh (BG 2.47) - Pada 1',
        'expected': 'अनुष्टुभ्',
        'verse': 'कर्मण्येवाधिकारस्ते',
        'source': 'Bhagavad Gita 2.47',
    },
    {
        'name': 'Anushtubh (BG 2.47) - Pada 2',
        'expected': 'अनुष्टुभ्',
        'verse': 'मा फलेषु कदाचन',
        'source': 'Bhagavad Gita 2.47',
    },
    {
        'name': 'Anushtubh (BG 4.7) - Pada 1',
        'expected': 'अनुष्टुभ्',
        'verse': 'यदा यदा हि धर्मस्य',
        'source': 'Bhagavad Gita 4.7',
    },
    {
        'name': 'Anushtubh (BG 4.7) - Pada 2',
        'expected': 'अनुष्टुभ्',
        'verse': 'ग्लानिर्भवति भारत',
        'source': 'Bhagavad Gita 4.7',
    },
    {
        'name': 'Gayatri (RV 3.62.10)',
        'expected': 'गायत्री',
        'verse': 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्',
        'source': 'Rigveda 3.62.10',
    },
    {'name': 'Ganesh Prayer - Pada 1', 'expected': 'अनुष्टुभ्', 'verse': 'वक्रतुण्ड महाकाय', 'source': 'Traditional'},
    {'name': 'Ganesh Prayer - Pada 2', 'expected': 'अनुष्टुभ्', 'verse': 'सूर्यकोटिसमप्रभ', 'source': 'Traditional'},
    {'name': 'Guru Stuti - Pada 1', 'expected': 'अनुष्टुभ्', 'verse': 'गुरुर्ब्रह्मा गुरुर्विष्णुः', 'source': 'Traditional'},
    {'name': 'Guru Stuti - Pada 2', 'expected': 'अनुष्टुभ्', 'verse': 'गुरुर्देवो महेश्वरः', 'source': 'Traditional'},
    # Full shloka tests (our model handles these, IITK may not)
    {
        'name': 'Full Shloka (BG 1.1)',
        'expected': 'अनुष्टुभ्',
        'verse': 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय',
        'source': 'Bhagavad Gita 1.1 (Full)',
    },
    {
        'name': 'Full Shloka (BG 4.7-8)',
        'expected': 'अनुष्टुभ्',
        'verse': 'यदा यदा हि धर्मस्य ग्लानिर्भवति भारत अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम्',
        'source': 'Bhagavad Gita 4.7 (Full)',
    },
]


def check_result(expected, result):
    """Check if expected meter is in result"""
    if not result:
        return False, None

    chanda_list = result.get('chanda', [])
    if chanda_list:
        for item in chanda_list:
            if isinstance(item, (list, tuple)) and len(item) > 0:
                name = item[0]
                if expected in name or name in expected:
                    return True, name

    # Check fuzzy matches
    fuzzy_list = result.get('fuzzy', [])
    for fuzzy in fuzzy_list:
        for item in fuzzy.get('chanda', []):
            if isinstance(item, (list, tuple)) and len(item) > 0:
                name = item[0]
                if expected in name or name in expected:
                    return True, name

    # Return first match if any
    first = None
    if chanda_list:
        if isinstance(chanda_list[0], (list, tuple)):
            first = chanda_list[0][0]

    return False, first


def run_authentic_comparison():
    """Run comparison on authentic verses"""
    print("=" * 90)
    print("AUTHENTIC VERSES - MODEL PERFORMANCE COMPARISON")
    print("=" * 90)
    print()

    # Initialize paths
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    our_data_path = os.path.join(base_path, 'data')
    iitk_data_path = os.path.join(base_path, '..', 'repos', 'chanda', 'data')

    # Initialize models
    print("Initializing models...")
    our_model = OurChanda(our_data_path)
    iitk_model = IITKChanda(iitk_data_path)
    print("  ✓ Both models initialized")
    print()

    print(f"Testing {len(AUTHENTIC_VERSES)} authentic Sanskrit verses...")
    print()
    print("-" * 90)
    print(f"{'#':3} {'Test Case':30} {'Expected':15} {'Our Model':15} {'IITK Model':15} {'Our':5} {'IITK':5}")
    print("-" * 90)

    our_correct = 0
    iitk_correct = 0
    our_times = []
    iitk_times = []

    for i, test in enumerate(AUTHENTIC_VERSES, 1):
        expected = test['expected']
        verse = test['verse']
        name = test['name'][:28]

        # Test our model
        start = time.time()
        our_result = our_model.identify_line(verse, fuzzy=True)
        our_time = time.time() - start
        our_times.append(our_time)
        our_match, our_got = check_result(expected, our_result)

        # Test IITK model
        start = time.time()
        iitk_result = iitk_model.identify_line(verse, fuzzy=True)
        iitk_time = time.time() - start
        iitk_times.append(iitk_time)
        iitk_match, iitk_got = check_result(expected, iitk_result)

        if our_match:
            our_correct += 1
        if iitk_match:
            iitk_correct += 1

        our_status = "✅" if our_match else "❌"
        iitk_status = "✅" if iitk_match else "❌"
        our_display = (our_got or "None")[:13]
        iitk_display = (iitk_got or "None")[:13]

        print(f"{i:3} {name:30} {expected[:13]:15} {our_display:15} {iitk_display:15} {our_status:5} {iitk_status:5}")

    # Summary
    print()
    print("=" * 90)
    print("RESULTS SUMMARY")
    print("=" * 90)
    print()

    total = len(AUTHENTIC_VERSES)
    our_accuracy = our_correct / total * 100
    iitk_accuracy = iitk_correct / total * 100
    our_avg_time = sum(our_times) / len(our_times) * 1000
    iitk_avg_time = sum(iitk_times) / len(iitk_times) * 1000

    print(f"{'Metric':<35} {'Our Model':>20} {'IITK Model':>20}")
    print("-" * 75)
    print(f"{'Database Size':<35} {'2,055 meters':>20} {'398 meters':>20}")
    print(f"{'Total Test Cases':<35} {total:>20} {total:>20}")
    print(f"{'Correct Identifications':<35} {our_correct:>20} {iitk_correct:>20}")
    print(f"{'Accuracy':<35} {our_accuracy:>19.1f}% {iitk_accuracy:>19.1f}%")
    print(f"{'Average Time (ms)':<35} {our_avg_time:>19.2f} {iitk_avg_time:>19.2f}")
    print()

    # Comparison
    print("COMPARISON:")
    print("-" * 40)

    diff = our_accuracy - iitk_accuracy
    if diff > 0:
        print(f"  🏆 Our model is {diff:.1f}% more accurate")
    elif diff < 0:
        print(f"  📉 IITK model is {-diff:.1f}% more accurate")
    else:
        print("  🤝 Both models have same accuracy")

    speed_ratio = iitk_avg_time / max(0.001, our_avg_time)
    if speed_ratio > 1:
        print(f"  ⚡ Our model is {speed_ratio:.1f}x faster")
    elif speed_ratio < 1:
        print(f"  🐢 IITK model is {1 / speed_ratio:.1f}x faster")
    else:
        print("  🤝 Both models have same speed")

    print(f"  📊 Our database is {2055 / 398:.1f}x larger")
    print()

    print("=" * 90)
    print(f"FINAL RESULT: Our Model {our_accuracy:.1f}% vs IITK Model {iitk_accuracy:.1f}%")
    print("=" * 90)

    return our_accuracy, iitk_accuracy


if __name__ == '__main__':
    run_authentic_comparison()
