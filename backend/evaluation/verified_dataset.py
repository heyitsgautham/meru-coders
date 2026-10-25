#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verified Dataset Performance Test
=================================
Tests both Our Model and IITK Model on the verified dataset.

Our Model: Uses large dataset (~2055 meters)
IITK Model: Uses small dataset (~398 meters)
"""

import csv
import os
import time

from backend.core.chanda import Chanda as OurChanda
from reference.alternative_implementations.chanda_iitk import Chanda as IITKChanda

# Mapping of English names to Devanagari/Sanskrit equivalents
METER_NAME_MAPPING = {
    'anushthubh': ['अनुष्टुभ्', 'anushtubh', 'anuṣṭubh', 'anustubh'],
    'gayatri': ['गायत्री', 'gayatri', 'gāyatrī'],
    'trishtubh': ['त्रिष्टुभ्', 'trishtubh', 'triṣṭubh', 'tristubh'],
    'jagati': ['जगती', 'jagati', 'jagatī'],
    'ushnik': ['उष्णिक्', 'ushnik', 'uṣṇik'],
    'pankti': ['पङ्क्ति', 'pankti', 'paṅkti'],
    'brihati': ['बृहती', 'brihati', 'bṛhatī'],
    'shatpadhi': ['षट्पदी', 'shatpadi', 'ṣaṭpadī'],
    'shakvari': ['शक्वरी', 'shakvari', 'śakvarī'],
    'upajati': ['उपजाति', 'upajati', 'upajāti'],
    'totaka': ['तोटक', 'totaka', 'ṭoṭaka'],
    'bhujangaprayata': ['भुजङ्गप्रयात', 'bhujangaprayata', 'bhujaṅgaprayāta'],
    'vasantatilaka': ['वसन्ततिलका', 'vasantatilaka', 'vasantatilakā'],
    'malini': ['मालिनी', 'malini', 'mālinī'],
    'shikharini': ['शिखरिणी', 'shikharini', 'śikhariṇī'],
    'shardula': ['शार्दूलविक्रीडित', 'shardulavikriditam', 'śārdūlavikrīḍita'],
    'indravajra': ['इन्द्रवज्रा', 'indravajra', 'indravajrā'],
    'upendravajra': ['उपेन्द्रवज्रा', 'upendravajra', 'upendravajrā'],
    'vamshastha': ['वंशशस्थ', 'vamshastha', 'vaṃśastha'],
    'drutavilambita': ['द्रुतविलम्बित', 'drutavilambita', 'drutavilambita'],
    'mandakranta': ['मन्दाक्रान्ता', 'mandakranta', 'mandākrāntā'],
    'arya': ['आर्या', 'arya', 'āryā'],
    'pushpitagra': ['पुष्पिताग्रा', 'pushpitagra', 'puṣpitāgrā'],
    'prithvi': ['पृथ्वी', 'prithvi', 'pṛthvī'],
    'harini': ['हरिणी', 'harini', 'hariṇī'],
    'champakamala': ['चम्पकमाला', 'champakamala', 'campakamālā'],
    'kusumitalatavellatā': ['कुसुमितलतावेल्लिता', 'kusumitalatavellita'],
    'giti': ['गीति', 'giti', 'gīti'],
    'udgiti': ['उद्गीति', 'udgiti', 'udgīti'],
}


def normalize_name(name):
    """Normalize meter name for comparison"""
    if not name:
        return ""
    name = name.strip().lower()
    # Normalize common diacritics
    replacements = {
        'ā': 'a',
        'ī': 'i',
        'ū': 'u',
        'ṛ': 'r',
        'ṝ': 'r',
        'ṅ': 'n',
        'ñ': 'n',
        'ṭ': 't',
        'ḍ': 'd',
        'ṇ': 'n',
        'ś': 's',
        'ṣ': 's',
        'ḥ': 'h',
        'ṃ': 'm',
        '-': '',
        '_': '',
        ' ': '',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name


def names_match(expected, detected):
    """Check if expected and detected meter names match (handles Devanagari/English)"""
    if not expected or not detected:
        return False

    expected_norm = normalize_name(expected)
    detected_norm = normalize_name(detected)

    # Direct comparison
    if expected_norm in detected_norm or detected_norm in expected_norm:
        return True

    # Check via mapping
    for key, aliases in METER_NAME_MAPPING.items():
        if expected_norm in key or key in expected_norm:
            # Check if detected matches any alias
            for alias in aliases:
                alias_norm = normalize_name(alias)
                if alias_norm in detected_norm or detected_norm in alias_norm:
                    return True
                # Also check if detected (in Devanagari) is the alias
                if alias in detected or detected in alias:
                    return True

    return False


def check_match(expected, result_dict):
    """Check if expected meter is found in results"""
    if not result_dict:
        return False, None

    # Handle the result format from identify_line
    # Format: {'found': bool, 'chanda': [...], 'fuzzy': [...], 'lg_marks': ...}
    first_name = None

    # Check exact matches in 'chanda'
    chanda_list = result_dict.get('chanda', [])
    if chanda_list:
        # chanda is a list of tuples: (name, (pada_info,))
        for item in chanda_list:
            if isinstance(item, (list, tuple)) and len(item) > 0:
                name = item[0] if isinstance(item[0], str) else str(item[0])
                if not first_name:
                    first_name = name
                if names_match(expected, name):
                    return True, first_name

    # Check fuzzy matches
    fuzzy_list = result_dict.get('fuzzy', [])
    for fuzzy in fuzzy_list:
        chanda_matches = fuzzy.get('chanda', [])
        for item in chanda_matches:
            if isinstance(item, (list, tuple)) and len(item) > 0:
                name = item[0] if isinstance(item[0], str) else str(item[0])
                if not first_name:
                    first_name = name
                if names_match(expected, name):
                    return True, first_name

    # Also check alternative result formats (results key)
    results = result_dict.get('results', [])
    if results:
        for result in results:
            if isinstance(result, dict):
                names = result.get('chanda_names', [])
                if not first_name and names:
                    first_name = names[0]
                for name in names:
                    if names_match(expected, name):
                        return True, first_name

    return False, first_name


def run_test():
    """Run the comparison test"""
    print("=" * 90)
    print("CHANDAS IDENTIFIER - MODEL PERFORMANCE COMPARISON")
    print("=" * 90)
    print()

    # Initialize paths
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    our_data_path = os.path.join(base_path, 'data')
    iitk_data_path = os.path.join(base_path, '..', 'repos', 'chanda', 'data')
    dataset_path = os.path.join(our_data_path, 'chanda_dataset_verified.csv')

    # Initialize models
    print("Initializing models...")
    start = time.time()
    our_model = OurChanda(our_data_path)
    our_init = time.time() - start
    print(f"  ✓ Our Model (2055 meters) initialized in {our_init:.3f}s")

    start = time.time()
    iitk_model = IITKChanda(iitk_data_path)
    iitk_init = time.time() - start
    print(f"  ✓ IITK Model (398 meters) initialized in {iitk_init:.3f}s")
    print()

    # Load test dataset
    test_cases = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Chandas Name') and row.get('Example Shloka'):
                test_cases.append(
                    {
                        'expected': row['Chandas Name'].strip(),
                        'shloka': row['Example Shloka'].strip(),
                        'syllables': row.get('Syllables per Quarter', ''),
                        'lg_pattern': row.get('L-G Pattern', ''),
                    }
                )

    print(f"Loaded {len(test_cases)} test cases from chanda_dataset_verified.csv")
    print()
    print("-" * 90)
    print(f"{'#':3} {'Expected Meter':25} {'Our Model':20} {'IITK Model':20} {'Our':5} {'IITK':5}")
    print("-" * 90)

    # Run tests
    our_correct = 0
    our_times = []
    iitk_correct = 0
    iitk_times = []

    our_wins = []
    iitk_wins = []
    both_fail = []

    for i, tc in enumerate(test_cases, 1):
        expected = tc['expected']
        shloka = tc['shloka']

        # Clean up the shloka - extract first pada for single-line testing
        # Remove special punctuation and split into padas
        clean_shloka = shloka.replace('।', ' ').replace('॥', ' ').strip()
        padas = [p.strip() for p in clean_shloka.split() if p.strip()]

        # Use first half (first 2 padas if available) for testing
        test_text = ' '.join(padas[:4]) if len(padas) >= 4 else clean_shloka

        # Test our model
        start = time.time()
        try:
            our_result = our_model.identify_line(test_text, fuzzy=True)
            our_match, our_got = check_match(expected, our_result)
        except Exception as e:
            our_match, our_got = False, f"Error: {str(e)[:15]}"
        our_time = time.time() - start
        our_times.append(our_time)

        # Test IITK model
        start = time.time()
        try:
            iitk_result = iitk_model.identify_line(test_text, fuzzy=True)
            iitk_match, iitk_got = check_match(expected, iitk_result)
        except Exception as e:
            iitk_match, iitk_got = False, f"Error: {str(e)[:15]}"
        iitk_time = time.time() - start
        iitk_times.append(iitk_time)

        # Update counts
        if our_match:
            our_correct += 1
        if iitk_match:
            iitk_correct += 1

        # Track wins
        if our_match and not iitk_match:
            our_wins.append(expected)
        elif iitk_match and not our_match:
            iitk_wins.append(expected)
        elif not our_match and not iitk_match:
            both_fail.append(expected)

        # Display
        our_status = "✅" if our_match else "❌"
        iitk_status = "✅" if iitk_match else "❌"
        our_display = (our_got or "None")[:18]
        iitk_display = (iitk_got or "None")[:18]

        print(f"{i:3} {expected:25} {our_display:20} {iitk_display:20} {our_status:5} {iitk_status:5}")

    # Summary
    print()
    print("=" * 90)
    print("RESULTS SUMMARY")
    print("=" * 90)
    print()

    our_accuracy = our_correct / max(1, len(test_cases)) * 100
    iitk_accuracy = iitk_correct / max(1, len(test_cases)) * 100
    our_avg_time = sum(our_times) / max(1, len(our_times)) * 1000
    iitk_avg_time = sum(iitk_times) / max(1, len(iitk_times)) * 1000

    print(f"{'Metric':<35} {'Our Model':>20} {'IITK Model':>20}")
    print("-" * 75)
    print(f"{'Database Size':<35} {'2,055 meters':>20} {'398 meters':>20}")
    print(f"{'Test Cases':<35} {len(test_cases):>20} {len(test_cases):>20}")
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
    else:
        print(f"  🐢 IITK model is {1 / speed_ratio:.1f}x faster")
    print()

    # Detailed breakdown
    if our_wins:
        print(f"METERS ONLY OUR MODEL IDENTIFIED ({len(our_wins)}):")
        for m in our_wins:
            print(f"  ✅ {m}")
        print()

    if iitk_wins:
        print(f"METERS ONLY IITK MODEL IDENTIFIED ({len(iitk_wins)}):")
        for m in iitk_wins:
            print(f"  ⚠️ {m}")
        print()

    if both_fail:
        print(f"METERS BOTH MODELS FAILED ({len(both_fail)}):")
        for m in both_fail:
            print(f"  ❌ {m}")
        print()

    print("=" * 90)
    print(f"FINAL VERDICT: Our Model {our_accuracy:.1f}% vs IITK Model {iitk_accuracy:.1f}%")
    print("=" * 90)

    return our_accuracy, iitk_accuracy


if __name__ == '__main__':
    run_test()
