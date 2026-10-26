#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Suite for match_chandas.csv Dataset (Atharva Veda)

This test validates the Chanda identifier against 471 verses from the Atharva Veda
with authentic Vedic accent marks and 81 unique chandas types.

Dataset Quality:
- Source: Atharva Veda (authentic Vedic text with accent marks ॑ ॒)
- Total verses: 471
- Unique chandas: 81
- Completeness: 100% (no missing data)
- Structure: Complete verses with proper pada breaks (। ॥)

Test Levels:
1. FIRST-LINE ACCURACY: Check if first line's prediction matches expected meter
2. ALL-LINES ACCURACY: Check if ALL lines in a verse match the expected meter
3. VERSE-LEVEL ACCURACY: Check if holistic verse analysis (verse=True) matches

Usage:
    python backend/evaluation/match_chandas_dataset.py          # Run first-line accuracy (fastest)
    python backend/evaluation/match_chandas_dataset.py -v       # Verbose mode (show mismatches)
    python backend/evaluation/match_chandas_dataset.py --all    # Run all three accuracy types
    python backend/evaluation/match_chandas_dataset.py --verse  # Run verse-level only
    python backend/evaluation/match_chandas_dataset.py --all -v # Full analysis with details
"""

import argparse
import csv
import os
import sys

from backend.core.chanda import Chanda

# Import our comprehensive Vedic-Classical mappings
from backend.evaluation.match_chandas_matching import (
    extract_all_lines_predictions,
    extract_first_line_prediction,
    extract_verse_level_prediction,
    meters_match,
)


def test_first_line_accuracy(chanda, csv_path, verbose=False):
    """
    Test FIRST-LINE accuracy: Does the first line prediction match expected?
    This is the fastest test and most lenient (only checks first line).
    """
    print("=" * 80)
    print("TEST 1: FIRST-LINE ACCURACY")
    print("=" * 80)
    print("Testing if the FIRST LINE's top prediction matches the expected chanda")
    print()

    correct = 0
    total = 0
    mismatches = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Column name is "full  verse" (with two spaces)
            verse = row.get('full  verse', row.get('full verse', '')).strip()
            expected_chanda = row.get('chanda', row.get('chandas', '')).strip()

            if not verse or not expected_chanda:
                continue

            total += 1

            # Test with verse mode = False (line-by-line mode)
            result = chanda.identify_from_text(verse, verse=False)
            predicted = extract_first_line_prediction(result)

            if predicted and meters_match(expected_chanda, predicted):
                correct += 1
            else:
                mismatches.append(
                    {
                        'verse_num': total,
                        'expected': expected_chanda,
                        'predicted': predicted or '(none)',
                        'verse': verse[:100] + '...' if len(verse) > 100 else verse,
                    }
                )

    accuracy = (correct / total * 100) if total > 0 else 0

    print(f"Results: {correct}/{total} correct ({accuracy:.1f}%)")
    print()

    if verbose and mismatches:
        print(f"Mismatches ({len(mismatches)}):")
        print("-" * 80)
        for mm in mismatches[:20]:  # Show first 20
            print(f"\nVerse #{mm['verse_num']}:")
            print(f"  Expected: {mm['expected']}")
            print(f"  Predicted: {mm['predicted']}")
            print(f"  Text: {mm['verse']}")
        if len(mismatches) > 20:
            print(f"\n... and {len(mismatches) - 20} more mismatches")

    return correct, total, accuracy


def test_all_lines_accuracy(chanda, csv_path, verbose=False):
    """
    Test ALL-LINES accuracy: Do ALL lines in each verse match expected?
    This is stricter than first-line accuracy.
    """
    print("=" * 80)
    print("TEST 2: ALL-LINES ACCURACY")
    print("=" * 80)
    print("Testing if ALL LINES in each verse match the expected chanda")
    print()

    correct_verses = 0
    total_verses = 0
    correct_lines = 0
    total_lines = 0
    mismatches = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            verse = row.get('full  verse', row.get('full verse', '')).strip()
            expected_chanda = row.get('chanda', row.get('chandas', '')).strip()

            if not verse or not expected_chanda:
                continue

            total_verses += 1

            # Test with verse mode = False (line-by-line mode)
            result = chanda.identify_from_text(verse, verse=False)
            predictions = extract_all_lines_predictions(result)

            if not predictions:
                mismatches.append(
                    {
                        'verse_num': total_verses,
                        'expected': expected_chanda,
                        'predicted': '(none)',
                        'verse': verse[:100] + '...' if len(verse) > 100 else verse,
                        'line_details': 'No predictions',
                    }
                )
                continue

            # Check if ALL lines match
            verse_correct = True
            line_details = []
            for line_num, pred in predictions:
                total_lines += 1
                if meters_match(expected_chanda, pred):
                    correct_lines += 1
                    line_details.append(f"Line {line_num}: ✓ {pred}")
                else:
                    verse_correct = False
                    line_details.append(f"Line {line_num}: ✗ {pred}")

            if verse_correct:
                correct_verses += 1
            else:
                mismatches.append(
                    {
                        'verse_num': total_verses,
                        'expected': expected_chanda,
                        'predicted': predictions[0][1] if predictions else '(none)',
                        'verse': verse[:100] + '...' if len(verse) > 100 else verse,
                        'line_details': '\n    '.join(line_details),
                    }
                )

    verse_accuracy = (correct_verses / total_verses * 100) if total_verses > 0 else 0
    line_accuracy = (correct_lines / total_lines * 100) if total_lines > 0 else 0

    print(f"Verse-level: {correct_verses}/{total_verses} correct ({verse_accuracy:.1f}%)")
    print(f"Line-level: {correct_lines}/{total_lines} correct ({line_accuracy:.1f}%)")
    print()

    if verbose and mismatches:
        print(f"Mismatches ({len(mismatches)}):")
        print("-" * 80)
        for mm in mismatches[:20]:
            print(f"\nVerse #{mm['verse_num']}:")
            print(f"  Expected: {mm['expected']}")
            print("  Line details:")
            print(f"    {mm['line_details']}")
            print(f"  Text: {mm['verse']}")
        if len(mismatches) > 20:
            print(f"\n... and {len(mismatches) - 20} more mismatches")

    return correct_verses, total_verses, correct_lines, total_lines, verse_accuracy


def test_verse_level_accuracy(chanda, csv_path, verbose=False):
    """
    Test VERSE-LEVEL accuracy: Does holistic verse analysis (verse=True) match?
    This uses the verse-level identification which may consider all lines together.
    """
    print("=" * 80)
    print("TEST 3: VERSE-LEVEL ACCURACY")
    print("=" * 80)
    print("Testing holistic verse identification (verse=True mode)")
    print()

    correct = 0
    total = 0
    mismatches = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            verse = row.get('full  verse', row.get('full verse', '')).strip()
            expected_chanda = row.get('chanda', row.get('chandas', '')).strip()

            if not verse or not expected_chanda:
                continue

            total += 1

            # Test with verse mode = True (holistic verse analysis)
            result = chanda.identify_from_text(verse, verse=True)
            predicted = extract_verse_level_prediction(result)

            if predicted and meters_match(expected_chanda, predicted):
                correct += 1
            else:
                mismatches.append(
                    {
                        'verse_num': total,
                        'expected': expected_chanda,
                        'predicted': predicted or '(none)',
                        'verse': verse[:100] + '...' if len(verse) > 100 else verse,
                    }
                )

    accuracy = (correct / total * 100) if total > 0 else 0

    print(f"Results: {correct}/{total} correct ({accuracy:.1f}%)")
    print()

    if verbose and mismatches:
        print(f"Mismatches ({len(mismatches)}):")
        print("-" * 80)
        for mm in mismatches[:20]:
            print(f"\nVerse #{mm['verse_num']}:")
            print(f"  Expected: {mm['expected']}")
            print(f"  Predicted: {mm['predicted']}")
            print(f"  Text: {mm['verse']}")
        if len(mismatches) > 20:
            print(f"\n... and {len(mismatches) - 20} more mismatches")

    return correct, total, accuracy


def main():
    """Main test execution"""
    parser = argparse.ArgumentParser(description='Test Chanda identifier against match_chandas.csv dataset')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed mismatch information')
    parser.add_argument('--all', action='store_true', help='Run all three accuracy tests')
    parser.add_argument('--verse', action='store_true', help='Run verse-level accuracy test only')
    args = parser.parse_args()

    # Initialize Chanda engine
    print("\n🔧 Initializing Chanda engine...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    data_path = os.path.join(backend_dir, 'data')

    chanda = Chanda(data_path=data_path)
    print(f"✓ Loaded {len(chanda.CHANDA)} total pattern entries")
    print(f"✓ Loaded {len(chanda.VEDIC_METERS)} vedic meter definitions")
    print(f"✓ Loaded {len(chanda.JAATI)} jaati entries")
    print()

    # Dataset path
    csv_path = os.path.join(backend_dir, 'data', 'match_chandas.csv')

    if not os.path.exists(csv_path):
        print(f"❌ ERROR: Dataset not found at {csv_path}")
        return 1

    print(f"📊 Dataset: {csv_path}")
    print()

    # Run tests based on arguments
    if args.verse:
        # Verse-level only
        test_verse_level_accuracy(chanda, csv_path, args.verbose)
    elif args.all:
        # All three tests
        print("\n" + "=" * 80)
        print("COMPREHENSIVE ACCURACY TEST - ALL THREE LEVELS")
        print("=" * 80)
        print()

        c1, t1, a1 = test_first_line_accuracy(chanda, csv_path, args.verbose)
        print()

        cv, tv, cl, tl, a2 = test_all_lines_accuracy(chanda, csv_path, args.verbose)
        print()

        c3, t3, a3 = test_verse_level_accuracy(chanda, csv_path, args.verbose)

        # Final summary
        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        print(f"📊 First-Line Accuracy:  {c1}/{t1} ({a1:.1f}%)")
        print(f"📋 All-Lines Accuracy:   {cv}/{tv} verses ({a2:.1f}%) | {cl}/{tl} lines")
        print(f"🕉️  Verse-Level Accuracy: {c3}/{t3} ({a3:.1f}%)")
        print()

        # Overall assessment
        avg_accuracy = (a1 + a2 + a3) / 3
        if avg_accuracy >= 90:
            status = "✅ EXCELLENT"
        elif avg_accuracy >= 75:
            status = "✓ GOOD"
        elif avg_accuracy >= 60:
            status = "⚠ NEEDS IMPROVEMENT"
        else:
            status = "❌ POOR"

        print(f"Overall Performance: {status} (Average: {avg_accuracy:.1f}%)")
        print()
    else:
        # Default: first-line only (fastest)
        test_first_line_accuracy(chanda, csv_path, args.verbose)

    return 0


if __name__ == '__main__':
    sys.exit(main())
