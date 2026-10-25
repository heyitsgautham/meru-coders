#!/usr/bin/env python3
"""
Cross-Dataset Performance Comparison

This script compares the effect of different meter databases on identification accuracy:

1. chanda_iitk.py + OUR curated 1920 meter dataset (backend/data/)
2. chanda_iitk.py + ORIGINAL IITK dataset (repos/chanda/data/)
3. enhanced_chanda.py + OUR curated 1920 meter dataset
4. chanda.py (our backend/core) + OUR curated 1920 meter dataset

All tested against: page 1-47 chanda list - Sheet1.csv (109 verses)

Goal: Measure the improvement from our curated dataset vs original IITK dataset.
"""

import csv
import re
import sys
from pathlib import Path

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

BACKEND_PATH = Path(__file__).parent.parent

ORIGINAL_REPO_PATH = BACKEND_PATH.parent / 'repos' / 'chanda'
REFERENCE_PATH = BACKEND_PATH.parent / 'reference' / 'alternative_implementations'
sys.path.insert(0, str(ORIGINAL_REPO_PATH))


# ============================================================================
# Meter Name Normalization
# ============================================================================

METER_ALIASES = {
    # Anushtubh variants
    'anushtup': 'anushtubh',
    'anushtubha': 'anushtubh',
    'anustubh': 'anushtubh',
    'anustup': 'anushtubh',
    'sloka': 'anushtubh',
    'shloka': 'anushtubh',
    'pathyavaktra': 'anushtubh',
    'pathya': 'anushtubh',
    # Vasantatilaka variants
    'vasantatilaka': 'vasantatilaka',
    'vasanthatilaka': 'vasantatilaka',
    'vasantatilakam': 'vasantatilaka',
    # Indravajra variants
    'indravajra': 'indravajra',
    # Upendravajra variants
    'upendravajra': 'upendravajra',
    # Upajati variants - map to generic upajati
    'upajati': 'upajati',
    'upajatih': 'upajati',
    # Shardulavikridita variants - IMPORTANT: handle the 'vk' vs 'vik' spelling
    'sardulavikridita': 'shardulavikridita',
    'sardulavikriditam': 'shardulavikridita',
    'shardulavikriditam': 'shardulavikridita',
    'shardulavkridita': 'shardulavikridita',  # Missing 'i' variant
    'shardulavikridita': 'shardulavikridita',
    # Mandakranta variants
    'mandakranta': 'mandakranta',
    'mandaakraantaa': 'mandakranta',
    # Sragdhara variants
    'sragdhara': 'sragdhara',
    # Prithvi variants
    'prithvi': 'prithvi',
    'prthvi': 'prithvi',
    # Shikharini variants
    'sikharini': 'shikharini',
    'shikharini': 'shikharini',
    # Shalini variants
    'salini': 'shalini',
    'shalini': 'shalini',
    # Rathoddhataa variants
    'rathoddhata': 'rathoddhata',
    # Harini variants
    'harini': 'harini',
    # Pushpitagra variants
    'pushpitagra': 'pushpitagra',
    'puspita': 'pushpitagra',
    'pushpita': 'pushpitagra',
    # Vamshastha variants - normalized form
    'vamshastha': 'vamshastha',
    'vamshastham': 'vamshastha',
    'vamshasthavilam': 'vamshastha',
    'vamshasthavila': 'vamshastha',
    'vashasthavilam': 'vamshastha',  # ṁ → sh variant
    'vashastha': 'vamshastha',
    # Totaka variants
    'totaka': 'totaka',
    'totakam': 'totaka',
    # Udgata variants
    'udgata': 'udgata',
    'udgatam': 'udgata',
    # Others
    'drutavilambita': 'drutavilambita',
    'drutavilambitam': 'drutavilambita',
    'bhujangaprayata': 'bhujangaprayata',
    'bhujangaprayatam': 'bhujangaprayata',
    # Tunaka variants
    'tunaka': 'tunaka',
    'tunakam': 'tunaka',
    # Pancacamara variants
    'pancacamara': 'pancacamara',
    'pancacamaram': 'pancacamara',
    'panchacamara': 'pancacamara',
    'panchacamaram': 'pancacamara',
}


def normalize_meter_name(name):
    """Normalize meter name for comparison."""
    if not name:
        return ''

    # If Devanagari, transliterate to IAST first
    if any('\u0900' <= c <= '\u097f' for c in str(name)):
        name = transliterate(str(name), sanscript.DEVANAGARI, sanscript.IAST)

    # Convert to lowercase and remove diacritics
    name = str(name).lower()

    # Remove diacritics
    diacritic_map = {
        'ā': 'a',
        'ī': 'i',
        'ū': 'u',
        'ṛ': 'r',
        'ṝ': 'r',
        'ḷ': 'l',
        'ṅ': 'n',
        'ñ': 'n',
        'ṇ': 'n',
        'ṭ': 't',
        'ḍ': 'd',
        'ś': 'sh',
        'ṣ': 'sh',
        'ḥ': 'h',
        'ṃ': 'm',
        'ä': 'a',
        'ü': 'u',
        'ö': 'o',  # German-style umlauts
    }
    for src, dst in diacritic_map.items():
        name = name.replace(src, dst)

    # Remove non-alphanumeric
    name = re.sub(r'[^a-z0-9]', '', name)

    # Apply aliases
    return METER_ALIASES.get(name, name)


def meters_match(expected, predicted, allow_family=False):
    """Check if predicted meter matches expected."""
    exp_norm = normalize_meter_name(expected)
    pred_norm = normalize_meter_name(predicted)

    # Exact match
    if exp_norm == pred_norm:
        return True, 'exact'

    # Handle meter families
    if allow_family:
        # Upajati family - indravajra, upendravajra, and upajati are interchangeable
        upajati_family = {'indravajra', 'upendravajra', 'upajati'}
        if exp_norm in upajati_family and pred_norm in upajati_family:
            return True, 'family'

        # Udgata family
        udgata_family = {'udgata', 'anyavidhodgata'}
        if exp_norm in udgata_family and pred_norm in udgata_family:
            return True, 'family'

        # Pushpitagra / Aupacchandasika family (these are alternative names for same meter)
        pushpitagra_family = {'pushpitagra', 'aupacchandasika', 'aupacchandasik', 'aupacchandasikam'}
        if exp_norm in pushpitagra_family and pred_norm in pushpitagra_family:
            return True, 'family'

        # Sundari family
        sundari_family = {'sundari', 'viyogini'}
        if exp_norm in sundari_family and pred_norm in sundari_family:
            return True, 'family'

    return False, None


# ============================================================================
# Data Loaders
# ============================================================================


def load_our_dataset():
    """Load our dataset (page 1-47 chanda list - Sheet1.csv)"""
    csv_path = BACKEND_PATH / 'data' / 'page 1-47 chanda list - Sheet1.csv'

    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        found_header = False
        for row in reader:
            # Find the header row
            if not found_header:
                if row and 'Shloka' in str(row):
                    found_header = True
                continue

            # Parse data rows
            if len(row) >= 4:
                verse = row[0].strip() if row[0] else ''
                meter = row[3].strip() if row[3] else ''  # 'chanda' is at index 3

                if not meter or not verse:
                    continue
                if meter.lower() in ['chanda', 'shloka']:  # Skip header-like values
                    continue

                data.append({'verse': verse, 'expected_meter': meter})

    return data


def load_original_repo_corpora():
    """Load all evaluation corpora from original repo."""
    corpora = ['meghaduta', 'ramaraksha', 'rajendrakarnapura', 'shantavilasa']
    eval_path = ORIGINAL_REPO_PATH / 'experiments' / 'evaluation'

    all_data = []
    corpus_stats = {}

    for corpus in corpora:
        corpus_path = eval_path / corpus
        answers_file = corpus_path / 'answers.txt'
        verses_file = corpus_path / f'{corpus}.wikisource.clean.txt'

        if not answers_file.exists() or not verses_file.exists():
            print(f"Skipping {corpus}: files not found")
            continue

        # Load answers
        with open(answers_file, 'r', encoding='utf-8') as f:
            answers = [line.strip() for line in f if line.strip()]

        # Load verses (separated by blank lines)
        with open(verses_file, 'r', encoding='utf-8') as f:
            content = f.read()
        verses = [v.strip() for v in content.split('\n\n') if v.strip()]

        # Pair answers with verses
        corpus_data = []
        for _i, (answer, verse) in enumerate(zip(answers, verses, strict=False)):
            # Handle multiple expected meters (e.g., "उपेन्द्रवज्रा + इन्द्रवज्रा")
            expected = answer.split(' + ')
            corpus_data.append(
                {
                    'verse': verse,
                    'expected_meter': expected[0],  # Primary expected meter
                    'all_expected': expected,
                    'corpus': corpus,
                }
            )

        all_data.extend(corpus_data)
        corpus_stats[corpus] = len(corpus_data)
        print(f"  {corpus}: {len(corpus_data)} verses")

    return all_data, corpus_stats


# ============================================================================
# Model Evaluators
# ============================================================================


def evaluate_with_chanda_iitk(data, data_path, label=""):
    """Evaluate using chanda_iitk.py with a specified meter database"""
    from reference.alternative_implementations.chanda_iitk import Chanda

    c = Chanda(str(data_path))

    correct = 0
    total = 0
    results = []

    for item in data:
        verse = item['verse']
        expected = item['expected_meter']
        all_expected = item.get('all_expected', [expected])

        try:
            result = c.identify_from_text(verse, verse=True, fuzzy=True)

            verse_results = result['result']['verse']
            if verse_results and verse_results[0].get('chanda'):
                predicted_list = verse_results[0]['chanda'][0]
                predicted = predicted_list[0] if predicted_list else ''
            else:
                predicted = ''

            is_correct = False
            for exp in all_expected:
                match, _ = meters_match(exp, predicted, allow_family=True)
                if match:
                    is_correct = True
                    break

            if is_correct:
                correct += 1

            total += 1
            results.append({'verse': verse[:50], 'expected': expected, 'predicted': predicted, 'correct': is_correct})

        except Exception as e:
            total += 1
            results.append({'verse': verse[:50], 'expected': expected, 'predicted': f'ERROR: {e}', 'correct': False})

    return correct, total, results


def evaluate_with_enhanced_chanda(data, data_path):
    """Evaluate using enhanced_chanda.py with our meter database"""
    from backend.core.enhanced_chanda import EnhancedChanda

    c = EnhancedChanda(str(data_path))

    correct = 0
    total = 0
    results = []

    for item in data:
        verse = item['verse']
        expected = item['expected_meter']
        all_expected = item.get('all_expected', [expected])

        try:
            result = c.identify_from_text(verse, verse=True, fuzzy=True)

            verse_results = result['result']['verse']
            if verse_results and verse_results[0].get('chanda'):
                predicted_list = verse_results[0]['chanda'][0]
                predicted = predicted_list[0] if predicted_list else ''
            else:
                predicted = ''

            is_correct = False
            for exp in all_expected:
                match, _ = meters_match(exp, predicted, allow_family=True)
                if match:
                    is_correct = True
                    break

            if is_correct:
                correct += 1

            total += 1
            results.append({'verse': verse[:50], 'expected': expected, 'predicted': predicted, 'correct': is_correct})

        except Exception as e:
            total += 1
            results.append({'verse': verse[:50], 'expected': expected, 'predicted': f'ERROR: {e}', 'correct': False})

    return correct, total, results


def evaluate_with_our_chanda(data, data_path):
    """Evaluate using our backend/core/chanda.py with our meter database"""
    from backend.core.chanda import Chanda

    c = Chanda(str(data_path))

    correct = 0
    total = 0
    results = []

    for item in data:
        verse = item['verse']
        expected = item['expected_meter']
        all_expected = item.get('all_expected', [expected])

        try:
            result = c.identify_from_text(verse, verse=True, fuzzy=True)

            verse_results = result['result']['verse']
            if verse_results and verse_results[0].get('chanda'):
                predicted_list = verse_results[0]['chanda'][0]
                predicted = predicted_list[0] if predicted_list else ''
            else:
                predicted = ''

            is_correct = False
            for exp in all_expected:
                match, _ = meters_match(exp, predicted, allow_family=True)
                if match:
                    is_correct = True
                    break

            if is_correct:
                correct += 1

            total += 1
            results.append({'verse': verse[:50], 'expected': expected, 'predicted': predicted, 'correct': is_correct})

        except Exception as e:
            total += 1
            results.append({'verse': verse[:50], 'expected': expected, 'predicted': f'ERROR: {e}', 'correct': False})

    return correct, total, results


# ============================================================================
# Main Comparison
# ============================================================================


def main():
    print("=" * 80)
    print("DATASET vs ALGORITHM COMPARISON")
    print("=" * 80)
    print("""
Comparing different implementations and datasets:

Test Data: page 1-47 chanda list - Sheet1.csv (109 verses)

Configurations:
1. chanda_iitk.py + ORIGINAL IITK dataset (baseline - original system)
2. chanda.py (backend/core) + OUR curated 1920 dataset (our system)
3. enhanced_chanda.py + OUR curated 1920 dataset (experimental)

NOTE: chanda_iitk.py + OUR large dataset is too slow due to regex matching.
      Our chanda.py has optimizations that handle the larger dataset efficiently.
""")

    # Define paths
    OUR_DATA_PATH = BACKEND_PATH / 'data'
    IITK_DATA_PATH = ORIGINAL_REPO_PATH / 'data'

    # Load test data
    test_data = load_our_dataset()
    print(f"Loaded {len(test_data)} test verses from page 1-47 chanda list")

    # Count meters in each database
    print("\n" + "-" * 60)
    print("METER DATABASE COMPARISON")
    print("-" * 60)

    # Count our meters
    our_meter_count = 0
    for csv_file in OUR_DATA_PATH.glob('chanda_*.csv'):
        with open(csv_file, 'r', encoding='utf-8') as f:
            our_meter_count += sum(1 for line in f if line.strip()) - 1  # minus header

    # Count IITK meters
    iitk_meter_count = 0
    for csv_file in IITK_DATA_PATH.glob('chanda_*.csv'):
        with open(csv_file, 'r', encoding='utf-8') as f:
            iitk_meter_count += sum(1 for line in f if line.strip()) - 1  # minus header

    print(f"Our curated dataset:    {our_meter_count:5d} meter patterns")
    print(f"Original IITK dataset:  {iitk_meter_count:5d} meter patterns")
    print(
        f"Improvement: {our_meter_count - iitk_meter_count:+d} patterns ({(our_meter_count / iitk_meter_count - 1) * 100:.1f}% more)"
    )

    # ========================================================================
    # Run evaluations
    # ========================================================================
    print("\n" + "=" * 80)
    print("RUNNING EVALUATIONS")
    print("=" * 80)

    results_summary = {}

    # 1. chanda_iitk.py + IITK original dataset (BASELINE)
    print("\n[1/3] BASELINE: chanda_iitk.py + ORIGINAL IITK dataset...")
    correct1, total1, results1 = evaluate_with_chanda_iitk(test_data, IITK_DATA_PATH, "iitk+iitk")
    acc1 = (correct1 / total1 * 100) if total1 > 0 else 0
    results_summary['baseline'] = {'correct': correct1, 'total': total1, 'acc': acc1, 'results': results1}
    print(f"    Result: {correct1}/{total1} = {acc1:.1f}%")

    # 2. chanda.py (our core) + OUR dataset
    print("\n[2/3] OUR SYSTEM: chanda.py (backend/core) + OUR curated dataset...")
    correct2, total2, results2 = evaluate_with_our_chanda(test_data, OUR_DATA_PATH)
    acc2 = (correct2 / total2 * 100) if total2 > 0 else 0
    results_summary['our_system'] = {'correct': correct2, 'total': total2, 'acc': acc2, 'results': results2}
    print(f"    Result: {correct2}/{total2} = {acc2:.1f}%")

    # 3. enhanced_chanda.py + OUR dataset
    print("\n[3/3] EXPERIMENTAL: enhanced_chanda.py + OUR curated dataset...")
    try:
        correct3, total3, results3 = evaluate_with_enhanced_chanda(test_data, OUR_DATA_PATH)
        acc3 = (correct3 / total3 * 100) if total3 > 0 else 0
        results_summary['enhanced'] = {'correct': correct3, 'total': total3, 'acc': acc3, 'results': results3}
        print(f"    Result: {correct3}/{total3} = {acc3:.1f}%")
    except Exception as e:
        print(f"    Error: {e}")
        acc3 = 0
        correct3, total3 = 0, 0
        results3 = []

    # ========================================================================
    # Summary Table
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY RESULTS")
    print("=" * 80)

    print("\n+--------------------------------------------------+----------+----------+")
    print("| Configuration                                    | Correct  | Accuracy |")
    print("+--------------------------------------------------+----------+----------+")
    print(f"| 1. BASELINE: chanda_iitk + IITK dataset          | {correct1:3d}/{total1:3d}  | {acc1:6.1f}%  |")
    print(f"| 2. OUR SYSTEM: chanda.py + OUR curated dataset   | {correct2:3d}/{total2:3d}  | {acc2:6.1f}%  |")
    if acc3 > 0:
        print(f"| 3. EXPERIMENTAL: enhanced_chanda + OUR dataset   | {correct3:3d}/{total3:3d}  | {acc3:6.1f}%  |")
    print("+--------------------------------------------------+----------+----------+")

    # Improvement
    improvement = acc2 - acc1
    print("\n📊 KEY METRICS:")
    print(f"   BASELINE (original IITK):     {acc1:.1f}%")
    print(f"   OUR SYSTEM (enhanced):        {acc2:.1f}%")
    print(f"   IMPROVEMENT:                  {improvement:+.1f}%")
    print(f"   Dataset size increase:        {our_meter_count - iitk_meter_count:+d} patterns")

    # ========================================================================
    # Show errors
    # ========================================================================
    print("\n" + "=" * 80)
    print("ERROR ANALYSIS")
    print("=" * 80)

    # Baseline errors
    errors1 = [r for r in results1 if not r['correct']]
    print(f"\n--- BASELINE errors ({len(errors1)} total) ---")
    for e in errors1[:10]:
        print(f"  Expected: {e['expected']:<25} Got: {e['predicted']}")

    # Our system errors
    errors2 = [r for r in results2 if not r['correct']]
    print(f"\n--- OUR SYSTEM errors ({len(errors2)} total) ---")
    if errors2:
        for e in errors2[:10]:
            print(f"  Expected: {e['expected']:<25} Got: {e['predicted']}")
    else:
        print("  ✅ No errors!")

    # What we fixed
    if errors1 and errors2:
        fixed = set(r['expected'] for r in errors1) - set(r['expected'] for r in errors2)
        if fixed:
            print(f"\n✅ METERS WE FIXED (now correct): {fixed}")


if __name__ == '__main__':
    main()
