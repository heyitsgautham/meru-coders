#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TRUE PREDICTION ACCURACY TEST FOR RIG VEDA VERSES

This test uses ACTUAL Sanskrit verse text from Rig Veda with ground truth
meters from the Anukramani (WSC2023 dataset).

NO DATA LEAKAGE: These verses are NOT in our training data.

The test flow:
1. Load actual Rig Veda verse text (Devanagari)
2. Ground truth meter from Anukramani
3. Feed verse to Chanda Identifier
4. Compare prediction vs ground truth
5. Calculate TRUE prediction accuracy

Sources:
- Verse text: Sacred-texts.com / GRETIL / VedicReserve
- Ground truth: WSC2023 Anukramani dataset
"""

import os

from backend.core.chanda import Chanda
from backend.evaluation.rigveda_prediction_verses import RIGVEDA_TEST_VERSES

# =============================================================================
# RIG VEDA TEST VERSES WITH GROUND TRUTH METERS
# =============================================================================
# Format: {
#     'mandala': mandala_number,
#     'hymn': hymn_number,
#     'verse': verse_number (or range),
#     'text': actual_sanskrit_verse_text,
#     'meter': ground_truth_meter_from_anukramani,
#     'source': 'sacred-texts' or 'gretil' etc.
# }


def normalize_meter_name(name):
    """Normalize meter name for comparison."""
    if not name:
        return ''

    # Handle tuple results
    if isinstance(name, tuple):
        name = name[0] if name else ''

    name = str(name).lower().strip()

    # Remove diacritics for comparison
    replacements = {
        'ā': 'a',
        'ī': 'i',
        'ū': 'u',
        'ṛ': 'r',
        'ṝ': 'r',
        'ṅ': 'n',
        'ñ': 'n',
        'ṇ': 'n',
        'ṭ': 't',
        'ḍ': 'd',
        'ś': 's',
        'ṣ': 's',
        'ḥ': 'h',
        'ṃ': 'm',
        'ē': 'e',
        'ō': 'o',
        'ḷ': 'l',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)

    # Normalize common variants
    name = name.replace('anushtubh', 'anustubh')
    name = name.replace('anushtup', 'anustubh')
    name = name.replace('anustup', 'anustubh')
    name = name.replace('sloka', 'anustubh')
    name = name.replace('trishtubh', 'tristubh')
    name = name.replace('trishtup', 'tristubh')
    name = name.replace('tristup', 'tristubh')
    name = name.replace('gayatri', 'gayatri')
    name = name.replace('jagati', 'jagati')
    name = name.replace('brhati', 'brhati')
    name = name.replace('brihati', 'brhati')
    name = name.replace('usnik', 'usnik')
    name = name.replace('pankti', 'pankti')

    # Remove parenthetical info
    if '(' in name:
        name = name.split('(')[0].strip()

    return name


def is_vedic_meter_match(predicted, expected):
    """Check if predicted meter matches expected (with normalization)."""
    pred_norm = normalize_meter_name(predicted)
    exp_norm = normalize_meter_name(expected)

    # Direct match
    if pred_norm == exp_norm:
        return True

    # Check if expected is contained in predicted
    if exp_norm in pred_norm:
        return True

    # Check if predicted is a Vedic meter and matches syllable count
    vedic_syllables = {
        'gayatri': 24,
        'usnik': 28,
        'anustubh': 32,
        'brhati': 36,
        'pankti': 40,
        'tristubh': 44,
        'jagati': 48,
    }

    # Both should map to same syllable count
    if exp_norm in vedic_syllables and pred_norm in vedic_syllables:
        return vedic_syllables[exp_norm] == vedic_syllables[pred_norm]

    return False


def run_prediction_accuracy_test():
    """Run TRUE prediction accuracy test on Rig Veda verses."""

    print("\n" + "=" * 80)
    print("   TRUE PREDICTION ACCURACY TEST - RIG VEDA VERSES")
    print("=" * 80)
    print("\nThis test uses ACTUAL Sanskrit verse text with ground truth meters.")
    print("NO DATA LEAKAGE - verses are from external sources.\n")

    # Get data path
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    chanda = Chanda(data_path)

    results = []
    correct = 0
    incorrect = 0
    vedic_found_somewhere = 0  # Count if Vedic meter is anywhere in results
    syllable_based_correct = 0  # Count if syllable-based identification works

    meter_stats = {
        'gayatri': {'correct': 0, 'total': 0},
        'tristubh': {'correct': 0, 'total': 0},
        'jagati': {'correct': 0, 'total': 0},
        'anustubh': {'correct': 0, 'total': 0},
        'usnik': {'correct': 0, 'total': 0},
        'brhati': {'correct': 0, 'total': 0},
        'pankti': {'correct': 0, 'total': 0},
    }

    incorrect_predictions = []

    print(f"{'Verse':<15} {'Expected':<15} {'Predicted':<25} {'Status':<10}")
    print("-" * 75)

    for test in RIGVEDA_TEST_VERSES:
        mandala = test['mandala']
        hymn = test['hymn']
        verse = test['verse']
        text = test['text']
        expected = test['meter']

        verse_id = f"RV {mandala}.{hymn}.{verse}"

        # Get prediction from Chanda
        try:
            result = chanda.identify_from_text(text, verse=True, fuzzy=True)

            # Navigate the result structure: result['result']['verse'][0]['chanda']
            if result and result.get('result'):
                inner_result = result['result']

                # Try verse-level result first
                verses = inner_result.get('verse', [])
                if verses and len(verses) > 0:
                    first_verse = verses[0]
                    chanda_list = first_verse.get('chanda', [])
                    if chanda_list and len(chanda_list) > 0:
                        # chanda is a list like [['meter1', 'meter2', ...], score]
                        if isinstance(chanda_list[0], list):
                            predicted = chanda_list[0][0] if chanda_list[0] else 'Unknown'
                        else:
                            predicted = chanda_list[0]
                        confidence = first_verse.get('scores', [[None, 0]])[0][1] if first_verse.get('scores') else 0
                    else:
                        predicted = 'Unknown'
                        confidence = 0
                # Fall back to line-level
                else:
                    lines = inner_result.get('line', [])
                    if lines and len(lines) > 0:
                        first_line = lines[0]
                        line_result = first_line.get('result', {})
                        chanda_list = line_result.get('chanda', [])
                        if chanda_list:
                            first_chanda = chanda_list[0]
                            if isinstance(first_chanda, (list, tuple)):
                                predicted = first_chanda[0]
                            else:
                                predicted = first_chanda
                            # Get confidence
                            conf_scores = line_result.get('confidence_scores', {})
                            if predicted in conf_scores:
                                confidence = conf_scores[predicted][0]
                            else:
                                confidence = 0
                        else:
                            predicted = 'Unknown'
                            confidence = 0
                    else:
                        predicted = 'Unknown'
                        confidence = 0
            else:
                predicted = 'Unknown'
                confidence = 0
        except Exception as e:
            predicted = f'Error: {str(e)[:30]}'
            confidence = 0

        # Check if correct
        is_correct = is_vedic_meter_match(predicted, expected)

        # Also check if syllable-based identification would work
        try:
            # Count syllables in the verse
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            total_syllables = 0
            for line in lines:
                clean_line = line.replace('।', '').replace('॥', '').strip()
                if clean_line:
                    syllables = chanda.get_syllables_icu(clean_line)
                    total_syllables += len(syllables)

            # Check if syllable count matches expected Vedic meter
            vedic_syllable_map = {
                'gayatri': 24,
                'gāyatrī': 24,
                'usnik': 28,
                'uṣṇik': 28,
                'anustubh': 32,
                'anuṣṭubh': 32,
                'brhati': 36,
                'bṛhatī': 36,
                'pankti': 40,
                'paṅkti': 40,
                'tristubh': 44,
                'triṣṭubh': 44,
                'jagati': 48,
                'jagatī': 48,
            }

            expected_syllables = vedic_syllable_map.get(expected.lower(), 0)
            # Allow ±2 syllables tolerance for Vedic text variations
            if expected_syllables > 0 and abs(total_syllables - expected_syllables) <= 2:
                syllable_based_correct += 1
        except Exception:
            pass

        # Check if Vedic meter appears anywhere in all results
        vedic_found = False
        try:
            if result and result.get('result'):
                inner = result['result']
                # Check all lines
                for line_data in inner.get('line', []):
                    line_result = line_data.get('result', {})
                    jaati = line_result.get('jaati', [])
                    if jaati:
                        for j in jaati:
                            if is_vedic_meter_match(j, expected):
                                vedic_found = True
                                break
                    # Also check display_jaati
                    display_jaati = line_result.get('display_jaati', '')
                    if display_jaati and is_vedic_meter_match(display_jaati, expected):
                        vedic_found = True
                if vedic_found:
                    vedic_found_somewhere += 1
        except Exception:
            pass

        # Update stats
        exp_norm = normalize_meter_name(expected)
        if exp_norm in meter_stats:
            meter_stats[exp_norm]['total'] += 1
            if is_correct:
                meter_stats[exp_norm]['correct'] += 1

        if is_correct:
            correct += 1
            status = "✓ PASS"
        else:
            incorrect += 1
            status = "✗ FAIL"
            incorrect_predictions.append(
                {
                    'verse_id': verse_id,
                    'text': text[:60] + '...' if len(text) > 60 else text,
                    'expected': expected,
                    'predicted': predicted,
                    'notes': test.get('notes', ''),
                }
            )

        # Truncate prediction for display
        pred_display = predicted[:23] + '..' if len(str(predicted)) > 25 else predicted

        print(f"{verse_id:<15} {expected:<15} {pred_display:<25} {status:<10}")

        results.append(
            {
                'verse_id': verse_id,
                'expected': expected,
                'predicted': predicted,
                'correct': is_correct,
                'confidence': confidence,
            }
        )

    total = correct + incorrect
    accuracy = correct / total * 100 if total > 0 else 0
    syllable_accuracy = syllable_based_correct / total * 100 if total > 0 else 0
    vedic_found_pct = vedic_found_somewhere / total * 100 if total > 0 else 0

    print("-" * 75)
    print(f"\n{'=' * 80}")
    print("   RESULTS SUMMARY")
    print("=" * 80)

    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    RIG VEDA PREDICTION ACCURACY                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   Total Verses Tested:           {total:>4}                                       ║
║                                                                               ║
║   ┌─────────────────────────────────────────────────────────────────────┐    ║
║   │ TOP-1 ACCURACY (Primary Prediction)                                 │    ║
║   │   Correct Predictions:       {correct:>4}                                   │    ║
║   │   Incorrect Predictions:     {incorrect:>4}                                   │    ║
║   │   ACCURACY:                {accuracy:>6.1f}%                                  │    ║
║   └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                               ║
║   ┌─────────────────────────────────────────────────────────────────────┐    ║
║   │ SYLLABLE-BASED ACCURACY (Vedic meter by syllable count)             │    ║
║   │   Verses with correct syllable count: {syllable_based_correct:>4}                       │    ║
║   │   ACCURACY:                {syllable_accuracy:>6.1f}%                                  │    ║
║   └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                               ║
║   ┌─────────────────────────────────────────────────────────────────────┐    ║
║   │ VEDIC METER IN RESULTS (Jāti field)                                 │    ║
║   │   Verses where Vedic meter found: {vedic_found_somewhere:>4}                           │    ║
║   │   PERCENTAGE:              {vedic_found_pct:>6.1f}%                                  │    ║
║   └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    # Per-meter breakdown
    print("\n--- Per-Meter Breakdown ---")
    print(f"{'Meter':<15} {'Correct':<10} {'Total':<10} {'Accuracy':<10}")
    print("-" * 45)
    for meter, stats in meter_stats.items():
        if stats['total'] > 0:
            acc = stats['correct'] / stats['total'] * 100
            print(f"{meter:<15} {stats['correct']:<10} {stats['total']:<10} {acc:.1f}%")

    # Show incorrect predictions
    if incorrect_predictions:
        print("\n" + "=" * 80)
        print("   INCORRECT PREDICTIONS (for debugging)")
        print("=" * 80)
        for pred in incorrect_predictions:
            print(f"\n  {pred['verse_id']}: {pred['notes']}")
            print(f"    Expected: {pred['expected']}")
            print(f"    Predicted: {pred['predicted']}")
            print(f"    Text: {pred['text']}")

    return accuracy, results, incorrect_predictions


def generate_sample_verses_for_frontend():
    """Generate sample verses that can be tested in the frontend."""

    print("\n" + "=" * 80)
    print("   SAMPLE VERSES FOR FRONTEND TESTING")
    print("=" * 80)

    samples = [
        {
            'name': 'Gayatri Mantra (RV 3.62.10)',
            'meter': 'Gāyatrī (24 syllables = 3×8)',
            'text': 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि ।\nधियो यो नः प्रचोदयात् ॥',
        },
        {
            'name': 'Agni Sukta Opening (RV 1.1.1)',
            'meter': 'Gāyatrī (24 syllables = 3×8)',
            'text': 'अग्निमीळे पुरोहितं यज्ञस्य देवं ऋत्विजम् ।\nहोतारं रत्नधातमम् ॥',
        },
        {
            'name': 'Indra-Vritra (RV 1.32.1)',
            'meter': 'Triṣṭubh (44 syllables = 4×11)',
            'text': 'इन्द्रस्य नु वीर्याणि प्र वोचं यानि चकार प्रथमानि वज्री ।\nअहन्नहिमन्वपस्ततर्द प्र वक्षणा अभिनत्पर्वतानाम् ॥',
        },
        {
            'name': 'Nasadiya (RV 10.129.1)',
            'meter': 'Triṣṭubh (44 syllables = 4×11)',
            'text': 'नासदासीन्नो सदासीत्तदानीं नासीद्रजो नो व्योमा परो यत् ।\nकिमावरीवः कुह कस्य शर्मन्नम्भः किमासीद्गहनं गभीरम् ॥',
        },
        {
            'name': 'Purusha Sukta (RV 10.90.1)',
            'meter': 'Anuṣṭubh (32 syllables = 4×8)',
            'text': 'सहस्रशीर्षा पुरुषः सहस्राक्षः सहस्रपात् ।\nस भूमिं विश्वतो वृत्वात्यतिष्ठद्दशाङ्गुलम् ॥',
        },
        {
            'name': 'Two Birds (RV 1.164.20)',
            'meter': 'Jagatī (48 syllables = 4×12)',
            'text': 'द्वा सुपर्णा सयुजा सखाया समानं वृक्षं परिषस्वजाते ।\nतयोरन्यः पिप्पलं स्वाद्वत्त्यनश्नन्नन्यो अभिचाकशीति ॥',
        },
        {
            'name': 'Ekam Sat (RV 1.164.46)',
            'meter': 'Jagatī (48 syllables = 4×12)',
            'text': 'इन्द्रं मित्रं वरुणमग्निमाहुरथो दिव्यः स सुपर्णो गरुत्मान् ।\nएकं सद्विप्रा बहुधा वदन्त्यग्निं यमं मातरिश्वानमाहुः ॥',
        },
        {
            'name': 'Vishnu Three Strides (RV 1.154.1)',
            'meter': 'Triṣṭubh (44 syllables = 4×11)',
            'text': 'विष्णोर्नु कं वीर्याणि प्र वोचं यः पार्थिवानि विममे रजांसि ।\nयो अस्कभायदुत्तरं सधस्थं विचक्रमाणस्त्रेधोरुगायः ॥',
        },
    ]

    print("\nCopy these verses to test in the frontend:\n")

    for i, sample in enumerate(samples, 1):
        print(f"\n--- {i}. {sample['name']} ---")
        print(f"Expected: {sample['meter']}")
        print(f"\nVerse:\n{sample['text']}")
        print()

    return samples


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     RIG VEDA PREDICTION ACCURACY TEST                                         ║
║     ─────────────────────────────────                                         ║
║                                                                               ║
║     Source: Actual Sanskrit verses with ground truth from Anukramani          ║
║     NO DATA LEAKAGE: External validation dataset                              ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    # Run the main prediction test
    accuracy, results, incorrect = run_prediction_accuracy_test()

    # Generate sample verses for frontend
    samples = generate_sample_verses_for_frontend()

    print("\n" + "=" * 80)
    print("   TEST COMPLETE")
    print("=" * 80)
    print(f"\n   Final Accuracy: {accuracy:.2f}%")
    print(f"   Incorrect Predictions: {len(incorrect)}")
    print("\n   Use the sample verses above to test in the frontend!")
