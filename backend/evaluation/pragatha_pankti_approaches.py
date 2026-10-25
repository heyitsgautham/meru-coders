#!/usr/bin/env python3
"""
Test multiple approaches for discriminating Pragātha vs Paṅkti meters.

Based on empirical analysis of pragatha_pankti_verses.csv (676 verses):
- Pragātha: 409 verses, syllables 21-45, mode=39, mean=35.4
- Paṅkti: 204 verses, syllables 30-47, mode=39, mean=39.0
- Overlap zone: 37-40 syllables (both have significant counts)

Key discriminating features discovered:
1. Syllable count: ≤36 → 97%+ Pragātha; ≥43 → Paṅkti
2. Refrain patterns: 35.8% Paṅkti have refrains vs 0.7% Pragātha
3. Seer-based hints: Some seers exclusive to one meter
"""

import os
from typing import Tuple

import pandas as pd

# Known Paṅkti refrain patterns (found in 35.8% of Paṅkti, <1% of Pragātha)
PANKTI_REFRAINS = [
    'स्वराज्यं',  # 9.3% of Pankti, 0% Pragatha
    'ते हरी',
    'तुवीमघ',
    'रोदसी',
    'आ भर',
    'श्रुतं हवं',
    'रातयः',
    'धन्वसु',
    'चनाममत्',
    'अर्चन्ननु',
    'वस्वीरनु',
]

# Paṅkti-EXCLUSIVE endings (appear in Paṅkti, ZERO in Pragātha)
PANKTI_EXCLUSIVE_ENDINGS = [
    'उत्तरः',  # 23 in Paṅkti, 0 in Pragātha
    'स्वराज्यं',  # 19 in Paṅkti, 0 in Pragātha
    'स्रव',  # 19 in Paṅkti, 0 in Pragātha
    'विवक्षसे',  # 17 in Paṅkti, 0 in Pragātha
    'अश्वसूनृते',  # 10 in Paṅkti, 0 in Pragātha
    'तुवीमघ',  # 7 in Paṅkti, 0 in Pragātha
    'हरी',  # 5 in Paṅkti, 0 in Pragātha (as ending word)
    'चनाममत्',  # 3 in Paṅkti, 0 in Pragātha
]

# Paṅkti-exclusive 2-word sequences
PANKTI_EXCLUSIVE_SEQUENCES = [
    'परि स्रव',  # 19 in Paṅkti
    'इंद्र उत्तरः',  # 16+ in Paṅkti
    'अस्य रोदसी',  # 10 in Paṅkti
    'अश्वसूनृते',  # 10 in Paṅkti
    'श्रुतं हवं',  # 9 in Paṅkti
    'सहस्रेषु तुवीमघ',  # 7 in Paṅkti
    'ते हरी',  # 5 in Paṅkti
    'नो वृधे',  # 4 in Paṅkti
]

# Seers predominantly associated with one meter
PRAGATHA_SEERS = {
    'kāṇvaḥ sobhariḥ',
    'prāgātho bhargaḥ',  # Name literally contains "prāgātha"!
    'prāgāthaḥ kaliḥ',
    'prāgātho ghauraḥ',
}

PANKTI_SEERS = {
    'rāhūgaṇo gotamaḥ',
    'aindraḥ prājapatyaḥ',
}


def approach_a_syllable_only(syllable_count: int) -> Tuple[str, float]:
    """
    Approach A: Pure syllable-count based discrimination.

    Based on empirical data:
    - ≤33: 98%+ Pragātha
    - 34-36: 82-97% Pragātha
    - 37: 50-50
    - 38: 38% Pragātha, 62% Paṅkti
    - 39: 60% Pragātha, 40% Paṅkti (both peak here!)
    - 40: 48% Pragātha, 52% Paṅkti
    - ≥43: Paṅkti/mahāpaṅkti
    """
    if syllable_count <= 33:
        return 'pragāthaḥ', 0.98
    elif syllable_count <= 36:
        return 'pragāthaḥ', 0.85
    elif syllable_count == 37:
        return 'pragāthaḥ', 0.50  # Coin flip
    elif syllable_count == 38:
        return 'paṅktiḥ', 0.62
    elif syllable_count == 39:
        return 'pragāthaḥ', 0.60  # Slight edge to Pragātha at peak
    elif syllable_count == 40:
        return 'paṅktiḥ', 0.52
    elif syllable_count <= 42:
        return 'paṅktiḥ', 0.70
    elif syllable_count <= 46:
        return 'mahāpaṅktiḥ', 0.80  # mahāpaṅkti range
    else:
        return 'paṅktiḥ', 0.60


def approach_b_refrain_first(verse_text: str, syllable_count: int) -> Tuple[str, float]:
    """
    Approach B: Refrain detection first, then syllable count.

    Key insight: Paṅkti verses often have refrains (35.8%), Pragātha rarely (0.7%).
    """
    # Check for Paṅkti refrain patterns in last 40 characters
    last_40 = verse_text[-40:] if len(verse_text) > 40 else verse_text

    for refrain in PANKTI_REFRAINS:
        if refrain in last_40:
            return 'paṅktiḥ', 0.95  # High confidence if refrain found

    # No refrain found - use syllable count with Pragātha bias
    if syllable_count <= 36:
        return 'pragāthaḥ', 0.90
    elif syllable_count <= 40:
        return 'pragāthaḥ', 0.65  # Slight Pragātha bias when no refrain
    elif syllable_count <= 42:
        return 'paṅktiḥ', 0.60
    else:
        return 'mahāpaṅktiḥ', 0.75


def approach_c_seer_aware(verse_text: str, syllable_count: int, seer: str) -> Tuple[str, float]:
    """
    Approach C: Use seer information + refrain + syllable count.

    Some seers are strongly associated with specific meters.
    """
    # Check seer first
    seer_lower = seer.lower() if seer else ''

    # "prāgātha" in seer name is a strong signal
    if 'prāgātha' in seer_lower or 'prāgātho' in seer_lower:
        return 'pragāthaḥ', 0.95

    if any(s.lower() in seer_lower for s in PRAGATHA_SEERS):
        return 'pragāthaḥ', 0.85

    if any(s.lower() in seer_lower for s in PANKTI_SEERS):
        return 'paṅktiḥ', 0.85

    # Fall back to refrain + syllable approach
    return approach_b_refrain_first(verse_text, syllable_count)


def approach_d_hybrid_weighted(verse_text: str, syllable_count: int, seer: str) -> Tuple[str, float]:
    """
    Approach D: Weighted combination of all signals.

    Scoring system:
    - Start neutral (score=0)
    - Positive = Pragātha, Negative = Paṅkti
    """
    score = 0.0

    # 1. Syllable count signal (strongest outside overlap zone)
    if syllable_count <= 33:
        score += 3.0  # Strong Pragātha
    elif syllable_count <= 36:
        score += 2.0  # Pragātha
    elif syllable_count == 37:
        score += 0.0  # Neutral
    elif syllable_count == 38:
        score -= 0.5  # Slight Paṅkti
    elif syllable_count == 39:
        score += 0.5  # Slight Pragātha (peak)
    elif syllable_count == 40:
        score -= 0.2  # Very slight Paṅkti
    elif syllable_count <= 42:
        score -= 1.5  # Paṅkti
    else:
        score -= 2.5  # Strong Paṅkti/mahāpaṅkti

    # 2. Refrain signal (strong for Paṅkti)
    last_40 = verse_text[-40:] if len(verse_text) > 40 else verse_text
    for refrain in PANKTI_REFRAINS:
        if refrain in last_40:
            score -= 3.0  # Strong Paṅkti signal
            break

    # 3. Seer signal
    seer_lower = seer.lower() if seer else ''
    if 'prāgātha' in seer_lower or 'prāgātho' in seer_lower:
        score += 2.5
    elif any(s.lower() in seer_lower for s in PRAGATHA_SEERS):
        score += 1.0
    elif any(s.lower() in seer_lower for s in PANKTI_SEERS):
        score -= 1.0

    # Convert score to prediction
    if score > 0.5:
        confidence = min(0.95, 0.5 + abs(score) * 0.1)
        return 'pragāthaḥ', confidence
    elif score < -0.5:
        confidence = min(0.95, 0.5 + abs(score) * 0.1)
        if syllable_count >= 43:
            return 'mahāpaṅktiḥ', confidence
        return 'paṅktiḥ', confidence
    else:
        # Very close - default to syllable count majority
        if syllable_count <= 39:
            return 'pragāthaḥ', 0.55
        else:
            return 'paṅktiḥ', 0.55


def approach_e_simple_threshold(syllable_count: int, verse_text: str) -> Tuple[str, float]:
    """
    Approach E: Simple decision tree based on strongest discriminators.

    1. If refrain → Paṅkti
    2. If ≤36 syllables → Pragātha
    3. If ≥43 syllables → mahāpaṅkti
    4. If 37-42 syllables → use 39 as threshold
    """
    # Check refrain first
    last_40 = verse_text[-40:] if len(verse_text) > 40 else verse_text
    for refrain in PANKTI_REFRAINS:
        if refrain in last_40:
            if syllable_count >= 43:
                return 'mahāpaṅktiḥ', 0.90
            return 'paṅktiḥ', 0.90

    # Syllable-based
    if syllable_count <= 36:
        return 'pragāthaḥ', 0.92  # 92%+ accurate in this range
    elif syllable_count >= 43:
        return 'mahāpaṅktiḥ', 0.85
    elif syllable_count <= 39:
        return 'pragāthaḥ', 0.58  # Slight edge at 37-39
    else:
        return 'paṅktiḥ', 0.55  # Slight edge at 40-42


def approach_f_exclusive_endings(verse_text: str, syllable_count: int, seer: str) -> Tuple[str, float]:
    """
    Approach F: Use Paṅkti-EXCLUSIVE word endings (100% precision).

    These endings appear ONLY in Paṅkti, never in Pragātha.
    """
    # Get last word
    words = verse_text.strip().split()
    last_word = words[-1] if words else ''

    # Check for Paṅkti-exclusive endings (100% precision)
    if last_word in PANKTI_EXCLUSIVE_ENDINGS:
        if syllable_count >= 43:
            return 'mahāpaṅktiḥ', 0.99
        return 'paṅktiḥ', 0.99

    # Check for exclusive word sequences in last part
    last_text = verse_text[-50:] if len(verse_text) > 50 else verse_text
    for seq in PANKTI_EXCLUSIVE_SEQUENCES:
        if seq in last_text:
            if syllable_count >= 43:
                return 'mahāpaṅktiḥ', 0.98
            return 'paṅktiḥ', 0.98

    # Check traditional refrains
    last_40 = verse_text[-40:] if len(verse_text) > 40 else verse_text
    for refrain in PANKTI_REFRAINS:
        if refrain in last_40:
            if syllable_count >= 43:
                return 'mahāpaṅktiḥ', 0.95
            return 'paṅktiḥ', 0.95

    # Check seer
    seer_lower = seer.lower() if seer else ''
    if 'prāgātha' in seer_lower or 'prāgātho' in seer_lower:
        return 'pragāthaḥ', 0.95

    # Syllable-based fallback
    if syllable_count <= 36:
        return 'pragāthaḥ', 0.92
    elif syllable_count >= 43:
        return 'mahāpaṅktiḥ', 0.80
    elif syllable_count <= 39:
        return 'pragāthaḥ', 0.58
    else:
        return 'paṅktiḥ', 0.55


def approach_g_all_signals(verse_text: str, syllable_count: int, seer: str, lg_pattern: str) -> Tuple[str, float]:
    """
    Approach G: All signals combined with weighted scoring.

    Combines:
    1. Exclusive endings (strongest signal)
    2. Refrain patterns
    3. Seer hints
    4. Syllable count
    5. L-G pattern suffix hints
    """
    score = 0.0  # Positive = Pragātha, Negative = Paṅkti

    # 1. Exclusive endings (strongest for Paṅkti)
    words = verse_text.strip().split()
    last_word = words[-1] if words else ''

    if last_word in PANKTI_EXCLUSIVE_ENDINGS:
        score -= 5.0  # Very strong Paṅkti signal

    # 2. Exclusive sequences
    last_text = verse_text[-50:] if len(verse_text) > 50 else verse_text
    for seq in PANKTI_EXCLUSIVE_SEQUENCES:
        if seq in last_text:
            score -= 4.0
            break

    # 3. Refrain patterns
    last_40 = verse_text[-40:] if len(verse_text) > 40 else verse_text
    for refrain in PANKTI_REFRAINS:
        if refrain in last_40:
            score -= 3.0
            break

    # 4. Seer signals
    seer_lower = seer.lower() if seer else ''
    if 'prāgātha' in seer_lower or 'prāgātho' in seer_lower:
        score += 4.0
    elif any(s.lower() in seer_lower for s in PRAGATHA_SEERS):
        score += 1.5
    elif any(s.lower() in seer_lower for s in PANKTI_SEERS):
        score -= 1.5

    # 5. Syllable count
    if syllable_count <= 33:
        score += 3.0
    elif syllable_count <= 36:
        score += 2.0
    elif syllable_count == 38:
        score -= 0.5
    elif syllable_count == 39:
        score += 0.3
    elif syllable_count >= 43:
        score -= 2.5

    # 6. L-G pattern suffix hints (some suffixes are more Paṅkti)
    if lg_pattern and len(lg_pattern) >= 8:
        suffix = lg_pattern[-8:]
        # These suffixes favor Paṅkti (87%, 71%, 69%)
        pankti_suffixes = ['लगगलगलगग', 'लगगगलगलल', 'लगगललगलल']
        if suffix in pankti_suffixes:
            score -= 1.0

    # Convert to prediction
    if score > 1.0:
        confidence = min(0.95, 0.6 + abs(score) * 0.05)
        return 'pragāthaḥ', confidence
    elif score < -1.0:
        confidence = min(0.95, 0.6 + abs(score) * 0.05)
        if syllable_count >= 43:
            return 'mahāpaṅktiḥ', confidence
        return 'paṅktiḥ', confidence
    else:
        # Close call - use syllable count
        if syllable_count <= 39:
            return 'pragāthaḥ', 0.52
        else:
            return 'paṅktiḥ', 0.52


def run_evaluation():
    """Run all approaches on the test data and compare accuracy."""

    # Load test data
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'pragatha_pankti_verses.csv')
    df = pd.read_csv(csv_path)

    # Filter to main meters (exclude variants with complex names)
    df = df[df['meter'].isin(['pragāthaḥ', 'paṅktiḥ', 'mahāpaṅktiḥ'])]

    print("=" * 80)
    print("PRAGĀTHA vs PAṄKTI DETECTION - MULTI-APPROACH EVALUATION")
    print("=" * 80)
    print(f"\nDataset: {len(df)} verses")
    print(f"  - Pragātha: {len(df[df['meter'] == 'pragāthaḥ'])}")
    print(f"  - Paṅkti: {len(df[df['meter'] == 'paṅktiḥ'])}")
    print(f"  - Mahāpaṅkti: {len(df[df['meter'] == 'mahāpaṅktiḥ'])}")

    approaches = {
        'A: Syllable Only': lambda r: approach_a_syllable_only(r['syllable_count']),
        'B: Refrain First': lambda r: approach_b_refrain_first(r['verse_text'], r['syllable_count']),
        'C: Seer Aware': lambda r: approach_c_seer_aware(r['verse_text'], r['syllable_count'], r['seer']),
        'D: Hybrid Weighted': lambda r: approach_d_hybrid_weighted(r['verse_text'], r['syllable_count'], r['seer']),
        'E: Simple Threshold': lambda r: approach_e_simple_threshold(r['syllable_count'], r['verse_text']),
        'F: Exclusive Endings': lambda r: approach_f_exclusive_endings(r['verse_text'], r['syllable_count'], r['seer']),
        'G: All Signals': lambda r: approach_g_all_signals(
            r['verse_text'], r['syllable_count'], r['seer'], r['lg_pattern']
        ),
    }

    results = {name: {'correct': 0, 'total': 0, 'by_meter': {}} for name in approaches}

    for _idx, row in df.iterrows():
        actual = row['meter']

        for name, approach_fn in approaches.items():
            predicted, confidence = approach_fn(row)

            is_correct = predicted == actual
            results[name]['total'] += 1
            if is_correct:
                results[name]['correct'] += 1

            # Track by actual meter
            if actual not in results[name]['by_meter']:
                results[name]['by_meter'][actual] = {'correct': 0, 'total': 0}
            results[name]['by_meter'][actual]['total'] += 1
            if is_correct:
                results[name]['by_meter'][actual]['correct'] += 1

    # Print results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print("\n### Overall Accuracy ###\n")
    print(f"{'Approach':<25} {'Accuracy':>10} {'Correct':>10} {'Total':>8}")
    print("-" * 55)

    sorted_results = sorted(results.items(), key=lambda x: x[1]['correct'] / x[1]['total'], reverse=True)

    for name, data in sorted_results:
        acc = 100 * data['correct'] / data['total']
        print(f"{name:<25} {acc:>9.1f}% {data['correct']:>10} {data['total']:>8}")

    # Detailed breakdown by meter
    print("\n### Accuracy by Meter ###\n")

    for name, data in sorted_results:
        print(f"\n{name}:")
        for meter, stats in sorted(data['by_meter'].items()):
            if stats['total'] > 0:
                acc = 100 * stats['correct'] / stats['total']
                print(f"  {meter:<15} {acc:>6.1f}% ({stats['correct']}/{stats['total']})")

    # Focus on overlap zone (37-40 syllables)
    print("\n" + "=" * 80)
    print("OVERLAP ZONE ANALYSIS (37-40 syllables)")
    print("=" * 80)

    overlap_df = df[df['syllable_count'].isin([37, 38, 39, 40])]
    print(f"\nOverlap zone: {len(overlap_df)} verses")
    print(f"  - Pragātha: {len(overlap_df[overlap_df['meter'] == 'pragāthaḥ'])}")
    print(f"  - Paṅkti: {len(overlap_df[overlap_df['meter'] == 'paṅktiḥ'])}")

    overlap_results = {name: {'correct': 0, 'total': 0} for name in approaches}

    for _idx, row in overlap_df.iterrows():
        actual = row['meter']

        for name, approach_fn in approaches.items():
            predicted, confidence = approach_fn(row)

            overlap_results[name]['total'] += 1
            if predicted == actual:
                overlap_results[name]['correct'] += 1

    print("\n### Overlap Zone Accuracy ###\n")
    print(f"{'Approach':<25} {'Accuracy':>10}")
    print("-" * 37)

    sorted_overlap = sorted(
        overlap_results.items(), key=lambda x: x[1]['correct'] / max(1, x[1]['total']), reverse=True
    )
    for name, data in sorted_overlap:
        if data['total'] > 0:
            acc = 100 * data['correct'] / data['total']
            print(f"{name:<25} {acc:>9.1f}%")

    return sorted_results[0][0]  # Return best approach name


if __name__ == '__main__':
    best = run_evaluation()
    print(f"\n{'=' * 80}")
    print(f"BEST APPROACH: {best}")
    print("=" * 80)
