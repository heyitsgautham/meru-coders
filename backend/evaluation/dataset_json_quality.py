#!/usr/bin/env python3
"""
Test the quality of dataset.json
Verify if the labeled meters match what our chanda engine identifies.
"""

import json
import sys
from pathlib import Path

from backend.config.settings import Settings
from backend.core.chanda import Chanda

backend_dir = Path(__file__).parent.parent


settings = Settings()


def test_dataset_quality():
    """Test dataset.json quality by comparing labeled meters with identified meters."""

    # Load dataset
    dataset_path = backend_dir / "data" / "dataset.json"
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Initialize chanda engine
    chanda = Chanda(data_path=str(settings.DATA_DIR))

    # Track results
    results = {'total': 0, 'correct': 0, 'incorrect': 0, 'errors': []}

    print(f"Testing {len(data['data'])} entries from dataset.json...\n")

    for idx, entry in enumerate(data['data']):
        results['total'] += 1
        text = entry['text']
        expected_meter = entry['meter']

        try:
            # Handle multi-line verses - split and take first line only
            lines = text.strip().split('\n')
            first_line = lines[0].strip()

            # Identify the meter from first line
            result = chanda.identify_line(first_line)

            if result['found']:
                # Extract clean meter name (remove transliteration and confidence scores)
                identified_full = result['display_chanda_primary']
                # Take first part before space (removes transliteration in parentheses)
                identified_meter = identified_full.split(' ')[0] if ' ' in identified_full else identified_full

                # Check if it matches
                if identified_meter == expected_meter:
                    results['correct'] += 1
                else:
                    results['incorrect'] += 1
                    results['errors'].append(
                        {
                            'index': idx + 1,
                            'text': first_line[:60] + '...' if len(first_line) > 60 else first_line,
                            'expected': expected_meter,
                            'identified': identified_meter,
                            'identified_full': identified_full,
                            'confidence': result.get('confidence', 'N/A'),
                        }
                    )
            else:
                results['incorrect'] += 1
                results['errors'].append(
                    {
                        'index': idx + 1,
                        'text': first_line[:60] + '...' if len(first_line) > 60 else first_line,
                        'expected': expected_meter,
                        'identified': 'NOT FOUND',
                        'confidence': 0,
                    }
                )

        except Exception as e:
            results['incorrect'] += 1
            results['errors'].append(
                {
                    'index': idx + 1,
                    'text': text[:60] + '...' if len(text) > 60 else text,
                    'expected': expected_meter,
                    'identified': f'ERROR: {str(e)}',
                    'confidence': 0,
                }
            )

    # Print results
    accuracy = (results['correct'] / results['total'] * 100) if results['total'] > 0 else 0

    print("=" * 80)
    print("DATASET QUALITY TEST RESULTS")
    print("=" * 80)
    print(f"Total entries: {results['total']}")
    print(f"Correct matches: {results['correct']}")
    print(f"Incorrect matches: {results['incorrect']}")
    print(f"Accuracy: {accuracy:.2f}%")
    print("=" * 80)

    if results['errors']:
        print("\n❌ MISMATCHES (showing first 20):")
        print("-" * 80)
        for error in results['errors'][:20]:
            print(f"\n#{error['index']}")
            print(f"Text: {error['text']}")
            print(f"Expected: {error['expected']}")
            print(f"Identified: {error['identified']}")
            if 'identified_full' in error:
                print(f"Full output: {error['identified_full']}")
            if 'confidence' in error and error['confidence'] != 'N/A':
                print(f"Confidence: {error['confidence']}")

    # Final verdict
    print("\n" + "=" * 80)
    if accuracy >= 95:
        print("✅ VERDICT: Dataset is HIGH QUALITY (≥95% accuracy)")
        return True
    elif accuracy >= 80:
        print("⚠️ VERDICT: Dataset has MODERATE QUALITY (80-95% accuracy)")
        return False
    else:
        print("❌ VERDICT: Dataset is GARBAGE (<80% accuracy)")
        return False


if __name__ == "__main__":
    success = test_dataset_quality()
    sys.exit(0 if success else 1)
