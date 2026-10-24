#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRUE VEDIC ACCURACY TEST

This test validates our Chanda identifier against Rigveda verses
with ground truth meters from the WSC2023 Anukramani.

Unlike previous tests that only checked COVERAGE (do we have the meter name?),
this test checks PREDICTION ACCURACY (does our model correctly identify the meter?).

Usage:
    cd backend && python tests/test_true_vedic_accuracy.py
"""

import os
import sys

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Import AUTHENTIC test data (merged from Rigveda_api + WSC2023 Anukramani)
import importlib.util

from core.chanda import Chanda

spec = importlib.util.spec_from_file_location(
    "rigveda_authentic",
    os.path.join(backend_dir, "tests", "data", "rigveda_authentic.py")
)
rigveda_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rigveda_module)
RIGVEDA_VERSES = rigveda_module.RIGVEDA_AUTHENTIC

def get_all_meters():
    """Get all unique meters in the dataset."""
    meters = {}
    for v in RIGVEDA_VERSES:
        key = v['meter_iast']
        if key not in meters:
            meters[key] = {'name': v['meter'], 'iast': v['meter_iast'], 'syllables': v['syllables'], 'count': 0}
        meters[key]['count'] += 1
    return meters


def normalize_meter_name(name):
    """Normalize meter name for comparison."""
    if not name:
        return ""
    name = str(name).lower().strip()
    # Remove common suffixes and normalize variants
    replacements = {
        'ī': 'i',
        'ū': 'u',
        'ā': 'a',
        'ṭ': 't',
        'ṣ': 's',
        'ṅ': 'n',
        'ñ': 'n',
        'ḥ': 'h',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name


def meter_matches(predicted, expected_devanagari, expected_iast):
    """Check if predicted meter matches expected."""
    pred_norm = normalize_meter_name(predicted)
    exp_dev_norm = normalize_meter_name(expected_devanagari)
    exp_iast_norm = normalize_meter_name(expected_iast)

    # Direct match
    if exp_dev_norm in pred_norm or exp_iast_norm in pred_norm:
        return True

    # Check common variants
    variants = {
        'gayatri': ['gayatri', 'गायत्री', 'gāyatrī'],
        'anustubh': ['anustubh', 'anustup', 'अनुष्टुभ्', 'anuṣṭubh', 'anuṣṭup'],
        'tristubh': ['tristubh', 'tristup', 'त्रिष्टुभ्', 'triṣṭubh', 'triṣṭup'],
        'jagati': ['jagati', 'jagatii', 'जगती', 'jagatī'],
        'brhati': ['brhati', 'brihati', 'बृहती', 'bṛhatī'],
        'pankti': ['pankti', 'panktih', 'पङ्क्ति', 'paṅkti'],
        'usnik': ['usnik', 'usnih', 'उष्णिक्', 'uṣṇik'],
    }

    for canonical, vars in variants.items():
        if any(v in pred_norm for v in [normalize_meter_name(x) for x in vars]):
            if any(v in exp_iast_norm for v in [normalize_meter_name(x) for x in vars]):
                return True

    return False


def run_vedic_accuracy_test():
    """Run the true Vedic accuracy test."""
    print("\n" + "=" * 70)
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           TRUE VEDIC ACCURACY TEST (Rigveda + Anukramani)            ║")
    print("║                                                                      ║")
    print("║  Testing prediction accuracy, NOT just coverage!                     ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print("=" * 70)

    # Initialize Chanda
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data')
    chanda = Chanda(data_path)

    # Results tracking
    results = {
        'total': 0,
        'correct': 0,
        'by_meter': {},
        'failures': []
    }

    # Test each verse
    print("\n" + "-" * 70)
    print("TESTING INDIVIDUAL VERSES")
    print("-" * 70)

    for verse_info in RIGVEDA_VERSES:
        text = verse_info['text']
        expected_meter = verse_info['meter']
        expected_iast = verse_info['meter_iast']
        expected_syllables = verse_info['syllables']
        source = verse_info['source']

        # Initialize meter tracking
        if expected_iast not in results['by_meter']:
            results['by_meter'][expected_iast] = {'total': 0, 'correct': 0}

        results['total'] += 1
        results['by_meter'][expected_iast]['total'] += 1

        # Identify the verse
        result = chanda.identify_line(text)

        predicted = result.get('display_chanda_primary', 'Unknown')
        actual_syllables = len(result.get('lg', []))

        # Check if prediction matches expected
        is_correct = meter_matches(predicted, expected_meter, expected_iast)

        if is_correct:
            results['correct'] += 1
            results['by_meter'][expected_iast]['correct'] += 1
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            results['failures'].append({
                'source': source,
                'text': text[:60] + '...' if len(text) > 60 else text,
                'expected': f"{expected_meter} ({expected_iast})",
                'predicted': predicted,
                'expected_syllables': expected_syllables,
                'actual_syllables': actual_syllables
            })

        print(f"\n  {status}: {source}")
        print(f"    Expected: {expected_meter} ({expected_syllables} syllables)")
        print(f"    Predicted: {predicted} ({actual_syllables} syllables)")

    # Print Summary
    print("\n" + "=" * 70)
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                           TEST RESULTS                               ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print("=" * 70)

    overall_accuracy = (results['correct'] / results['total'] * 100) if results['total'] > 0 else 0

    print(f"\n  OVERALL ACCURACY: {results['correct']}/{results['total']} ({overall_accuracy:.1f}%)")

    print("\n  BY METER:")
    print(f"  {'─' * 50}")

    for meter_iast, stats in sorted(results['by_meter'].items(), key=lambda x: x[0]):
        meter_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        status_icon = "✅" if stats['correct'] == stats['total'] else "⚠️" if stats['correct'] > 0 else "❌"
        print(f"  {status_icon} {meter_iast:15}: {stats['correct']}/{stats['total']} ({meter_acc:.0f}%)")

    if results['failures']:
        print(f"\n  FAILURES ({len(results['failures'])}):")
        print(f"  {'─' * 50}")
        for f in results['failures'][:10]:  # Show first 10 failures
            print(f"\n    Source: {f['source']}")
            print(f"    Expected: {f['expected']} ({f['expected_syllables']} syllables)")
            print(f"    Predicted: {f['predicted']} ({f['actual_syllables']} syllables)")

    print("\n" + "=" * 70)

    # Verdict
    if overall_accuracy >= 90:
        print("🎉 EXCELLENT! Ready for SIH 2025 Grand Finale!")
    elif overall_accuracy >= 70:
        print("✅ GOOD! Minor improvements needed.")
    elif overall_accuracy >= 50:
        print("⚠️  MODERATE: Significant improvements needed.")
    else:
        print("❌ POOR: Major issues with Vedic meter identification.")

    print("=" * 70 + "\n")

    return results


if __name__ == '__main__':
    results = run_vedic_accuracy_test()

    # Exit with appropriate code
    accuracy = (results['correct'] / results['total'] * 100) if results['total'] > 0 else 0
    sys.exit(0 if accuracy >= 70 else 1)
