#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Comparison Test Suite

Compares three implementations:
1. chanda.py (current enhanced model)
2. chanda_iitk.py (original IIT-K implementation)
3. enhanced_chanda.py (new implementation with Chandovallari rules)

Uses test data from: page 1-47 chanda list - complete.csv
"""

import csv
import os
from collections import Counter, defaultdict

from backend.evaluation.model_comparison_matching import (
    get_meter_family,
    load_test_data,
    normalize_meter_name,
)
from backend.pipeline.benchmarks import CLASSICAL_BENCHMARK

###############################################################################
# Meter Name Normalization (Enhanced)
###############################################################################


###############################################################################
# Meter Family Classification
###############################################################################


###############################################################################
# Test Data Loading
###############################################################################


###############################################################################
# Model Evaluation
###############################################################################


def evaluate_model(model, test_cases, model_name):
    """Evaluate a model on test cases"""
    results = []

    correct_top1 = 0
    correct_top3 = 0
    correct_family = 0
    total = 0

    _DEBUG = False  # Set to True to debug counting
    if _DEBUG:
        print(f'[DEBUG] Starting {model_name} with {len(test_cases)} cases, total={total}')

    for idx, test_case in enumerate(test_cases):
        shloka = test_case['shloka']
        expected = test_case['expected']
        expected_normalized = test_case['expected_normalized']
        expected_family = test_case['expected_family']

        try:
            # Try identify_from_text for multi-line verses
            if '\n' in shloka or len(shloka) > 100:
                result = model.identify_from_text(shloka)
                if 'results' in result and result['results']:
                    line_result = result['results'][0].get('result', {})
                elif 'result' in result and result['result'].get('line'):
                    line_result = result['result']['line'][0].get('result', {})
                else:
                    line_result = {}
            else:
                line_result = model.identify_line(shloka, fuzzy=True)

            # Extract predictions
            predictions = []

            # Try to get from 'results' list
            if 'results' in line_result and line_result['results']:
                for r in line_result['results'][:5]:
                    name = r.get('name', '')
                    conf = r.get('confidence', 0)
                    predictions.append((name, conf))

            # Fall back to 'chanda' list
            elif 'chanda' in line_result and line_result['chanda']:
                for c in line_result['chanda'][:5]:
                    if isinstance(c, tuple):
                        name = c[0]
                    else:
                        name = c
                    predictions.append((name, 10.0))

            # Fall back to display_chanda
            elif 'display_chanda' in line_result and line_result['display_chanda']:
                display = line_result['display_chanda']
                for part in display.split('/'):
                    name = part.strip().split('(')[0].strip()
                    predictions.append((name, 5.0))

            # Check accuracy
            top1_match = False
            top3_match = False
            family_match = False

            if predictions:
                # Top-1 accuracy
                pred_normalized = normalize_meter_name(predictions[0][0])
                top1_match = pred_normalized == expected_normalized

                # Top-3 accuracy
                for pred, _conf in predictions[:3]:
                    pred_normalized = normalize_meter_name(pred)
                    if pred_normalized == expected_normalized:
                        top3_match = True
                        break

                # Family-level accuracy
                for pred, _conf in predictions[:5]:
                    pred_family = get_meter_family(pred)
                    if pred_family == expected_family:
                        family_match = True
                        break

            if top1_match:
                correct_top1 += 1
            if top3_match:
                correct_top3 += 1
            if family_match:
                correct_family += 1

            if _DEBUG:
                print(f'[DEBUG] idx={idx}, total BEFORE increment={total}')
            total += 1
            if _DEBUG:
                print(f'[DEBUG] idx={idx}, total AFTER increment={total}')

            # Get lg pattern safely (may be list or string)
            lg_pattern = line_result.get('lg', '')
            if isinstance(lg_pattern, list):
                lg_pattern = ''.join(lg_pattern)

            results.append(
                {
                    'index': idx + 1,
                    'shloka': shloka[:60] + '...' if len(shloka) > 60 else shloka,
                    'expected': expected,
                    'expected_normalized': expected_normalized,
                    'predictions': predictions[:3],
                    'top1_match': top1_match,
                    'top3_match': top3_match,
                    'family_match': family_match,
                    'lg_pattern': lg_pattern,
                    'syllables': len(lg_pattern.replace(' ', '')),
                }
            )
            if _DEBUG:
                print(f'[DEBUG] idx={idx}, total at end of try={total}')

        except Exception as e:
            if _DEBUG:
                print(f'[DEBUG] idx={idx}, EXCEPTION: {e}, total BEFORE={total}')
            results.append(
                {
                    'index': idx + 1,
                    'shloka': shloka[:60] + '...' if len(shloka) > 60 else shloka,
                    'expected': expected,
                    'expected_normalized': expected_normalized,
                    'predictions': [],
                    'top1_match': False,
                    'top3_match': False,
                    'family_match': False,
                    'error': str(e),
                }
            )
            total += 1

    # Calculate metrics
    metrics = {
        'model_name': model_name,
        'total': total,
        'correct_top1': correct_top1,
        'correct_top3': correct_top3,
        'correct_family': correct_family,
        'accuracy_top1': correct_top1 / total if total > 0 else 0,
        'accuracy_top3': correct_top3 / total if total > 0 else 0,
        'accuracy_family': correct_family / total if total > 0 else 0,
    }

    return metrics, results


###############################################################################
# Confusion Matrix Generation
###############################################################################


def generate_confusion_matrix(results):
    """Generate confusion matrix from results"""
    confusion = defaultdict(Counter)

    for result in results:
        expected = result['expected_normalized']
        if result['predictions']:
            predicted = normalize_meter_name(result['predictions'][0][0])
        else:
            predicted = 'ERROR'

        confusion[expected][predicted] += 1

    return confusion


def print_confusion_matrix(confusion, title):
    """Print confusion matrix"""
    print(f"\n{'=' * 80}")
    print(f"CONFUSION MATRIX: {title}")
    print('=' * 80)

    # Get all labels
    all_labels = set(confusion.keys())
    for predictions in confusion.values():
        all_labels.update(predictions.keys())
    all_labels = sorted(all_labels)

    # Print header
    print(f"{'Expected':<20}", end='')
    for label in all_labels[:10]:  # Limit to 10 columns
        print(f"{label[:8]:<10}", end='')
    print()
    print('-' * 120)

    # Print rows
    for expected in sorted(confusion.keys()):
        print(f"{expected:<20}", end='')
        for predicted in all_labels[:10]:
            count = confusion[expected].get(predicted, 0)
            print(f"{count:<10}", end='')
        print()


###############################################################################
# Main Comparison
###############################################################################


def main():
    print("=" * 80)
    print("COMPREHENSIVE CHANDA MODEL COMPARISON")
    print("=" * 80)

    # Load test data
    test_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', CLASSICAL_BENCHMARK)

    if not os.path.exists(test_data_path):
        print(f"ERROR: Test data not found at {test_data_path}")
        return

    test_cases = load_test_data(test_data_path)
    print(f"\nLoaded {len(test_cases)} test cases")

    # Show distribution of expected meters
    meter_dist = Counter(tc['expected_normalized'] for tc in test_cases)
    print("\nMeter distribution (top 10):")
    for meter, count in meter_dist.most_common(10):
        print(f"  {meter}: {count}")

    data_path = os.path.join(os.path.dirname(__file__), '..', 'data')

    # Initialize models
    models = {}

    # Model 1: Current enhanced chanda.py
    try:
        from backend.core.chanda import Chanda

        models['chanda.py'] = Chanda(data_path)
        print("\n✓ Loaded chanda.py (current model)")
    except Exception as e:
        print(f"\n✗ Failed to load chanda.py: {e}")

    # Model 2: Original IIT-K implementation
    try:
        # Import from reference folder
        from reference.alternative_implementations.chanda_iitk import Chanda as ChandaIITK

        models['chanda_iitk.py'] = ChandaIITK(data_path)
        print("✓ Loaded chanda_iitk.py (original IIT-K)")
    except Exception as e:
        print(f"✗ Failed to load chanda_iitk.py: {e}")

    # Model 3: Enhanced implementation with Chandovallari rules
    try:
        from backend.experimental.enhanced_chanda import EnhancedChanda

        models['enhanced_chanda.py'] = EnhancedChanda(data_path)
        print("✓ Loaded enhanced_chanda.py (Chandovallari rules)")
    except Exception as e:
        print(f"✗ Failed to load enhanced_chanda.py: {e}")

    if not models:
        print("\nERROR: No models could be loaded!")
        return

    # Evaluate each model
    all_metrics = []
    all_results = {}

    for model_name, model in models.items():
        print(f"\n{'=' * 80}")
        print(f"EVALUATING: {model_name}")
        print('=' * 80)

        metrics, results = evaluate_model(model, test_cases, model_name)
        all_metrics.append(metrics)
        all_results[model_name] = results

        print(f"\nResults for {model_name}:")
        print(f"  Total test cases: {metrics['total']}")
        print(
            f"  Top-1 Accuracy:   {metrics['accuracy_top1'] * 100:.1f}% ({metrics['correct_top1']}/{metrics['total']})"
        )
        print(
            f"  Top-3 Accuracy:   {metrics['accuracy_top3'] * 100:.1f}% ({metrics['correct_top3']}/{metrics['total']})"
        )
        print(
            f"  Family Accuracy:  {metrics['accuracy_family'] * 100:.1f}% ({metrics['correct_family']}/{metrics['total']})"
        )

        # Show some failures
        failures = [r for r in results if not r['top1_match']][:5]
        if failures:
            print("\nSample failures (first 5):")
            for f in failures:
                pred = f['predictions'][0][0] if f['predictions'] else 'None'
                print(f"  Expected: {f['expected_normalized']}, Got: {normalize_meter_name(pred)}")

    # Comparison Summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    print(f"\n{'Model':<25} {'Top-1':<12} {'Top-3':<12} {'Family':<12}")
    print("-" * 60)
    for m in all_metrics:
        print(
            f"{m['model_name']:<25} {m['accuracy_top1'] * 100:>5.1f}%      {m['accuracy_top3'] * 100:>5.1f}%      {m['accuracy_family'] * 100:>5.1f}%"
        )

    # Generate confusion matrices
    for model_name, results in all_results.items():
        confusion = generate_confusion_matrix(results)
        print_confusion_matrix(confusion, model_name)

    # Per-meter breakdown for best model
    best_model = max(all_metrics, key=lambda x: x['accuracy_top1'])
    print(f"\n{'=' * 80}")
    print(f"PER-METER BREAKDOWN: {best_model['model_name']}")
    print("=" * 80)

    best_results = all_results[best_model['model_name']]
    meter_accuracy = defaultdict(lambda: {'correct': 0, 'total': 0})

    for r in best_results:
        meter = r['expected_normalized']
        meter_accuracy[meter]['total'] += 1
        if r['top1_match']:
            meter_accuracy[meter]['correct'] += 1

    print(f"\n{'Meter':<25} {'Correct':<10} {'Total':<10} {'Accuracy':<10}")
    print("-" * 60)
    for meter in sorted(meter_accuracy.keys()):
        data = meter_accuracy[meter]
        acc = data['correct'] / data['total'] if data['total'] > 0 else 0
        print(f"{meter:<25} {data['correct']:<10} {data['total']:<10} {acc * 100:>5.1f}%")

    # Save detailed results to CSV
    output_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'comparison_results.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                'Model',
                'Index',
                'Shloka',
                'Expected',
                'Predicted',
                'Confidence',
                'Top1_Match',
                'Top3_Match',
                'Family_Match',
                'Syllables',
            ]
        )

        for model_name, results in all_results.items():
            for r in results:
                pred = r['predictions'][0] if r['predictions'] else ('', 0)
                writer.writerow(
                    [
                        model_name,
                        r['index'],
                        r['shloka'][:50],
                        r['expected'],
                        pred[0],
                        f"{pred[1]:.2f}" if isinstance(pred[1], float) else pred[1],
                        r['top1_match'],
                        r['top3_match'],
                        r['family_match'],
                        r.get('syllables', ''),
                    ]
                )

    print(f"\nDetailed results saved to: {output_path}")

    return all_metrics, all_results


if __name__ == '__main__':
    main()
