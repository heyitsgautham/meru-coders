#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Vedic accuracy using ChandaModal with VEDIC mode on COMPLETE verses only.
"""

import importlib.util
import os

from backend.core.chanda_modal import ChandaModal

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Direct import to avoid ultralytics conflict
spec = importlib.util.spec_from_file_location(
    "rigveda_complete", os.path.join(backend_dir, "tests", "data", "rigveda_complete.py")
)
rigveda_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rigveda_module)
RIGVEDA_COMPLETE = rigveda_module.RIGVEDA_COMPLETE


def normalize_meter(name):
    """Normalize meter names for comparison."""
    if not name:
        return ''
    name = name.lower().strip()

    # Remove parenthetical prefixes like "(1-7)"
    if name.startswith('('):
        import re

        name = re.sub(r'^\([^)]+\)', '', name).strip()

    mapping = {
        'gāyatrī': 'gāyatrī',
        'gayatri': 'gāyatrī',
        'गायत्री': 'gāyatrī',
        'triṣṭup': 'triṣṭup',
        'trishtup': 'triṣṭup',
        'त्रिष्टुभ्': 'triṣṭup',
        'jagatī': 'jagatī',
        'jagati': 'jagatī',
        'जगती': 'jagatī',
        'anuṣṭup': 'anuṣṭup',
        'anushtup': 'anuṣṭup',
        'अनुष्टुभ्': 'anuṣṭup',
        'bṛhatī': 'bṛhatī',
        'brhati': 'bṛhatī',
        'बृहती': 'bṛhatī',
        'uṣṇik': 'uṣṇik',
        'ushnik': 'uṣṇik',
        'उष्णिक्': 'uṣṇik',
        'paṅkti': 'paṅkti',
        'pankti': 'paṅkti',
        'पङ्क्ति': 'paṅkti',
    }
    return mapping.get(name, name)


def main():
    # Initialize
    data_path = os.path.join(backend_dir, 'data')
    chanda = ChandaModal(data_path)

    # Filter to only standard Vedic meters
    standard_meters = {'gāyatrī', 'triṣṭup', 'jagatī', 'anuṣṭup', 'bṛhatī', 'uṣṇik', 'paṅkti'}

    # Test
    correct = 0
    total = 0
    by_meter = {}

    print('=' * 70)
    print('   VEDIC MODE ACCURACY TEST - COMPLETE VERSES ONLY')
    print('   Using ChandaModal with mode="vedic"')
    print('=' * 70)
    print()

    for i, verse in enumerate(RIGVEDA_COMPLETE):
        expected_raw = verse.get('meter', '')
        expected = normalize_meter(expected_raw)

        # Skip non-standard meters
        if expected not in standard_meters:
            print(f"SKIP [{i + 1:3d}] Non-standard meter: {expected_raw}")
            continue

        text = verse['text']
        total += 1

        # Use VEDIC mode
        result = chanda.identify_modal(text, mode='vedic')

        predicted_raw = result.get('meter', '')
        predicted = normalize_meter(predicted_raw)
        syl_count = result.get('syllable_count', 0)
        expected_syl = result.get('expected_syllables', '?')
        confidence = result.get('confidence', 0)

        # Track by expected meter
        if expected not in by_meter:
            by_meter[expected] = {'correct': 0, 'total': 0}
        by_meter[expected]['total'] += 1

        is_correct = predicted == expected
        if is_correct:
            correct += 1
            by_meter[expected]['correct'] += 1
            status = '✓'
        else:
            status = '✗'

        # Print all results for this small dataset
        print(
            f'{status} [{i + 1:3d}] {verse["ref"]:10s} Expected: {expected:10s} | Got: {predicted:10s} (syl: {syl_count}, exp: {expected_syl}, conf: {confidence:.2f})'
        )

    print()
    print('=' * 70)
    print(f'   OVERALL ACCURACY (VEDIC MODE, COMPLETE VERSES): {correct}/{total} ({100 * correct / total:.1f}%)')
    print('=' * 70)
    print()
    print('BY METER:')
    for meter, stats in sorted(by_meter.items()):
        if stats['total'] > 0:
            acc = 100 * stats['correct'] / stats['total']
            emoji = '✓' if acc >= 70 else '⚠️' if acc >= 40 else '❌'
            print(f'  {emoji} {meter:15s}: {stats["correct"]:3d}/{stats["total"]:3d} ({acc:5.1f}%)')

    # Verdict
    print()
    if total > 0:
        accuracy = correct / total
        if accuracy >= 0.9:
            print('✅ EXCELLENT: Vedic mode working very well on complete verses!')
        elif accuracy >= 0.7:
            print('⚠️ GOOD: Vedic mode reasonable on complete verses')
        elif accuracy >= 0.5:
            print('⚠️ FAIR: Vedic mode partially working')
        else:
            print('❌ POOR: Vedic mode needs improvement')


if __name__ == '__main__':
    main()
