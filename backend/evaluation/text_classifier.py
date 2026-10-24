#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the Text Classifier accuracy on Rigveda and Classical CSV datasets.

This measures how well the classifier can distinguish Vedic from Classical texts
before even running meter identification.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from core.text_classifier import TextClassifier, classify_text


def test_on_rigveda(classifier, limit=1000):
    """Test classifier on Rigveda dataset - should all be 'vedic'"""
    filepath = os.path.join(settings.DATA_DIR, 'rigveda_with_meters_complete.csv')

    correct = 0
    incorrect = 0
    total = 0
    misclassified = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            verse = row.get('verse_text', '').strip()
            if not verse:
                continue

            total += 1
            classification, confidence = classify_text(verse)

            if classification == 'vedic':
                correct += 1
            else:
                incorrect += 1
                if len(misclassified) < 20:
                    misclassified.append({
                        'text': verse[:60],
                        'classified_as': classification,
                        'confidence': confidence,
                    })

            if limit and total >= limit:
                break

    return {
        'total': total,
        'correct': correct,
        'incorrect': incorrect,
        'accuracy': correct / total * 100 if total > 0 else 0,
        'misclassified_samples': misclassified
    }


def test_on_classical_csv(classifier):
    """Test classifier on Classical CSV - should all be 'classical'"""
    filepath = os.path.join(settings.DATA_DIR, 'page 1-47 chanda list - complete.csv')

    correct = 0
    incorrect = 0
    total = 0
    misclassified = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    for row in rows[:150]:  # First 147 are real verses
        if len(row) >= 4:
            verse = row[0].strip()
            if not verse or verse == 'Shloka ' or verse == 'Shloka':
                continue

            # Skip single-line meter definitions (like "स्यादिन्द्रवज्रा यदि तौ जगौ गः")
            # Real verses have multiple lines or danda markers
            if '।' not in verse and '॥' not in verse and '\n' not in verse:
                continue  # Single-line definition, not a real verse

            total += 1
            classification, confidence = classify_text(verse)

            if classification == 'classical':
                correct += 1
            else:
                incorrect += 1
                if len(misclassified) < 20:
                    misclassified.append({
                        'text': verse[:60],
                        'classified_as': classification,
                        'confidence': confidence,
                    })

    return {
        'total': total,
        'correct': correct,
        'incorrect': incorrect,
        'accuracy': correct / total * 100 if total > 0 else 0,
        'misclassified_samples': misclassified
    }


def main():
    print("=" * 70)
    print("TEXT CLASSIFIER ACCURACY TEST")
    print("=" * 70)

    classifier = TextClassifier()

    # Test on Rigveda
    print("\n📜 Testing on Rigveda (Vedic texts)...")
    rigveda_results = test_on_rigveda(classifier, limit=2000)

    print(f"\n  Total tested: {rigveda_results['total']}")
    print(f"  Correctly classified as Vedic: {rigveda_results['correct']}")
    print(f"  Incorrectly classified as Classical: {rigveda_results['incorrect']}")
    print(f"  Accuracy: {rigveda_results['accuracy']:.1f}%")

    if rigveda_results['misclassified_samples']:
        print("\n  Sample misclassifications:")
        for sample in rigveda_results['misclassified_samples'][:5]:
            print(f"    - '{sample['text']}...' → {sample['classified_as']} ({sample['confidence']:.2f})")

    # Test on Classical CSV
    print("\n📋 Testing on Classical CSV...")
    classical_results = test_on_classical_csv(classifier)

    print(f"\n  Total tested: {classical_results['total']}")
    print(f"  Correctly classified as Classical: {classical_results['correct']}")
    print(f"  Incorrectly classified as Vedic: {classical_results['incorrect']}")
    print(f"  Accuracy: {classical_results['accuracy']:.1f}%")

    if classical_results['misclassified_samples']:
        print("\n  Sample misclassifications:")
        for sample in classical_results['misclassified_samples'][:5]:
            print(f"    - '{sample['text']}...' → {sample['classified_as']} ({sample['confidence']:.2f})")

    # Overall
    total_correct = rigveda_results['correct'] + classical_results['correct']
    total_tested = rigveda_results['total'] + classical_results['total']
    overall_accuracy = total_correct / total_tested * 100

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Rigveda (should be Vedic): {rigveda_results['accuracy']:.1f}%")
    print(f"Classical CSV (should be Classical): {classical_results['accuracy']:.1f}%")
    print(f"Overall accuracy: {overall_accuracy:.1f}%")
    print("=" * 70)

    return rigveda_results, classical_results


if __name__ == '__main__':
    main()
