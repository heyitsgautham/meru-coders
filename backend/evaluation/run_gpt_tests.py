#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for chanda_gpt.py implementation.

Tests chanda_gpt.py against all three test suites:
1. test_csv_accuracy.py - CSV dataset accuracy
2. test_rigveda_validation.py - Rigveda validation
3. test_matching_chandas_dataset.py - Matching chandas dataset

Usage:
    python tests/run_gpt_tests.py              # Run all tests
    python tests/run_gpt_tests.py --csv        # Run CSV test only
    python tests/run_gpt_tests.py --rigveda    # Run Rigveda test only
    python tests/run_gpt_tests.py --matching   # Run matching chandas test only
    python tests/run_gpt_tests.py -v           # Verbose mode
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent.parent)
sys.path.insert(0, backend_path)

# Import the adapter directly
import importlib.util

adapter_path = Path(__file__).parent / 'test_chanda_gpt_adapter.py'
spec = importlib.util.spec_from_file_location("chanda_gpt_adapter", adapter_path)
adapter_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter_module)
ChandaGPTAdapter = adapter_module.ChandaGPTAdapter

# Import test utilities
import csv

import pandas as pd


def test_csv_accuracy(verbose=False):
    """Test against CSV dataset (test_csv_accuracy.py logic)"""
    print("\n" + "="*75)
    print("TEST 1: CSV ACCURACY (page 1-47 chanda list - complete.csv)")
    print("="*75)

    from config.settings import Settings
    settings = Settings()

    # Initialize adapter
    c = ChandaGPTAdapter(data_path=str(settings.DATA_DIR))

    # Read CSV
    csv_path = settings.DATA_DIR / 'page 1-47 chanda list - complete.csv'
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return {'accuracy': 0.0}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Import normalization functions directly from test file
    import importlib.util
    test_csv_path = Path(__file__).parent / 'test_csv_accuracy.py'
    spec = importlib.util.spec_from_file_location("test_csv_accuracy", test_csv_path)
    test_csv_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_csv_module)

    normalize = test_csv_module.normalize
    get_family = test_csv_module.get_family
    meters_match = test_csv_module.meters_match
    REAL_VERSE_COUNT = test_csv_module.REAL_VERSE_COUNT

    correct = 0
    total = 0
    issues = []

    row_index = 0
    for row in rows:
        if len(row) >= 4:
            verse = row[0].strip()
            expected = row[3].strip()

            if not verse or expected.lower() == 'chanda':
                continue

            row_index += 1

            # Only test real verses
            if row_index > REAL_VERSE_COUNT:
                continue

            # Test with adapter
            result = c.identify_from_text(verse, verse=False)

            # Extract prediction
            predicted = None
            if result and 'result' in result and result['result'].get('line'):
                first_line = result['result']['line'][0]
                if first_line and 'result' in first_line and first_line['result'].get('chanda'):
                    chanda_list = first_line['result']['chanda']
                    if chanda_list and chanda_list[0]:
                        predicted = chanda_list[0][0]

            total += 1

            if predicted and meters_match(expected, predicted):
                correct += 1
            else:
                issues.append({
                    'row': row_index,
                    'expected': expected,
                    'predicted': predicted or 'NO RESULT',
                    'verse': verse[:60]
                })

    accuracy = 100 * correct / total if total > 0 else 0

    print("\n📊 FIRST-LINE ACCURACY")
    print(f"   Total verses tested: {total}")
    print(f"   Correct predictions: {correct}")
    print(f"   ACCURACY: {accuracy:.1f}%")

    if verbose and issues:
        print("\n   ❌ Mismatches (first 5):")
        for i, issue in enumerate(issues[:5], 1):
            print(f"      {i}. Row {issue['row']}: Expected '{issue['expected']}' → Got '{issue['predicted']}'")
        if len(issues) > 5:
            print(f"      ... and {len(issues) - 5} more")

    print("="*75)
    return {'accuracy': accuracy, 'correct': correct, 'total': total}


def test_rigveda_validation(verbose=False, limit=100):
    """Test against Rigveda dataset (test_rigveda_validation.py logic)"""
    print("\n" + "="*75)
    print("TEST 2: RIGVEDA VALIDATION (rigveda_with_meters_complete.csv)")
    print("="*75)

    from config.settings import Settings
    settings = Settings()

    # Initialize adapter
    c = ChandaGPTAdapter(data_path=str(settings.DATA_DIR))

    # Load dataset
    csv_path = settings.DATA_DIR / 'rigveda_with_meters_complete.csv'
    if not csv_path.exists():
        print(f"❌ Rigveda CSV file not found: {csv_path}")
        return {'accuracy': 0.0}

    # Import normalization from test file
    import importlib.util
    test_rigveda_path = Path(__file__).parent / 'test_rigveda_validation.py'
    spec = importlib.util.spec_from_file_location("test_rigveda_validation", test_rigveda_path)
    test_rigveda_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_rigveda_module)

    normalize_meter_name = test_rigveda_module.normalize_meter_name
    meters_match = test_rigveda_module.meters_match

    # Load data
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            meter_name = normalize_meter_name(row.get('chandas', ''))
            if meter_name and row.get('full_verse'):
                data.append({
                    'verse_text': row['full_verse'],
                    'expected_meter': meter_name,
                    'ref': row.get('reference', 'unknown')
                })

    # Limit data
    if limit and limit < len(data):
        data = data[:limit]

    total = len(data)
    exact_matches = 0
    family_matches = 0

    print(f"\n🔍 Testing {total} verses from Rigveda dataset...")

    for i, entry in enumerate(data):
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{total} ({(i + 1) * 100 // total}%)")

        verse_text = entry['verse_text']
        expected_meter = entry['expected_meter']

        # Use Vedic mode
        result = c._identify_vedic_mode(verse_text)
        predicted_meter = result.get('meter')

        # Check match
        exact, family = meters_match(expected_meter, predicted_meter)

        if exact:
            exact_matches += 1
        elif family:
            family_matches += 1

    exact_accuracy = (exact_matches / total * 100) if total > 0 else 0
    family_accuracy = ((exact_matches + family_matches) / total * 100) if total > 0 else 0

    print("\n📊 RIGVEDA VALIDATION RESULTS")
    print(f"   Total verses: {total}")
    print(f"   Exact matches: {exact_matches} ({exact_accuracy:.2f}%)")
    print(f"   Family matches: {family_matches}")
    print(f"   📈 EXACT ACCURACY: {exact_accuracy:.2f}%")
    print(f"   📈 FAMILY ACCURACY: {family_accuracy:.2f}%")

    print("="*75)
    return {'exact_accuracy': exact_accuracy, 'family_accuracy': family_accuracy, 'total': total}


def test_matching_chandas(verbose=False, limit=100):
    """Test against matching chandas dataset (test_matching_chandas_dataset.py logic)"""
    print("\n" + "="*75)
    print("TEST 3: MATCHING CHANDAS DATASET (matching_chandas.csv)")
    print("="*75)

    from config.settings import Settings
    settings = Settings()

    # Initialize adapter
    c = ChandaGPTAdapter(data_path=str(settings.DATA_DIR))

    # Load dataset
    csv_path = settings.DATA_DIR / 'matching_chandas.csv'
    if not csv_path.exists():
        print(f"❌ Matching chandas CSV file not found: {csv_path}")
        return {'accuracy': 0.0}

    df = pd.read_csv(csv_path)

    if limit and limit < len(df):
        df = df.sample(n=limit, random_state=42)

    total = len(df)
    matches = 0

    import importlib.util
    test_matching_path = Path(__file__).parent / 'test_matching_chandas_dataset.py'
    spec = importlib.util.spec_from_file_location("test_matching_chandas", test_matching_path)
    test_matching_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_matching_module)

    normalize_chandas_name = test_matching_module.normalize_chandas_name

    # Normalize chandas names
    df['chandas_normalized'] = df['chandas'].apply(normalize_chandas_name)

    print(f"\n🔍 Testing {total} verses from matching chandas dataset...")

    for idx, row in df.iterrows():
        if (idx + 1) % 50 == 0:
            print(f"  Progress: {idx + 1}/{total} ({(idx + 1) * 100 // total}%)")

        verse = row['full_verse']
        expected = row['chandas_normalized']

        # Split into lines
        lines = [line.strip() for line in verse.split('\n') if line.strip()]

        # Test
        if len(lines) == 1:
            identification = c.identify_line(lines[0])
            primary = identification.get('display_chanda_primary', '')
        else:
            verse_result = c.identify_verse_holistically(lines)
            primary = verse_result.get('meter', '')

        # Check match
        if expected in primary:
            matches += 1

    accuracy = (matches / total * 100) if total > 0 else 0

    print("\n📊 MATCHING CHANDAS RESULTS")
    print(f"   Total verses: {total}")
    print(f"   Correct matches: {matches}")
    print(f"   ACCURACY: {accuracy:.2f}%")

    print("="*75)
    return {'accuracy': accuracy, 'correct': matches, 'total': total}


def main():
    parser = argparse.ArgumentParser(description='Test chanda_gpt.py against all test suites')
    parser.add_argument('--csv', action='store_true', help='Run CSV test only')
    parser.add_argument('--rigveda', action='store_true', help='Run Rigveda test only')
    parser.add_argument('--matching', action='store_true', help='Run matching chandas test only')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--limit', type=int, default=100, help='Limit verses for Rigveda/matching tests')
    args = parser.parse_args()

    run_all = not (args.csv or args.rigveda or args.matching)

    results = {}

    print("\n" + "="*75)
    print("🧪 TESTING chanda_gpt.py IMPLEMENTATION")
    print("="*75)

    if run_all or args.csv:
        results['csv'] = test_csv_accuracy(verbose=args.verbose)

    if run_all or args.rigveda:
        results['rigveda'] = test_rigveda_validation(verbose=args.verbose, limit=args.limit)

    if run_all or args.matching:
        results['matching'] = test_matching_chandas(verbose=args.verbose, limit=args.limit)

    # Summary
    print("\n" + "="*75)
    print("📈 COMPREHENSIVE TEST SUMMARY")
    print("="*75)

    if 'csv' in results:
        print(f"\n✅ CSV Accuracy: {results['csv']['accuracy']:.1f}%")

    if 'rigveda' in results:
        print(f"✅ Rigveda Exact: {results['rigveda']['exact_accuracy']:.1f}%")
        print(f"   Rigveda Family: {results['rigveda']['family_accuracy']:.1f}%")

    if 'matching' in results:
        print(f"✅ Matching Chandas: {results['matching']['accuracy']:.1f}%")

    print("\n" + "="*75)
    print("\n💡 NOTES:")
    print("   - chanda_gpt.py uses only 12 Vedic meters (basic + variants)")
    print("   - No pattern-based matching or fuzzy logic")
    print("   - Syllable counting and pada structure heuristics only")
    print("   - Lower accuracy expected vs. full rule-based system")
    print("="*75 + "\n")


if __name__ == '__main__':
    main()
