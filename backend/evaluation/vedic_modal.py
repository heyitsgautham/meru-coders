#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Vedic accuracy using ChandaModal with VEDIC mode.
"""

import importlib.util
import os

from backend.core.chanda_modal import ChandaModal

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Direct import to avoid ultralytics conflict
spec = importlib.util.spec_from_file_location(
    "rigveda_authentic", os.path.join(backend_dir, "evaluation", "data", "rigveda_authentic.py")
)
rigveda_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rigveda_module)
RIGVEDA_VERSES = rigveda_module.RIGVEDA_AUTHENTIC


def normalize_meter(name):
    """Normalize meter names for comparison."""
    if not name:
        return ''
    name = name.lower().strip()
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
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    chanda = ChandaModal(data_path)

    # Test
    correct = 0
    total = len(RIGVEDA_VERSES)
    by_meter = {}
    failures = []

    print('=' * 70)
    print('   VEDIC MODE ACCURACY TEST')
    print('   Using ChandaModal with mode="vedic"')
    print('=' * 70)
    print()

    for i, verse in enumerate(RIGVEDA_VERSES):
        text = verse['text']
        expected = normalize_meter(verse['meter'])

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
            failures.append(
                {
                    'index': i + 1,
                    'expected': expected,
                    'predicted': predicted,
                    'syl_count': syl_count,
                    'expected_syl': expected_syl,
                    'confidence': confidence,
                    'text': text[:60] + '...' if len(text) > 60 else text,
                }
            )

        # Print first 15
        if i < 15:
            print(
                f'{status} [{i + 1:3d}] Expected: {expected:10s} | Got: {predicted:10s} (syl: {syl_count}, conf: {confidence:.2f})'
            )

    print()
    print('=' * 70)
    print(f'   OVERALL ACCURACY (VEDIC MODE): {correct}/{total} ({100 * correct / total:.1f}%)')
    print('=' * 70)
    print()
    print('BY METER:')
    for meter, stats in sorted(by_meter.items()):
        acc = 100 * stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        emoji = '✓' if acc >= 70 else '⚠️' if acc >= 40 else '❌'
        print(f'  {emoji} {meter:15s}: {stats["correct"]:3d}/{stats["total"]:3d} ({acc:5.1f}%)')

    # Show some failures
    print()
    print('-' * 70)
    print('SAMPLE FAILURES (first 20):')
    print('-' * 70)
    for f in failures[:20]:
        print(
            f"  [{f['index']:3d}] Expected: {f['expected']:10s} -> Got: {f['predicted']:10s} (syl: {f['syl_count']}, exp_syl: {f['expected_syl']})"
        )

    # Verdict
    print()
    if correct / total >= 0.9:
        print('✅ EXCELLENT: Vedic mode working well!')
    elif correct / total >= 0.7:
        print('⚠️ GOOD: Vedic mode reasonable but needs improvement')
    elif correct / total >= 0.5:
        print('⚠️ FAIR: Vedic mode partially working')
    else:
        print('❌ POOR: Vedic mode needs significant work')


if __name__ == '__main__':
    main()
