#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compare syllabification methods on the full CSV dataset.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chanda import Chanda

# Number of real verses (as defined in test_csv_accuracy.py)
REAL_VERSE_COUNT = 147


def normalize_meter(name):
    """Normalize meter name for comparison"""
    name = name.lower().strip()
    # Common normalizations
    replacements = {
        'ä': 'a',
        'ü': 'u',
        'ö': 'o',
        'anushtup': 'anustubh',
        'anustup': 'anustubh',
        'anushtubh': 'anustubh',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name


def meters_match(expected, predicted):
    """Check if meters match (with some flexibility)"""
    exp_norm = normalize_meter(expected)
    pred_norm = normalize_meter(predicted)

    return exp_norm in pred_norm or pred_norm in exp_norm


def test_method(method_name, data_path, rows):
    """Test a specific syllabification method"""
    try:
        chanda = Chanda(data_path, syllabization_method=method_name)
    except Exception as e:
        return {'error': str(e)}

    correct = 0
    total = 0

    row_index = 0
    for row in rows:
        if len(row) < 4:
            continue

        verse = row[0].strip()
        expected = row[3].strip()

        if not verse or expected.lower() == 'chanda':
            continue

        row_index += 1
        if row_index > REAL_VERSE_COUNT:
            break

        # Get first line
        first_line = verse.split('\n')[0].strip()
        first_line = first_line.split('।')[0].strip()
        first_line = first_line.replace('॥', '').strip()

        if not first_line:
            continue

        try:
            result = chanda.identify_line(first_line)
            predicted = result.get('display_chanda_primary', '') or ''

            if meters_match(expected, predicted):
                correct += 1
        except:
            pass  # Count as incorrect

        total += 1

    return {'correct': correct, 'total': total, 'accuracy': (correct / total * 100) if total > 0 else 0}


def main():
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    csv_path = os.path.join(data_path, 'page 1-47 chanda list - complete.csv')

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)[1:]  # Skip header

    print("=" * 60)
    print("SYLLABIFICATION METHOD COMPARISON ON FULL CSV DATASET")
    print("=" * 60)
    print()

    methods = ['sanskrit_text', 'icu']
    results = {}

    for method in methods:
        print(f"Testing {method}...", end=" ", flush=True)
        result = test_method(method, data_path + '/', rows)
        results[method] = result

        if 'error' in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"{result['correct']}/{result['total']} = {result['accuracy']:.1f}%")

    print()
    print("-" * 60)
    print("SUMMARY:")
    print("-" * 60)

    best_method = None
    best_accuracy = 0

    for method, result in results.items():
        if 'error' not in result and result['accuracy'] > best_accuracy:
            best_accuracy = result['accuracy']
            best_method = method

    for method, result in results.items():
        if 'error' not in result:
            marker = " <-- BEST" if method == best_method else ""
            print(f"  {method}: {result['accuracy']:.1f}%{marker}")

    print()
    print("=" * 60)


if __name__ == '__main__':
    main()
