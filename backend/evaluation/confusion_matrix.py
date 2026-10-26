#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confusion Matrix Evaluation for Chandojñānam Model

This script evaluates the meter identification model against the
classical benchmark list, "page 1-47 chanda list - complete.csv", of 264 shlokas
with labeled chandas. It generates:
1. Overall accuracy metrics (Top-1 and Top-3)
2. Per-meter precision, recall, and F1 scores
3. Confusion matrix visualization
4. Detailed error analysis

@author: Chandojñānam Enhancement Project
@date: November 2025
"""

import csv
import os
import re
import sys
from collections import Counter

from backend.core.chanda import Chanda
from backend.evaluation.confusion_matrix_matching import (
    extract_top_meter,
    is_family_match,
    normalize_meter_name,
)
from backend.evaluation.confusion_matrix_report import (
    build_confusion_matrix,
    plot_confusion_matrix,
    print_confusion_matrix,
    print_results,
    save_confusion_matrix_csv,
    save_results_csv,
)
from backend.pipeline.benchmarks import CLASSICAL_BENCHMARK

# Initialize Chanda
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data')
chanda = Chanda(DATA_PATH)

###############################################################################
# METER NAME NORMALIZATION
###############################################################################


###############################################################################
# DATA LOADING
###############################################################################


def load_test_data(csv_path):
    """
    Load test data from CSV file.
    Handles multi-line verses and filters out empty entries.

    Returns list of dicts: [{text, expected_chanda, lg_pattern, gana}, ...]
    """
    test_cases = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Skip header rows (first 2 rows are headers)
    data_rows = rows[2:]

    for row in data_rows:
        if len(row) < 4:
            continue

        shloka = row[0].strip() if row[0] else ''
        lg_pattern = row[1].strip() if len(row) > 1 and row[1] else ''
        gana = row[2].strip() if len(row) > 2 and row[2] else ''
        expected_chanda = row[3].strip() if len(row) > 3 and row[3] else ''

        # Skip if no text or no expected chanda
        if not shloka or not expected_chanda:
            continue

        # Clean up the shloka text
        # Remove verse markers and extra whitespace
        shloka = re.sub(r'\s+', ' ', shloka)
        shloka = shloka.strip('" ')

        test_cases.append({'text': shloka, 'expected_chanda': expected_chanda, 'lg_pattern': lg_pattern, 'gana': gana})

    return test_cases


###############################################################################
# EVALUATION
###############################################################################


def evaluate_model(test_cases, verbose=False):
    """
    Run evaluation on all test cases.
    Returns detailed results and summary statistics.
    """
    results = []

    # Counters for metrics
    top1_correct = 0
    top3_correct = 0
    total = 0

    # Per-meter tracking
    true_positives = Counter()  # Correctly predicted
    false_positives = Counter()  # Predicted but wrong
    false_negatives = Counter()  # Should have predicted but didn't

    # Confusion matrix data
    confusion_data = []  # (expected, predicted) pairs

    print("=" * 80)
    print("CHANDOJÑĀNAM MODEL EVALUATION")
    print("=" * 80)
    print(f"Total test cases: {len(test_cases)}")
    print()

    for idx, case in enumerate(test_cases, 1):
        text = case['text']
        expected = case['expected_chanda']
        expected_norm = normalize_meter_name(expected)

        # Run identification
        try:
            # Check if multi-line verse (contains newlines or verse markers)
            is_multiline = '\n' in text or '।' in text or len(text) > 100

            if is_multiline:
                # Use identify_from_text for multi-line verses
                full_result = chanda.identify_from_text(text, verse=True, fuzzy=True)

                if full_result and full_result.get('result', {}).get('verse'):
                    verse_result = full_result['result']['verse'][0]
                    chanda_tuple = verse_result.get('chanda', ([], 0))

                    if chanda_tuple and chanda_tuple[0]:
                        top_meter = chanda_tuple[0][0]  # First match name
                        confidence = chanda_tuple[1]  # Score
                        predicted = top_meter
                        predicted_norm = normalize_meter_name(predicted) if predicted else ''

                        # Check match rank
                        match_rank = 0
                        for rank, meter_name in enumerate(chanda_tuple[0][:5], 1):
                            if normalize_meter_name(meter_name) == expected_norm:
                                match_rank = rank
                                break
                    else:
                        top_meter = None
                        confidence = 0.0
                        match_rank = 0
                        predicted = 'NOT_FOUND'
                        predicted_norm = 'not_found'
                else:
                    top_meter = None
                    confidence = 0.0
                    match_rank = 0
                    predicted = 'NOT_FOUND'
                    predicted_norm = 'not_found'
            else:
                # Use identify_line for single line
                result = chanda.identify_line(text, fuzzy=True)

                if result and result.get('found'):
                    top_meter, confidence, match_rank = extract_top_meter(result, expected)
                    predicted = top_meter
                    predicted_norm = normalize_meter_name(predicted) if predicted else ''
                else:
                    top_meter = None
                    confidence = 0.0
                    match_rank = 0
                    predicted = 'NOT_FOUND'
                    predicted_norm = 'not_found'

        except Exception as e:
            if verbose:
                print(f"Error processing verse {idx}: {e}")
                import traceback

                traceback.print_exc()
            predicted = 'ERROR'
            predicted_norm = 'error'
            confidence = 0.0
            match_rank = 0
            result = None

        # Record result
        is_top1_match = match_rank == 1
        is_top3_match = match_rank in [1, 2, 3]
        is_family_match_flag = is_family_match(expected_norm, predicted_norm)

        total += 1
        if is_top1_match:
            top1_correct += 1
            true_positives[expected_norm] += 1
        else:
            false_negatives[expected_norm] += 1
            if predicted_norm and predicted_norm != 'not_found':
                false_positives[predicted_norm] += 1

        if is_top3_match:
            top3_correct += 1

        # Record for confusion matrix
        confusion_data.append((expected_norm, predicted_norm))

        results.append(
            {
                'idx': idx,
                'text': text[:60] + '...' if len(text) > 60 else text,
                'expected': expected,
                'expected_norm': expected_norm,
                'predicted': predicted,
                'predicted_norm': predicted_norm,
                'confidence': confidence,
                'match_rank': match_rank,
                'is_top1': is_top1_match,
                'is_top3': is_top3_match,
                'is_family_match': is_family_match_flag,
            }
        )

        # Progress indicator
        if idx % 20 == 0:
            print(f"Processed {idx}/{len(test_cases)} verses...")

    # Calculate metrics
    top1_accuracy = (top1_correct / total * 100) if total > 0 else 0
    top3_accuracy = (top3_correct / total * 100) if total > 0 else 0

    # Calculate family-level accuracy (lenient matching)
    family_correct = sum(1 for r in results if r['is_top1'] or r['is_family_match'])
    family_accuracy = (family_correct / total * 100) if total > 0 else 0

    # Per-meter precision/recall
    meter_metrics = {}
    all_meters = set(true_positives.keys()) | set(false_positives.keys()) | set(false_negatives.keys())

    for meter in all_meters:
        tp = true_positives[meter]
        fp = false_positives[meter]
        fn = false_negatives[meter]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        support = tp + fn  # Total actual instances

        meter_metrics[meter] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support,
            'tp': tp,
            'fp': fp,
            'fn': fn,
        }

    summary = {
        'total': total,
        'top1_correct': top1_correct,
        'top3_correct': top3_correct,
        'family_correct': family_correct,
        'top1_accuracy': top1_accuracy,
        'top3_accuracy': top3_accuracy,
        'family_accuracy': family_accuracy,
        'meter_metrics': meter_metrics,
        'confusion_data': confusion_data,
    }

    return results, summary


###############################################################################
# MAIN
###############################################################################


def main():
    """Main evaluation function."""

    # Path to test data
    test_csv = os.path.join(DATA_PATH, CLASSICAL_BENCHMARK)

    if not os.path.exists(test_csv):
        print(f"❌ Test data not found: {test_csv}")
        return 1

    # Load test data
    print("Loading test data...")
    test_cases = load_test_data(test_csv)
    print(f"Loaded {len(test_cases)} test cases with labeled chandas")

    # Get unique meters in test data
    unique_meters = set(normalize_meter_name(tc['expected_chanda']) for tc in test_cases)
    print(f"Unique meters in test data: {len(unique_meters)}")

    # Show meter distribution
    meter_dist = Counter(normalize_meter_name(tc['expected_chanda']) for tc in test_cases)
    print("\nMeter distribution (top 10):")
    for meter, count in meter_dist.most_common(10):
        print(f"  {meter}: {count} examples")

    # Run evaluation
    print("\n" + "=" * 80)
    print("RUNNING EVALUATION...")
    print("=" * 80)

    results, summary = evaluate_model(test_cases, verbose=False)

    # Print results
    print_results(results, summary, show_errors=True)

    # Build and print confusion matrix
    matrix, labels = build_confusion_matrix(summary['confusion_data'])
    print_confusion_matrix(matrix, labels)

    # Save results
    output_dir = os.path.join(DATA_PATH, '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    results_csv = os.path.join(output_dir, 'evaluation_results.csv')
    save_results_csv(results, summary, results_csv)

    confusion_csv = os.path.join(output_dir, 'confusion_matrix.csv')
    save_confusion_matrix_csv(matrix, labels, confusion_csv)

    # Generate visual plot
    confusion_plot = os.path.join(output_dir, 'confusion_matrix.png')
    plot_confusion_matrix(matrix, labels, confusion_plot)

    # Final verdict
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)

    if summary['top1_accuracy'] >= 90:
        print("🎉 EXCELLENT! Top-1 exact accuracy ≥90%")
    elif summary['top1_accuracy'] >= 75:
        print("✓ GOOD! Top-1 exact accuracy ≥75%")
    elif summary['top1_accuracy'] >= 50:
        print("⚠ MODERATE: Top-1 exact accuracy 50-75%")
    else:
        print("⚠ NEEDS IMPROVEMENT: Top-1 exact accuracy <50%")

    if summary['family_accuracy'] >= 75:
        print("✓ GOOD family-level recognition (≥75%)")

    print("\nFinal Scores:")
    print(f"  Top-1 Exact Match:  {summary['top1_accuracy']:.1f}%")
    print(f"  Top-3 Exact Match:  {summary['top3_accuracy']:.1f}%")
    print(f"  Family-Level Match: {summary['family_accuracy']:.1f}%")

    return 0


if __name__ == '__main__':
    sys.exit(main())
