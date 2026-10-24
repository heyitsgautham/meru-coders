#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Detect Mode Accuracy Test

Tests the accuracy of mode='auto' against the SAME datasets used by:
1. test_rigveda_validation.py - Rigveda dataset (10,000+ Vedic verses)
2. test_csv_accuracy.py - Classical poetry dataset (147 verses)

This compares auto-detect performance against explicit mode='vedic' and
mode='classical' to measure any accuracy loss from automatic mode selection.

Key Metrics:
- Rigveda (Vedic): Compare auto vs explicit vedic mode
- Classical CSV: Compare auto vs explicit classical mode (verse=False)
- Overall: Combined accuracy across both datasets

Usage:
    python tests/test_autodetect_accuracy.py              # Quick test (sample)
    python tests/test_autodetect_accuracy.py --full       # Full dataset test
    python tests/test_autodetect_accuracy.py --rigveda    # Rigveda only
    python tests/test_autodetect_accuracy.py --csv        # CSV only
    python tests/test_autodetect_accuracy.py -v           # Verbose mode

Author: Meru Coders Team (SIH 2025)
"""

import argparse
import csv
import os
import sys
import unicodedata
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from core.chanda import Chanda

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate

    HAS_TRANSLITERATION = True
except ImportError:
    HAS_TRANSLITERATION = False


# ============================================================================
# METER NORMALIZATION (from test_rigveda_validation.py)
# ============================================================================

METER_NORMALIZATION = {
    # Standard Vedic meters (7 major)
    'gāyatrī': 'गायत्री',
    'gayatri': 'गायत्री',
    'uṣṇik': 'उष्णिक्',
    'uṣnik': 'उष्णिक्',
    'usnik': 'उष्णिक्',
    'anuṣṭup': 'अनुष्टुभ्',
    'anuṣṭubh': 'अनुष्टुभ्',
    'anustup': 'अनुष्टुभ्',
    'bṛhatī': 'बृहती',
    'brhati': 'बृहती',
    'paṅktiḥ': 'पङ्क्ति',
    'paṅkti': 'पङ्क्ति',
    'pankti': 'पङ्क्ति',
    'triṣṭup': 'त्रिष्टुभ्',
    'triṣṭubh': 'त्रिष्टुभ्',
    'tristup': 'त्रिष्टुभ्',
    'jagatī': 'जगती',
    'jagati': 'जगती',
    # Extended Vedic meters
    'virāṭ': 'विराट्',
    'virat': 'विराट्',
    'pragāthaḥ': 'प्रगाथ',
    'pragātha': 'प्रगाथ',
    'mahāpaṅktiḥ': 'महापङ्क्ति',
    'mahāpaṅkti': 'महापङ्क्ति',
    'kakup': 'ककुभ्',
    'kakubh': 'ककुभ्',
    'dvipadā virāṭ': 'द्विपदा विराट्',
    'dvipadā triṣṭup': 'द्विपदा त्रिष्टुभ्',
}

# Meter families for fuzzy matching
METER_FAMILIES = {
    'गायत्री': ['गायत्री'],
    'उष्णिक्': ['उष्णिक्', 'ककुभ्'],
    'अनुष्टुभ्': ['अनुष्टुभ्'],
    'बृहती': ['बृहती', 'प्रगाथ', 'पङ्क्ति'],
    'पङ्क्ति': ['पङ्क्ति', 'बृहती', 'प्रगाथ', 'त्रिष्टुभ्'],
    'त्रिष्टुभ्': ['त्रिष्टुभ्', 'जगती', 'पङ्क्ति'],
    'जगती': ['जगती', 'त्रिष्टुभ्'],
    'विराट्': ['विराट्', 'गायत्री', 'उष्णिक्'],
    'प्रगाथ': ['प्रगाथ', 'बृहती', 'पङ्क्ति', 'त्रिष्टुभ्', 'जगती'],
    'ककुभ्': ['ककुभ्', 'उष्णिक्', 'बृहती'],
    'महापङ्क्ति': ['महापङ्क्ति', 'पङ्क्ति', 'जगती'],
}


def normalize_meter_name(name):
    """Normalize meter name from IAST to Devanagari"""
    if not name:
        return None
    name = name.strip().lower()
    if name.startswith('('):
        return None
    if name in METER_NORMALIZATION:
        return METER_NORMALIZATION[name]
    # Try without diacritics
    simple = name.replace('ṭ', 't').replace('ṣ', 's').replace('ṇ', 'n').replace('ī', 'i').replace('ā', 'a')
    for key, value in METER_NORMALIZATION.items():
        simple_key = key.replace('ṭ', 't').replace('ṣ', 's').replace('ṇ', 'n').replace('ī', 'i').replace('ā', 'a')
        if simple == simple_key:
            return value
    return None


def get_meter_family(meter_name):
    """Get the family of a meter"""
    for family, members in METER_FAMILIES.items():
        if meter_name in members:
            return family
    return meter_name


def meters_match_vedic(expected, predicted):
    """Check if meters match for Vedic dataset (with family matching)"""
    if not expected or not predicted:
        return False, False
    if expected == predicted:
        return True, True
    # Family match
    exp_family = get_meter_family(expected)
    pred_family = get_meter_family(predicted)
    if exp_family == pred_family:
        return False, True
    # Check cross-family
    for family, members in METER_FAMILIES.items():
        if expected in members and predicted in members:
            return False, True
    return False, False


# ============================================================================
# CSV METER MATCHING (from test_csv_accuracy.py)
# ============================================================================


def to_iast(text):
    """Convert Devanagari to IAST"""
    if not HAS_TRANSLITERATION:
        return text
    try:
        return transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
    except:
        return text


def normalize_csv(name):
    """Normalize meter name for CSV comparison"""
    name = name.lower().strip()
    name = to_iast(name)
    name = unicodedata.normalize('NFD', name)
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))
    return name


CSV_METER_FAMILIES = {
    'anustup': 'anustubh',
    'anustubh': 'anustubh',
    'sardulavkridita': 'sardula',
    'sardulavikriditam': 'sardula',
    'sardulavikridita': 'sardula',
    'upajatih': 'upajati',
    'upajati': 'upajati',
    'indravajra': 'upajati',
    'upendravajra': 'upajati',
    'vasantatilakam': 'vasantatilaka',
    'vasantatilaka': 'vasantatilaka',
    'mandakranta': 'mandakranta',
    'mandakrantam': 'mandakranta',
    'sragdhara': 'sragdhara',
    'pancakavali': 'sragdhara',
    'bhujangaprayatam': 'bhujanga',
    'bhujangaprayata': 'bhujanga',
}


def get_csv_family(name):
    """Get meter family for CSV comparison"""
    norm = normalize_csv(name)
    return CSV_METER_FAMILIES.get(norm, norm)


def meters_match_csv(expected, predicted):
    """Check if two meter names match for CSV dataset"""
    exp_fam = get_csv_family(expected)
    pred_fam = get_csv_family(predicted)
    if exp_fam == pred_fam:
        return True
    if exp_fam in pred_fam or pred_fam in exp_fam:
        return True
    return False


# ============================================================================
# RIGVEDA DATASET TESTING
# ============================================================================


def load_rigveda_dataset(filepath, limit=None):
    """Load the Rigveda dataset"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            verse_text = row.get('verse_text', '').strip()
            meter = row.get('meter', '').strip()
            if not verse_text or not meter or meter.startswith('('):
                continue
            normalized = normalize_meter_name(meter)
            if not normalized:
                continue
            data.append(
                {
                    'ref': f"{row.get('mandala', '')}.{row.get('sukta', '')}.{row.get('rik', '')}",
                    'verse_text': verse_text,
                    'expected_meter': normalized,
                    'original_meter': meter,
                }
            )
            if limit and len(data) >= limit:
                break
    return data


def test_rigveda_autodetect(chanda, data, verbose=False):
    """
    Test auto-detect mode on Rigveda dataset.
    Compare with explicit vedic mode results.
    """
    results = {
        'auto': {'exact': 0, 'family': 0, 'miss': 0},
        'vedic': {'exact': 0, 'family': 0, 'miss': 0},
    }
    meter_stats = defaultdict(
        lambda: {'auto_exact': 0, 'auto_family': 0, 'vedic_exact': 0, 'vedic_family': 0, 'total': 0}
    )
    mismatches = []

    total = len(data)
    print(f"\n🔍 Testing {total} Rigveda verses...")

    for i, entry in enumerate(data):
        if i % 2000 == 0 and i > 0:
            print(f"  Progress: {i}/{total} ({i * 100 // total}%)")

        verse_text = entry['verse_text']
        expected = entry['expected_meter']

        # Test with mode='auto'
        result_auto = chanda.identify_from_text(verse_text, verse=True, mode='auto')
        auto_meter = extract_meter(result_auto)

        # Test with mode='vedic'
        result_vedic = chanda.identify_from_text(verse_text, verse=True, mode='vedic')
        vedic_meter = extract_meter(result_vedic)

        # Check matches
        auto_exact, auto_family = meters_match_vedic(expected, auto_meter)
        vedic_exact, vedic_family = meters_match_vedic(expected, vedic_meter)

        # Update stats
        meter_stats[expected]['total'] += 1

        if auto_exact:
            results['auto']['exact'] += 1
            meter_stats[expected]['auto_exact'] += 1
        elif auto_family:
            results['auto']['family'] += 1
            meter_stats[expected]['auto_family'] += 1
        else:
            results['auto']['miss'] += 1
            if len(mismatches) < 100:
                mismatches.append(
                    {
                        'ref': entry['ref'],
                        'expected': expected,
                        'auto': auto_meter,
                        'vedic': vedic_meter,
                    }
                )

        if vedic_exact:
            results['vedic']['exact'] += 1
            meter_stats[expected]['vedic_exact'] += 1
        elif vedic_family:
            results['vedic']['family'] += 1
            meter_stats[expected]['vedic_family'] += 1
        else:
            results['vedic']['miss'] += 1

    return results, meter_stats, mismatches


# ============================================================================
# CSV DATASET TESTING
# ============================================================================

REAL_VERSE_COUNT = 147  # First 147 rows are real verses


def load_csv_dataset(filepath):
    """Load the classical CSV dataset"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    row_index = 0
    for row in rows:
        if len(row) >= 4:
            verse = row[0].strip()
            expected = row[3].strip()
            if not verse or expected.lower() == 'chanda':
                continue
            row_index += 1
            if row_index > REAL_VERSE_COUNT:
                break
            data.append(
                {
                    'verse': verse,
                    'expected_meter': expected,
                    'row': row_index,
                }
            )
    return data


def test_csv_autodetect(chanda, data, verbose=False):
    """
    Test auto-detect mode on CSV dataset.
    Compare with standard (no mode) results.
    """
    results = {
        'auto': {'correct': 0, 'incorrect': 0},
        'standard': {'correct': 0, 'incorrect': 0},
    }
    mismatches = []

    total = len(data)
    print(f"\n🔍 Testing {total} CSV verses...")

    for entry in data:
        verse = entry['verse']
        expected = entry['expected_meter']

        # Test with mode='auto'
        result_auto = chanda.identify_from_text(verse, verse=False, mode='auto')
        auto_meter = extract_first_line_meter(result_auto)

        # Test with standard (no mode specified, defaults to classical pattern matching)
        result_std = chanda.identify_from_text(verse, verse=False)
        std_meter = extract_first_line_meter(result_std)

        # Check matches
        auto_match = auto_meter and meters_match_csv(expected, auto_meter)
        std_match = std_meter and meters_match_csv(expected, std_meter)

        if auto_match:
            results['auto']['correct'] += 1
        else:
            results['auto']['incorrect'] += 1
            if len(mismatches) < 50:
                mismatches.append(
                    {
                        'row': entry['row'],
                        'expected': expected,
                        'auto': auto_meter,
                        'standard': std_meter,
                    }
                )

        if std_match:
            results['standard']['correct'] += 1
        else:
            results['standard']['incorrect'] += 1

    return results, mismatches


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def extract_meter(result):
    """Extract primary meter from result"""
    if not result or 'result' not in result:
        return None
    inner = result['result']
    # Try verse level
    verses = inner.get('verse', [])
    if verses and verses[0].get('chanda'):
        chanda = verses[0]['chanda']
        if chanda and chanda[0]:
            return chanda[0][0] if isinstance(chanda[0], list) else chanda[0]
    # Try line level
    lines = inner.get('line', [])
    if lines and lines[0].get('result', {}).get('chanda'):
        chanda = lines[0]['result']['chanda']
        if chanda:
            return chanda[0][0] if isinstance(chanda[0], tuple) else chanda[0]
    return None


def extract_first_line_meter(result):
    """Extract meter from first line result"""
    if result and 'result' in result and result['result'].get('line'):
        first_line = result['result']['line'][0]
        if first_line and 'result' in first_line and first_line['result'].get('chanda'):
            return first_line['result']['chanda'][0][0]
    return None


# ============================================================================
# MAIN
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description='Test auto-detect mode accuracy')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--full', action='store_true', help='Test full datasets (slower)')
    parser.add_argument('--rigveda', action='store_true', help='Test Rigveda only')
    parser.add_argument('--csv', action='store_true', help='Test CSV only')
    parser.add_argument('-n', '--limit', type=int, help='Limit Rigveda verses')
    args = parser.parse_args()

    # Initialize
    print("Initializing Chanda identifier...")
    chanda = Chanda(data_path=str(settings.DATA_DIR))

    # Determine what to test
    test_rigveda = args.rigveda or (not args.csv)
    test_csv = args.csv or (not args.rigveda)

    # Set limits
    rigveda_limit = args.limit if args.limit else (None if args.full else 1000)

    print("\n" + "=" * 70)
    print("AUTO-DETECT MODE ACCURACY TEST")
    print("=" * 70)

    rigveda_results = None
    csv_results = None

    # ===== RIGVEDA TESTING =====
    if test_rigveda:
        rigveda_path = os.path.join(settings.DATA_DIR, 'rigveda_with_meters_complete.csv')
        if os.path.exists(rigveda_path):
            rigveda_data = load_rigveda_dataset(rigveda_path, limit=rigveda_limit)
            rigveda_results, meter_stats, mismatches = test_rigveda_autodetect(
                chanda, rigveda_data, verbose=args.verbose
            )

            total = len(rigveda_data)
            auto_exact = rigveda_results['auto']['exact']
            auto_family = rigveda_results['auto']['family']
            vedic_exact = rigveda_results['vedic']['exact']
            vedic_family = rigveda_results['vedic']['family']

            auto_exact_acc = auto_exact / total * 100
            auto_family_acc = (auto_exact + auto_family) / total * 100
            vedic_exact_acc = vedic_exact / total * 100
            vedic_family_acc = (vedic_exact + vedic_family) / total * 100

            print("\n" + "-" * 70)
            print("📜 RIGVEDA DATASET RESULTS")
            print("-" * 70)
            print(f"Total verses tested: {total}")
            print()
            print(f"{'Mode':<15} {'Exact':>10} {'Family':>10} {'Miss':>10} {'Exact%':>10} {'Family%':>10}")
            print("-" * 65)
            print(
                f"{'AUTO':<15} {auto_exact:>10} {auto_family:>10} {rigveda_results['auto']['miss']:>10} {auto_exact_acc:>9.1f}% {auto_family_acc:>9.1f}%"
            )
            print(
                f"{'VEDIC':<15} {vedic_exact:>10} {vedic_family:>10} {rigveda_results['vedic']['miss']:>10} {vedic_exact_acc:>9.1f}% {vedic_family_acc:>9.1f}%"
            )
            print()
            print(f"📊 Auto vs Vedic difference: {auto_family_acc - vedic_family_acc:+.1f}% (family accuracy)")

            if args.verbose and mismatches:
                print("\n❌ Sample mismatches (auto mode):")
                for m in mismatches[:10]:
                    print(f"  {m['ref']}: Expected '{m['expected']}' → Auto: '{m['auto']}', Vedic: '{m['vedic']}'")
        else:
            print(f"\n⚠️ Rigveda dataset not found: {rigveda_path}")

    # ===== CSV TESTING =====
    if test_csv:
        csv_path = os.path.join(settings.DATA_DIR, 'page 1-47 chanda list - complete.csv')
        if os.path.exists(csv_path):
            csv_data = load_csv_dataset(csv_path)
            csv_results, csv_mismatches = test_csv_autodetect(chanda, csv_data, verbose=args.verbose)

            total = csv_results['auto']['correct'] + csv_results['auto']['incorrect']
            auto_acc = csv_results['auto']['correct'] / total * 100
            std_acc = csv_results['standard']['correct'] / total * 100

            print("\n" + "-" * 70)
            print("📋 CLASSICAL CSV DATASET RESULTS")
            print("-" * 70)
            print(f"Total verses tested: {total}")
            print()
            print(f"{'Mode':<15} {'Correct':>10} {'Incorrect':>10} {'Accuracy':>12}")
            print("-" * 50)
            print(
                f"{'AUTO':<15} {csv_results['auto']['correct']:>10} {csv_results['auto']['incorrect']:>10} {auto_acc:>11.1f}%"
            )
            print(
                f"{'STANDARD':<15} {csv_results['standard']['correct']:>10} {csv_results['standard']['incorrect']:>10} {std_acc:>11.1f}%"
            )
            print()
            print(f"📊 Auto vs Standard difference: {auto_acc - std_acc:+.1f}%")

            if args.verbose and csv_mismatches:
                print("\n❌ Sample mismatches (auto mode):")
                for m in csv_mismatches[:10]:
                    print(f"  Row {m['row']}: Expected '{m['expected']}' → Auto: '{m['auto']}', Std: '{m['standard']}'")
        else:
            print(f"\n⚠️ CSV dataset not found: {csv_path}")

    # ===== SUMMARY =====
    print("\n" + "=" * 70)
    print("📈 SUMMARY")
    print("=" * 70)

    if rigveda_results:
        total_rv = len(rigveda_data) if 'rigveda_data' in dir() else 0
        auto_rv = (
            (rigveda_results['auto']['exact'] + rigveda_results['auto']['family']) / total_rv * 100 if total_rv else 0
        )
        vedic_rv = (
            (rigveda_results['vedic']['exact'] + rigveda_results['vedic']['family']) / total_rv * 100 if total_rv else 0
        )
        print("\nRigveda (Vedic texts):")
        print(f"  Auto mode:  {auto_rv:.1f}% family accuracy")
        print(f"  Vedic mode: {vedic_rv:.1f}% family accuracy")
        print(f"  Difference: {auto_rv - vedic_rv:+.1f}%")

    if csv_results:
        total_csv = csv_results['auto']['correct'] + csv_results['auto']['incorrect']
        auto_csv = csv_results['auto']['correct'] / total_csv * 100 if total_csv else 0
        std_csv = csv_results['standard']['correct'] / total_csv * 100 if total_csv else 0
        print("\nClassical CSV:")
        print(f"  Auto mode:     {auto_csv:.1f}% accuracy")
        print(f"  Standard mode: {std_csv:.1f}% accuracy")
        print(f"  Difference:    {auto_csv - std_csv:+.1f}%")

    # Overall assessment
    print("\n" + "-" * 70)
    if rigveda_results and csv_results:
        # Weighted average (Rigveda has more verses)
        total_all = total_rv + total_csv
        auto_weighted = (auto_rv * total_rv + auto_csv * total_csv) / total_all
        print(f"🎯 OVERALL AUTO-DETECT ACCURACY: {auto_weighted:.1f}%")

    print("=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
