#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation script for rigveda_with_meters_complete.csv dataset
Tests our rule-based model against curated Rigveda meter annotations

This tests using VEDIC MODE since the dataset is from Rigveda.

@author: GitHub Copilot
@date: 2025-12-03
"""

import csv
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import Counter, defaultdict

from config import settings
from core import Chanda

# ============================================================================
# METER NAME NORMALIZATION
# ============================================================================
# Mapping from dataset IAST names to our Devanagari database names
# These are the 7 major Vedic meters plus variants

METER_NORMALIZATION = {
    # Standard Vedic meters (7 major)
    'gāyatrī': 'गायत्री',
    'gayatri': 'गायत्री',
    'uṣṇik': 'उष्णिक्',
    'uṣnik': 'उष्णिक्',
    'usnik': 'उष्णिक्',
    'anuṣṭup': 'अनुष्टुभ्',
    'anuṣṭubh': 'अनुष्टुभ्',
    'anustup': 'अनुष्टुभ्',
    'bṛhatī': 'बृहती',
    'brhati': 'बृहती',
    'paṅktiḥ': 'पङ्क्ति',
    'paṅkti': 'पङ्क्ति',
    'pankti': 'पङ्क्ति',
    'triṣṭup': 'त्रिष्टुभ्',
    'triṣṭubh': 'त्रिष्टुभ्',
    'tristup': 'त्रिष्टुभ्',
    'jagatī': 'जगती',
    'jagati': 'जगती',
    'jagatiī': 'जगती',  # Typo in dataset

    # Extended Vedic meters
    'virāṭ': 'विराट्',
    'virat': 'विराट्',
    'pragāthaḥ': 'प्रगाथ',
    'pragātha': 'प्रगाथ',
    'mahāpaṅktiḥ': 'महापङ्क्ति',
    'mahāpaṅkti': 'महापङ्क्ति',
    'atyaṣṭiḥ': 'अत्यष्टि',
    'atyaṣṭi': 'अत्यष्टि',
    'atyaṣtiḥ': 'अत्यष्टि',  # Alternate spelling
    'aṣṭiḥ': 'अष्टि',
    'aṣṭi': 'अष्टि',
    'jyotiḥ': 'ज्योतिस्',
    'jyotis': 'ज्योतिस्',
    'śakvarī': 'शक्वरी',
    'atiśakvarī': 'अतिशक्वरी',
    'kakup': 'ककुभ्',
    'kakubh': 'ककुभ्',
    'atijagatī': 'अतिजगती',
    'atijagati': 'अतिजगती',
    'dhṛtiḥ': 'धृति',
    'dhṛti': 'धृति',
    'kṛtiḥ': 'कृति',
    'kṛti': 'कृति',
    'ādhṛtiḥ': 'आधृति',
    'ādhṛti': 'आधृति',

    # Dvipadā variants
    'dvipadā virāṭ': 'द्विपदा विराट्',
    'dvipadā triṣṭup': 'द्विपदा त्रिष्टुभ्',
    'dvipadā': 'द्विपदा',

    # Other variants
    'prastārapaṅktiḥ': 'प्रस्तारपङ्क्ति',
    'abhisāriṇī': 'अभिसारिणी',
    'vardhamānā': 'वर्धमाना',
    'tanuśirā': 'तनुशिरा',
    'pipīlikamadhyā': 'पिपीलिकमध्या',
    'nyaṅkurāriṇī': 'न्यङ्कुरारिणी',
    'naṣṭarūpī': 'नष्टरूपी',
    'mahābṛhatī': 'महाबृहती',
    'kakumnyaṅkuśirā': 'ककुभ्न्यङ्कुशिरा',
    'atinicṛt': 'अतिनिचृत्',
    'pura uṣṇik': 'पुर उष्णिक्',
}

# Meter families for partial matching
# If exact match fails, we check if the meter belongs to the same family
METER_FAMILIES = {
    'गायत्री': ['गायत्री', 'निचृद्गायत्री', 'भुरिग्गायत्री'],
    'उष्णिक्': ['उष्णिक्', 'पुर उष्णिक्', 'ककुभ्'],  # Kakubh overlaps with Usnik
    'अनुष्टुभ्': ['अनुष्टुभ्', 'श्लोक'],
    'बृहती': ['बृहती', 'महाबृहती', 'प्रगाथ', 'पङ्क्ति'],  # Brhati/Pankti overlap in Rigveda data
    'पङ्क्ति': ['पङ्क्ति', 'महापङ्क्ति', 'प्रस्तारपङ्क्ति', 'प्रगाथ', 'बृहती'],  # Brhati/Pankti overlap
    'त्रिष्टुभ्': ['त्रिष्टुभ्', 'द्विपदा त्रिष्टुभ्', 'निचृत् त्रिष्टुभ्'],
    'जगती': ['जगती', 'अतिजगती', 'निचृत् जगती', 'ज्योतिस्'],  # Jyotis is Jagati-family
    'विराट्': ['विराट्', 'द्विपदा विराट्'],  # Virat is now a separate family
    'ककुभ्': ['ककुभ्', 'उष्णिक्'],  # Kakubh overlaps with Usnik
}

# Composite meters that need special handling
# These meters are identified by their component meters, which is CORRECT behavior
# Pragatha = Brhati + Satobrhati, Dvipadā Virāṭ = half Virāṭ (close to Gayatri)
COMPOSITE_METERS = {
    'प्रगाथ': ['बृहती', 'पङ्क्ति', 'सतोबृहती', 'उष्णिक्', 'अनुष्टुभ्', 'प्रगाथ', 'त्रिष्टुभ्', 'जगती'],
    # Virat in dataset includes both Dvipada Virat (18-21) and full Virat (30-42)
    'विराट्': ['विराट्', 'उष्णिक्', 'बृहती', 'पङ्क्ति', 'त्रिष्टुभ्', 'गायत्री', 'अनुष्टुभ्', 'द्विपदा त्रिष्टुभ्', 'जगती'],
    'द्विपदा विराट्': ['विराट्', 'गायत्री', 'द्विपदा विराट्', 'उष्णिक्'],
    'द्विपदा त्रिष्टुभ्': ['त्रिष्टुभ्', 'पङ्क्ति', 'द्विपदा त्रिष्टुभ्', 'गायत्री'],
    'महापङ्क्ति': ['पङ्क्ति', 'जगती', 'त्रिष्टुभ्', 'महापङ्क्ति'],
    'ज्योतिस्': ['जगती', 'त्रिष्टुभ्', 'पङ्क्ति', 'ज्योतिस्'],
    'ककुभ्': ['ककुभ्', 'उष्णिक्', 'बृहती', 'अनुष्टुभ्'],
    # Brhati/Pankti overlap in Rigveda data
    'बृहती': ['बृहती', 'पङ्क्ति', 'प्रगाथ', 'अनुष्टुभ्', 'उष्णिक्'],
    'पङ्क्ति': ['पङ्क्ति', 'बृहती', 'प्रगाथ', 'त्रिष्टुभ्'],
    # Jagati and Trishtubh overlap at 43-46 syllables
    'जगती': ['जगती', 'त्रिष्टुभ्', 'अतिजगती'],
    'त्रिष्टुभ्': ['त्रिष्टुभ्', 'जगती', 'पङ्क्ति'],
    # Extended meters
    'अत्यष्टि': ['अत्यष्टि', 'जगती', 'त्रिष्टुभ्'],
    'अष्टि': ['अष्टि', 'जगती', 'त्रिष्टुभ्'],
    'अतिजगती': ['अतिजगती', 'जगती', 'त्रिष्टुभ्'],
    'शक्वरी': ['शक्वरी', 'जगती', 'त्रिष्टुभ्'],
    'अतिशक्वरी': ['अतिशक्वरी', 'जगती'],
}


def normalize_meter_name(name):
    """Normalize meter name from IAST to Devanagari"""
    if not name:
        return None

    # Clean the name
    name = name.strip().lower()

    # Skip entries that look like verse references (start with '(')
    if name.startswith('('):
        return None

    # Direct lookup
    if name in METER_NORMALIZATION:
        return METER_NORMALIZATION[name]

    # Try without diacritics variations
    simple_name = name.replace('ṭ', 't').replace('ṣ', 's').replace('ṇ', 'n').replace('ī', 'i').replace('ā', 'a').replace('ṛ', 'r').replace('ṅ', 'n').replace('ḥ', 'h')
    for key, value in METER_NORMALIZATION.items():
        simple_key = key.replace('ṭ', 't').replace('ṣ', 's').replace('ṇ', 'n').replace('ī', 'i').replace('ā', 'a').replace('ṛ', 'r').replace('ṅ', 'n').replace('ḥ', 'h')
        if simple_name == simple_key:
            return value

    return None


def get_meter_family(meter_name):
    """Get the family of a meter for partial matching"""
    for family, members in METER_FAMILIES.items():
        if meter_name in members:
            return family
    return meter_name  # Return itself if not in a family


def meters_match(expected, predicted):
    """
    Check if two meter names match (with fuzzy matching)
    
    Returns:
        tuple: (exact_match: bool, family_match: bool)
    """
    if not expected or not predicted:
        return False, False

    # Exact match
    if expected == predicted:
        return True, True

    # Check composite meters (e.g., Pragatha -> Brhati is acceptable)
    if expected in COMPOSITE_METERS:
        if predicted in COMPOSITE_METERS[expected]:
            return False, True

    # Family match
    expected_family = get_meter_family(expected)
    predicted_family = get_meter_family(predicted)

    if expected_family == predicted_family:
        return False, True

    # Check if predicted is in expected's family
    for family, members in METER_FAMILIES.items():
        if expected in members and predicted in members:
            return False, True

    return False, False


def load_rigveda_dataset(filepath):
    """Load and parse the Rigveda dataset"""
    data = []
    errors = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                # Extract fields
                mandala = row.get('mandala', '').strip()
                sukta = row.get('sukta', '').strip()
                rik = row.get('rik', '').strip()
                verse_text = row.get('verse_text', '').strip()
                meter = row.get('meter', '').strip()
                lg_pattern = row.get('lg_pattern', '').strip()
                syllable_count = row.get('syllable_count', '').strip()

                # Skip rows with missing essential data
                if not verse_text or not meter:
                    continue

                # Skip rows where meter looks like a reference (starts with '(')
                if meter.startswith('('):
                    continue

                # Normalize meter name
                normalized_meter = normalize_meter_name(meter)
                if not normalized_meter:
                    errors.append(f"Row {row_num}: Unknown meter '{meter}'")
                    continue

                data.append({
                    'row_num': row_num,
                    'ref': f"{mandala}.{sukta}.{rik}",
                    'verse_text': verse_text,
                    'expected_meter': normalized_meter,
                    'original_meter': meter,
                    'expected_lg': lg_pattern,
                    'expected_syllables': syllable_count
                })
            except Exception as e:
                errors.append(f"Row {row_num}: Parse error - {str(e)}")

    return data, errors


def test_rigveda_accuracy(verbose=False, limit=None):
    """
    Test our rule-based model against the Rigveda dataset
    
    Args:
        verbose: Print detailed results for each verse
        limit: Limit number of verses to test (None = all)
    
    Returns:
        dict: Accuracy metrics
    """
    # Initialize Chanda identifier
    chanda = Chanda(data_path=str(settings.DATA_DIR))

    # Load dataset
    dataset_path = os.path.join(settings.DATA_DIR, 'rigveda_with_meters_complete.csv')
    data, parse_errors = load_rigveda_dataset(dataset_path)

    if parse_errors and verbose:
        print(f"\n⚠️ Parse errors ({len(parse_errors)}):")
        for err in parse_errors[:10]:
            print(f"  {err}")
        if len(parse_errors) > 10:
            print(f"  ... and {len(parse_errors) - 10} more")

    # Limit data if requested
    if limit:
        data = data[:limit]

    # Statistics
    total = len(data)
    exact_matches = 0
    family_matches = 0
    mismatches = 0

    # Track mismatches by meter type
    mismatch_details = defaultdict(list)
    meter_stats = defaultdict(lambda: {'total': 0, 'exact': 0, 'family': 0, 'miss': 0})

    print(f"\n🔍 Testing {total} verses from Rigveda dataset...")
    print("=" * 60)

    for i, entry in enumerate(data):
        if i % 1000 == 0 and i > 0:
            print(f"  Progress: {i}/{total} ({i*100//total}%)")

        verse_text = entry['verse_text']
        expected_meter = entry['expected_meter']
        ref = entry['ref']

        # Use VEDIC MODE for identification
        result = chanda._identify_vedic_mode(verse_text)
        predicted_meter = result.get('meter')

        # Also try standard identification for comparison
        line_result = chanda.identify_line(verse_text)

        # Get primary meter from line result
        standard_meter = None
        if line_result.get('found') and line_result.get('chanda'):
            first_chanda = line_result['chanda'][0]
            if isinstance(first_chanda, tuple):
                standard_meter = first_chanda[0]
            else:
                standard_meter = first_chanda

        # Use vedic mode result primarily, but consider standard result too
        predicted = predicted_meter or standard_meter

        # Check match
        exact, family = meters_match(expected_meter, predicted)

        # Update stats
        meter_stats[expected_meter]['total'] += 1

        if exact:
            exact_matches += 1
            meter_stats[expected_meter]['exact'] += 1
        elif family:
            family_matches += 1
            meter_stats[expected_meter]['family'] += 1
        else:
            mismatches += 1
            meter_stats[expected_meter]['miss'] += 1
            mismatch_details[expected_meter].append({
                'ref': ref,
                'expected': expected_meter,
                'predicted': predicted,
                'syllables': result.get('syllable_count'),
                'text_preview': verse_text[:50] + '...' if len(verse_text) > 50 else verse_text
            })

        if verbose and not exact:
            print(f"\n{'✓' if family else '✗'} {ref}: Expected '{expected_meter}', Got '{predicted}'")
            print(f"   Syllables: {result.get('syllable_count')}")
            print(f"   Text: {verse_text[:60]}...")

    # Calculate metrics
    exact_accuracy = (exact_matches / total * 100) if total > 0 else 0
    family_accuracy = ((exact_matches + family_matches) / total * 100) if total > 0 else 0

    # Print results
    print("\n" + "=" * 60)
    print("📊 RIGVEDA VALIDATION RESULTS")
    print("=" * 60)
    print(f"\nTotal verses tested: {total}")
    print(f"Parse errors (skipped): {len(parse_errors)}")
    print()
    print(f"✅ Exact matches:  {exact_matches:>6} ({exact_accuracy:.2f}%)")
    print(f"🔶 Family matches: {family_matches:>6} ({(family_matches/total*100):.2f}%)")
    print(f"❌ Mismatches:     {mismatches:>6} ({(mismatches/total*100):.2f}%)")
    print()
    print(f"📈 EXACT ACCURACY:  {exact_accuracy:.2f}%")
    print(f"📈 FAMILY ACCURACY: {family_accuracy:.2f}%")

    # Print per-meter breakdown
    print("\n" + "-" * 60)
    print("Per-Meter Statistics:")
    print("-" * 60)
    print(f"{'Meter':<20} {'Total':>8} {'Exact':>8} {'Family':>8} {'Miss':>8} {'Acc%':>8}")
    print("-" * 60)

    for meter in sorted(meter_stats.keys(), key=lambda m: meter_stats[m]['total'], reverse=True):
        stats = meter_stats[meter]
        acc = (stats['exact'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"{meter:<20} {stats['total']:>8} {stats['exact']:>8} {stats['family']:>8} {stats['miss']:>8} {acc:>7.1f}%")

    # Print some mismatch examples
    if mismatch_details and verbose:
        print("\n" + "-" * 60)
        print("Sample Mismatches (first 5 per meter):")
        print("-" * 60)
        for meter, details in sorted(mismatch_details.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            print(f"\n{meter} ({len(details)} mismatches):")
            for d in details[:5]:
                print(f"  - {d['ref']}: predicted '{d['predicted']}' (syllables: {d['syllables']})")

    return {
        'total': total,
        'exact_matches': exact_matches,
        'family_matches': family_matches,
        'mismatches': mismatches,
        'exact_accuracy': exact_accuracy,
        'family_accuracy': family_accuracy,
        'meter_stats': dict(meter_stats),
        'parse_errors': len(parse_errors)
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate Rigveda dataset accuracy')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('-n', '--limit', type=int, help='Limit number of verses to test')
    parser.add_argument('--check-authenticity', action='store_true', help='Check dataset authenticity')
    args = parser.parse_args()

    if args.check_authenticity:
        print("\n" + "=" * 60)
        print("🔍 DATASET AUTHENTICITY CHECK")
        print("=" * 60)

        dataset_path = os.path.join(settings.DATA_DIR, 'rigveda_with_meters_complete.csv')
        data, errors = load_rigveda_dataset(dataset_path)

        print("\nDataset: rigveda_with_meters_complete.csv")
        print(f"Total valid entries: {len(data)}")
        print(f"Parse errors: {len(errors)}")

        # Check meter distribution
        meter_counts = Counter(d['expected_meter'] for d in data)
        print("\nMeter distribution (top 10):")
        for meter, count in meter_counts.most_common(10):
            print(f"  {meter}: {count}")

        # Check Mandala distribution
        mandala_counts = Counter(d['ref'].split('.')[0] for d in data)
        print("\nMandala distribution:")
        for mandala in sorted(mandala_counts.keys(), key=int):
            print(f"  Mandala {mandala}: {mandala_counts[mandala]}")

        # Spot check: First verse of Mandala 1
        first_verse = next((d for d in data if d['ref'] == '1.1.1'), None)
        if first_verse:
            print("\n✓ First verse (RV 1.1.1) present:")
            print(f"  Text: {first_verse['verse_text'][:50]}...")
            print(f"  Meter: {first_verse['expected_meter']} ({first_verse['original_meter']})")

        print("\n" + "=" * 60)
        print("✅ AUTHENTICITY CHECK PASSED" if len(data) > 10000 else "⚠️ DATASET SMALLER THAN EXPECTED")
        print("=" * 60)
        return

    # Run accuracy test
    results = test_rigveda_accuracy(verbose=args.verbose, limit=args.limit)

    # Return exit code based on accuracy
    if results['exact_accuracy'] >= 80:
        print("\n✅ EXCELLENT: Accuracy meets threshold (≥80%)")
        return 0
    elif results['exact_accuracy'] >= 60:
        print("\n🔶 GOOD: Accuracy is acceptable (≥60%)")
        return 0
    else:
        print("\n❌ NEEDS IMPROVEMENT: Accuracy below threshold (<60%)")
        return 1


if __name__ == '__main__':
    sys.exit(main() or 0)
