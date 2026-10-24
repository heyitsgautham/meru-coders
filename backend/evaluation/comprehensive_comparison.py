#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE MODEL PERFORMANCE COMPARISON
==========================================
SIH 2025 Grand Finale - Chandojñānam Project

Compares:
- Our Model (chanda.py with 2,055 meters database)
- IITK Reference Model (chanda_iitk.py with 398 meters database)

Uses ALL 35 test cases from chanda_dataset_verified.csv
"""

import csv
import os
import sys
import time

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'reference', 'alternative_implementations'))
)

from chanda_iitk import Chanda as IITKChanda
from core.chanda import Chanda as OurChanda

# Mapping of English names to Devanagari equivalents
METER_NAME_MAPPING = {
    'anushthubh': ['अनुष्टुभ्', 'anushtubh', 'anuṣṭubh'],
    'gayatri': ['गायत्री', 'gayatri', 'gāyatrī'],
    'trishtubh': ['त्रिष्टुभ्', 'trishtubh', 'triṣṭubh'],
    'jagati': ['जगती', 'jagati', 'jagatī'],
    'ushnik': ['उष्णिक्', 'ushnik', 'uṣṇik'],
    'pankti': ['पङ्क्ति', 'pankti', 'paṅkti'],
    'brihati': ['बृहती', 'brihati', 'bṛhatī'],
    'shatpadhi': ['षट्पदी', 'shatpadi'],
    'dvipadha': ['द्विपदा', 'dvipadha'],
    'viraja': ['विराज', 'viraja', 'virāj'],
    'prastarapankti': ['प्रस्तारपङ्क्ति', 'prastarapankti'],
    'mahabrihati': ['महाबृहती', 'mahabrihati'],
    'shakvari': ['शक्वरी', 'shakvari', 'śakvarī'],
    'upajati': ['उपजाति', 'upajati', 'upajāti'],
    'totaka': ['तोटक', 'totaka', 'ṭoṭaka'],
    'bhujangaprayata': ['भुजङ्गप्रयात', 'bhujangaprayata'],
    'vasantatilaka': ['वसन्ततिलका', 'vasantatilaka'],
    'malini': ['मालिनी', 'malini', 'mālinī'],
    'panchachamara': ['पञ्चचामर', 'panchachamara'],
    'shikharini': ['शिखरिणी', 'shikharini', 'śikhariṇī'],
    'shardula': ['शार्दूलविक्रीडित', 'shardulavikriditam'],
    'matra': ['मात्रा', 'matra'],
    'indravajra': ['इन्द्रवज्रा', 'indravajra'],
    'upendravajra': ['उपेन्द्रवज्रा', 'upendravajra'],
    'vamshastha': ['वंशस्थ', 'vamshastha', 'vaṃśastha'],
    'drutavilambita': ['द्रुतविलम्बित', 'drutavilambita'],
    'mandakranta': ['मन्दाक्रान्ता', 'mandakranta'],
    'arya': ['आर्या', 'arya', 'āryā'],
    'pushpitagra': ['पुष्पिताग्रा', 'pushpitagra'],
    'prithvi': ['पृथ्वी', 'prithvi', 'pṛthvī'],
    'harini': ['हरिणी', 'harini', 'hariṇī'],
    'champakamala': ['चम्पकमाला', 'champakamala'],
    'kusumitalatavellata': ['कुसुमितलतावेल्लिता', 'kusumitalatavellata'],
    'aupacchandasika': ['औपच्छन्दसिक', 'aupacchandasika'],
    'giti': ['गीति', 'giti', 'gīti'],
    'udgiti': ['उद्गीति', 'udgiti', 'udgīti'],
}


def normalize_name(name):
    """Normalize meter name for comparison"""
    if not name:
        return ""
    name = name.strip().lower()
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
    """Check if expected and detected meter names match"""
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
            for alias in aliases:
                alias_norm = normalize_name(alias)
                if alias_norm in detected_norm or detected_norm in alias_norm:
                    return True
                if alias in detected or detected in alias:
                    return True

    return False


def check_result(expected, result):
    """Check if expected meter is in result"""
    if not result:
        return False, None

    chanda_list = result.get('chanda', [])
    first_name = None

    if chanda_list:
        for item in chanda_list:
            if isinstance(item, (list, tuple)) and len(item) > 0:
                name = item[0]
                if not first_name:
                    first_name = name
                if names_match(expected, name):
                    return True, first_name

    fuzzy_list = result.get('fuzzy', [])
    for fuzzy in fuzzy_list:
        for item in fuzzy.get('chanda', []):
            if isinstance(item, (list, tuple)) and len(item) > 0:
                name = item[0]
                if not first_name:
                    first_name = name
                if names_match(expected, name):
                    return True, first_name

    return False, first_name


def load_dataset(filepath):
    """Load all 35 test cases from the verified dataset"""
    tests = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Chandas Name') and row.get('Example Shloka'):
                # Clean the shloka - remove punctuation marks
                shloka = row['Example Shloka'].strip()
                shloka = shloka.replace('।', ' ').replace('॥', ' ').strip()

                tests.append(
                    {
                        'name': row['Chandas Name'].strip(),
                        'expected': row['Chandas Name'].strip(),
                        'verse': shloka,
                        'syllables': row.get('Syllables per Quarter', ''),
                        'source': row.get('Translation/Source', '')[:30],
                    }
                )
    return tests


def main():
    print("=" * 100)
    print("CHANDOJÑĀNAM - COMPREHENSIVE MODEL PERFORMANCE COMPARISON")
    print("SIH 2025 Grand Finale | Meru Coders Team")
    print("Testing ALL 35 verses from chanda_dataset_verified.csv")
    print("=" * 100)
    print()

    # Initialize paths
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    our_data_path = os.path.join(base_path, 'data')
    iitk_data_path = os.path.join(base_path, '..', 'repos', 'chanda', 'data')
    dataset_path = os.path.join(our_data_path, 'chanda_dataset_verified.csv')

    print("Loading models...")
    our_model = OurChanda(our_data_path)
    iitk_model = IITKChanda(iitk_data_path)
    print("✓ Models loaded successfully")
    print()

    # Count database sizes
    our_count = 0
    for f in ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv', 'chanda_vedic.csv', 'chanda_matra.csv']:
        fp = os.path.join(our_data_path, f)
        if os.path.exists(fp):
            with open(fp, 'r') as fh:
                our_count += max(0, sum(1 for line in fh if line.strip()) - 1)

    iitk_count = 0
    for f in ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv']:
        fp = os.path.join(iitk_data_path, f)
        if os.path.exists(fp):
            with open(fp, 'r') as fh:
                iitk_count += max(0, sum(1 for line in fh if line.strip()) - 1)

    print("Database Comparison:")
    print(f"  Our Model:  {our_count:,} meters")
    print(f"  IITK Model: {iitk_count:,} meters")
    print(f"  Ratio:      {our_count / iitk_count:.1f}x larger")
    print()

    # Load all 35 test cases
    tests = load_dataset(dataset_path)
    print(f"Loaded {len(tests)} test cases from chanda_dataset_verified.csv")
    print()

    # Run tests
    print("=" * 100)
    print(f"{'#':>3} {'Expected Meter':<25} {'Our Model':<18} {'IITK Model':<18} {'Our':>5} {'IITK':>5}")
    print("=" * 100)

    our_correct = 0
    iitk_correct = 0
    our_times = []
    iitk_times = []

    our_wins = []
    iitk_wins = []
    both_correct = []
    both_fail = []

    for i, test in enumerate(tests, 1):
        expected = test['expected']
        verse = test['verse']

        # Test our model
        start = time.time()
        try:
            our_result = our_model.identify_line(verse, fuzzy=True)
            our_match, our_got = check_result(expected, our_result)
        except Exception:
            our_match, our_got = False, "Error"
        our_time = time.time() - start
        our_times.append(our_time)

        # Test IITK model
        start = time.time()
        try:
            iitk_result = iitk_model.identify_line(verse, fuzzy=True)
            iitk_match, iitk_got = check_result(expected, iitk_result)
        except Exception:
            iitk_match, iitk_got = False, "Error"
        iitk_time = time.time() - start
        iitk_times.append(iitk_time)

        if our_match:
            our_correct += 1
        if iitk_match:
            iitk_correct += 1

        # Track comparison
        if our_match and iitk_match:
            both_correct.append(expected)
        elif our_match and not iitk_match:
            our_wins.append(expected)
        elif iitk_match and not our_match:
            iitk_wins.append(expected)
        else:
            both_fail.append(expected)

        our_status = "✅" if our_match else "❌"
        iitk_status = "✅" if iitk_match else "❌"
        our_display = (our_got or "None")[:16]
        iitk_display = (iitk_got or "None")[:16]

        print(f"{i:>3} {expected:<25} {our_display:<18} {iitk_display:<18} {our_status:>5} {iitk_status:>5}")

    # Summary
    print()
    print("=" * 100)
    print("FINAL SUMMARY")
    print("=" * 100)
    print()

    total = len(tests)
    our_accuracy = our_correct / total * 100
    iitk_accuracy = iitk_correct / total * 100
    our_avg_time = sum(our_times) / len(our_times) * 1000
    iitk_avg_time = sum(iitk_times) / len(iitk_times) * 1000

    print(f"{'Metric':<45} {'Our Model':>25} {'IITK Model':>25}")
    print("-" * 100)
    print(f"{'Database Size':<45} {f'{our_count:,} meters':>25} {f'{iitk_count:,} meters':>25}")
    print(f"{'Total Test Cases':<45} {total:>25} {total:>25}")
    print(f"{'Correct Identifications':<45} {our_correct:>25} {iitk_correct:>25}")
    print(f"{'Accuracy':<45} {f'{our_accuracy:.1f}%':>25} {f'{iitk_accuracy:.1f}%':>25}")
    print(f"{'Average Time per Verse (ms)':<45} {f'{our_avg_time:.2f}':>25} {f'{iitk_avg_time:.2f}':>25}")
    print()

    # Detailed breakdown
    print("DETAILED BREAKDOWN:")
    print("-" * 50)
    print(f"  Both models correct:     {len(both_correct):>3} meters")
    print(f"  Only Our Model correct:  {len(our_wins):>3} meters")
    print(f"  Only IITK correct:       {len(iitk_wins):>3} meters")
    print(f"  Both models failed:      {len(both_fail):>3} meters")
    print()

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

    # Winner announcement
    print("=" * 100)
    diff = our_accuracy - iitk_accuracy
    if diff > 0:
        print("🏆 WINNER: OUR MODEL")
        print(f"   Accuracy: {our_accuracy:.1f}% vs IITK's {iitk_accuracy:.1f}% (+{diff:.1f}% improvement)")
        print(f"   Database: {our_count:,} vs {iitk_count:,} meters ({our_count / iitk_count:.1f}x larger)")
    elif diff < 0:
        print(f"📉 IITK Model leads: {iitk_accuracy:.1f}% vs Our's {our_accuracy:.1f}%")
    else:
        print(f"🤝 TIE: Both models at {our_accuracy:.1f}% accuracy")

    print()
    print("KEY ADVANTAGES OF OUR MODEL:")
    print(f"  ✓ {our_count:,} meters database (5.2x larger than IITK)")
    print("  ✓ Handles full multi-pada shlokas")
    print("  ✓ Vedic meter support with syllable-count detection")
    print("  ✓ Multi-level confidence scoring (7 levels)")
    print("  ✓ Vedic Unicode normalization")
    print("=" * 100)


if __name__ == '__main__':
    main()
