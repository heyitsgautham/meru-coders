#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test accuracy of chanda.py against matching_chandas.csv dataset

Dataset contains 2,875 Vedic verses with authentic chandas annotations.
Tests the core rule-based model's ability to identify Vedic meters.

Author: SIH 2025 Meru Coders Team
Date: December 7, 2025
"""

from pathlib import Path

import pandas as pd

from backend.config.settings import Settings
from backend.core.chanda import Chanda

settings = Settings()


def normalize_chandas_name(name):
    """
    Normalize chandas names to match our system's format.

    Maps IAST transliteration to Devanagari and handles variations.
    Composite meters are mapped to their base forms.
    """
    # Mapping from dataset format to our system's expected format
    normalization_map = {
        'anuṣṭubh': 'अनुष्टुभ्',
        'triṣṭubh': 'त्रिष्टुभ्',
        'jagatī': 'जगती',
        'bhurik triṣṭubh': 'त्रिष्टुभ्',  # Map composite to base form
        'pathyāpaṅktiḥ': 'पङ्क्ति',  # Map to base form
        # Alternative spellings (if needed)
        'anushtubh': 'अनुष्टुभ्',
        'trishtubh': 'त्रिष्टुभ्',
        'jagati': 'जगती',
        'pathyapankti': 'पङ्क्ति',
    }

    # Normalize to lowercase for matching
    name_lower = name.lower().strip()

    # Return normalized name or original if not in map
    return normalization_map.get(name_lower, name)


def test_verse_accuracy(chanda, verse, expected_chandas, verbose=False):
    """
    Test a single verse and return whether it matches.

    Args:
        chanda: Chanda instance
        verse: Full verse text (may contain multiple lines)
        expected_chandas: Expected chandas name (normalized)
        verbose: Print details

    Returns:
        dict with test results
    """
    result = {
        'verse': verse[:50] + '...' if len(verse) > 50 else verse,
        'expected': expected_chandas,
        'identified': None,
        'match': False,
        'confidence': 0.0,
        'all_matches': [],
    }

    try:
        # Split verse into lines
        lines = [line.strip() for line in verse.split('\n') if line.strip()]

        # For single-line verses, use identify_line
        if len(lines) == 1:
            identification = chanda.identify_line(lines[0])

            if identification and identification.get('found'):
                # Get primary chandas
                primary = identification.get('display_chanda_primary', '')
                result['identified'] = primary

                # Get all matches with confidence scores
                all_chandas = identification.get('display_chanda', '')
                result['all_matches'] = all_chandas

                # Check if expected chandas is in the results
                if expected_chandas in primary or expected_chandas in all_chandas:
                    result['match'] = True
                    result['confidence'] = 10.0  # High confidence for exact match

                # Also check fuzzy matches
                fuzzy = identification.get('fuzzy', [])
                if fuzzy and not result['match']:
                    for fuzzy_match in fuzzy[:3]:  # Check top 3 fuzzy matches
                        fuzzy_name = fuzzy_match[0] if isinstance(fuzzy_match, (list, tuple)) else fuzzy_match
                        if expected_chandas in str(fuzzy_name):
                            result['match'] = True
                            result['confidence'] = fuzzy_match[1] if isinstance(fuzzy_match, (list, tuple)) else 5.0
                            break

        # For multi-line verses, use holistic verse identification
        else:
            verse_result = chanda.identify_verse_holistically(lines)

            if verse_result and verse_result.get('found'):
                meter_name = verse_result.get('meter', '')
                result['identified'] = meter_name
                result['all_matches'] = meter_name

                # Check if expected chandas matches
                if expected_chandas in meter_name:
                    result['match'] = True
                    result['confidence'] = 10.0

        if verbose and not result['match']:
            print("\nMISMATCH:")
            print(f"  Verse: {verse[:80]}...")
            print(f"  Expected: {expected_chandas}")
            print(f"  Identified: {result['identified']}")
            print(f"  All matches: {result['all_matches']}")
            print(f"  Lines: {len(lines)}")

    except Exception as e:
        if verbose:
            print(f"\nERROR processing verse: {verse[:50]}...")
            print(f"  Error: {str(e)}")

    return result


def run_dataset_test(csv_path, sample_size=None, verbose=False):
    """
    Test chanda.py against the matching_chandas.csv dataset.

    Args:
        csv_path: Path to the CSV file
        sample_size: Number of verses to test (None = all)
        verbose: Print detailed results

    Returns:
        dict with accuracy metrics
    """
    print(f"Loading dataset from: {csv_path}")
    df = pd.read_csv(csv_path)

    if sample_size:
        df = df.sample(n=min(sample_size, len(df)), random_state=42)
        print(f"Testing {len(df)} verses (sample)")
    else:
        print(f"Testing all {len(df)} verses")

    # Initialize Chanda
    print("Initializing Chanda engine...")
    chanda = Chanda(data_path=str(settings.DATA_DIR))

    # Normalize chandas names
    df['chandas_normalized'] = df['chandas'].apply(normalize_chandas_name)

    # Test each verse
    results = []
    matches = 0
    total = len(df)

    print("\nProcessing verses...")
    for idx, row in df.iterrows():
        if (idx + 1) % 100 == 0:
            print(f"  Progress: {idx + 1}/{total} ({(idx + 1) / total * 100:.1f}%)")

        result = test_verse_accuracy(chanda, row['full_verse'], row['chandas_normalized'], verbose=verbose)
        results.append(result)

        if result['match']:
            matches += 1

    # Calculate metrics
    accuracy = (matches / total * 100) if total > 0 else 0

    # Chandas-wise accuracy
    chandas_accuracy = {}
    for chandas in df['chandas_normalized'].unique():
        chandas_results = [
            r for r, (_, row) in zip(results, df.iterrows(), strict=False) if row['chandas_normalized'] == chandas
        ]
        chandas_matches = sum(1 for r in chandas_results if r['match'])
        chandas_total = len(chandas_results)
        chandas_accuracy[chandas] = {
            'correct': chandas_matches,
            'total': chandas_total,
            'accuracy': (chandas_matches / chandas_total * 100) if chandas_total > 0 else 0,
        }

    return {
        'total': total,
        'matches': matches,
        'accuracy': accuracy,
        'chandas_accuracy': chandas_accuracy,
        'results': results,
    }


def main():
    """Main test function"""
    import argparse

    parser = argparse.ArgumentParser(description='Test Chanda identification against matching_chandas dataset')
    parser.add_argument('--all', action='store_true', help='Test all verses (default: sample of 100)')
    parser.add_argument('--sample', type=int, default=100, help='Number of verses to sample')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed mismatches')
    args = parser.parse_args()

    # Dataset path
    csv_path = Path(__file__).parent.parent / 'data' / 'matching_chandas.csv'

    if not csv_path.exists():
        print(f"ERROR: Dataset not found at {csv_path}")
        return

    # Run test
    sample_size = None if args.all else args.sample
    metrics = run_dataset_test(csv_path, sample_size=sample_size, verbose=args.verbose)

    # Print results
    print("\n" + "=" * 70)
    print("MATCHING CHANDAS DATASET - TEST RESULTS")
    print("=" * 70)
    print("\nOverall Performance:")
    print(f"  Total Verses: {metrics['total']}")
    print(f"  Correct Matches: {metrics['matches']}")
    print(f"  Accuracy: {metrics['accuracy']:.2f}%")

    print("\nChandas-wise Accuracy:")
    print(f"  {'Chandas':<25} {'Correct':<10} {'Total':<10} {'Accuracy'}")
    print(f"  {'-' * 60}")

    # Sort by total count (descending)
    sorted_chandas = sorted(metrics['chandas_accuracy'].items(), key=lambda x: x[1]['total'], reverse=True)

    for chandas, stats in sorted_chandas:
        print(f"  {chandas:<25} {stats['correct']:<10} {stats['total']:<10} {stats['accuracy']:.1f}%")

    print("\n" + "=" * 70)

    # Success threshold
    if metrics['accuracy'] >= 90:
        print("✅ EXCELLENT ACCURACY - Ready for SIH 2025!")
    elif metrics['accuracy'] >= 80:
        print("✓ GOOD ACCURACY - Minor improvements needed")
    elif metrics['accuracy'] >= 70:
        print("⚠ MODERATE ACCURACY - Optimization required")
    else:
        print("❌ LOW ACCURACY - Major improvements needed")

    print("=" * 70 + "\n")

    return metrics


if __name__ == '__main__':
    main()
