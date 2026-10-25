#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Performance Comparison Test

Compares:
1. chanda_iitk.py (original IITK implementation) with small dataset against Rigveda validation
2. chanda_iitk.py with our large dataset against Rigveda validation
3. chanda_iitk.py with small dataset against CSV accuracy test
4. chanda_iitk.py with large dataset against CSV accuracy test
5. chanda.py (our implementation) with large dataset against Rigveda validation
6. chanda.py with large dataset against CSV accuracy test

@author: GitHub Copilot
@date: 2025-12-05
"""

import csv
import os
import sys
import time
import unicodedata

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ============================================================================
# CONSTANTS AND PATHS
# ============================================================================

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)

# Dataset paths
SMALL_DATA_PATH = os.path.join(ROOT_DIR, 'repos', 'chanda', 'data')
LARGE_DATA_PATH = os.path.join(BACKEND_DIR, 'data')

# Test data paths
RIGVEDA_CSV = os.path.join(LARGE_DATA_PATH, 'rigveda_with_meters_complete.csv')
PAGE_CSV = os.path.join(LARGE_DATA_PATH, 'page 1-47 chanda list - complete.csv')


# ============================================================================
# METER NAME NORMALIZATION (from test_rigveda_validation.py)
# ============================================================================

METER_NORMALIZATION = {
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
    'jagatiī': 'जगती',
    'virāṭ': 'विराट्',
    'virat': 'विराट्',
    'pragāthaḥ': 'प्रगाथ',
    'pragātha': 'प्रगाथ',
    'mahāpaṅktiḥ': 'महापङ्क्ति',
    'mahāpaṅkti': 'महापङ्क्ति',
    'atyaṣṭiḥ': 'अत्यष्टि',
    'atyaṣṭi': 'अत्यष्टि',
    'atyaṣtiḥ': 'अत्यष्टि',
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
    'dvipadā virāṭ': 'द्विपदा विराट्',
    'dvipadā triṣṭup': 'द्विपदा त्रिष्टुभ्',
    'dvipadā': 'द्विपदा',
}

METER_FAMILIES = {
    'गायत्री': ['गायत्री', 'निचृद्गायत्री', 'भुरिग्गायत्री'],
    'उष्णिक्': ['उष्णिक्', 'पुर उष्णिक्', 'ककुभ्'],
    'अनुष्टुभ्': ['अनुष्टुभ्', 'श्लोक'],
    'बृहती': ['बृहती', 'महाबृहती', 'प्रगाथ', 'पङ्क्ति'],
    'पङ्क्ति': ['पङ्क्ति', 'महापङ्क्ति', 'प्रस्तारपङ्क्ति', 'प्रगाथ', 'बृहती'],
    'त्रिष्टुभ्': ['त्रिष्टुभ्', 'द्विपदा त्रिष्टुभ्', 'निचृत् त्रिष्टुभ्'],
    'जगती': ['जगती', 'अतिजगती', 'निचृत् जगती', 'ज्योतिस्'],
    'विराट्': ['विराट्', 'द्विपदा विराट्'],
    'ककुभ्': ['ककुभ्', 'उष्णिक्'],
}

COMPOSITE_METERS = {
    'प्रगाथ': ['बृहती', 'पङ्क्ति', 'सतोबृहती', 'उष्णिक्', 'अनुष्टुभ्', 'प्रगाथ', 'त्रिष्टुभ्', 'जगती'],
    'विराट्': ['विराट्', 'उष्णिक्', 'बृहती', 'पङ्क्ति', 'त्रिष्टुभ्', 'गायत्री', 'अनुष्टुभ्', 'द्विपदा त्रिष्टुभ्', 'जगती'],
    'द्विपदा विराट्': ['विराट्', 'गायत्री', 'द्विपदा विराट्', 'उष्णिक्'],
    'द्विपदा त्रिष्टुभ्': ['त्रिष्टुभ्', 'पङ्क्ति', 'द्विपदा त्रिष्टुभ्', 'गायत्री'],
    'महापङ्क्ति': ['पङ्क्ति', 'जगती', 'त्रिष्टुभ्', 'महापङ्क्ति'],
    'ज्योतिस्': ['जगती', 'त्रिष्टुभ्', 'पङ्क्ति', 'ज्योतिस्'],
    'ककुभ्': ['ककुभ्', 'उष्णिक्', 'बृहती', 'अनुष्टुभ्'],
    'बृहती': ['बृहती', 'पङ्क्ति', 'प्रगाथ', 'अनुष्टुभ्', 'उष्णिक्'],
    'पङ्क्ति': ['पङ्क्ति', 'बृहती', 'प्रगाथ', 'त्रिष्टुभ्'],
    'जगती': ['जगती', 'त्रिष्टुभ्', 'अतिजगती'],
    'त्रिष्टुभ्': ['त्रिष्टुभ्', 'जगती', 'पङ्क्ति'],
    'अत्यष्टि': ['अत्यष्टि', 'जगती', 'त्रिष्टुभ्'],
    'अष्टि': ['अष्टि', 'जगती', 'त्रिष्टुभ्'],
    'अतिजगती': ['अतिजगती', 'जगती', 'त्रिष्टुभ्'],
    'शक्वरी': ['शक्वरी', 'जगती', 'त्रिष्टुभ्'],
    'अतिशक्वरी': ['अतिशक्वरी', 'जगती'],
}


# ============================================================================
# CSV ACCURACY TEST FAMILIES (from test_csv_accuracy.py)
# ============================================================================

CSV_METER_FAMILIES = {
    'anustup': 'anustubh',
    'anustubh': 'anustubh',
    'rsabhagajavilasita': 'anustubh',
    'pythvi': 'prthvi',
    'prthvi': 'prthvi',
    'prthi': 'prthvi',
    'sardulavkridita': 'sardula',
    'sardulavikriditam': 'sardula',
    'sardulavikridita': 'sardula',
    'meghavisphurjita': 'sardula',
    'sardulalaltiam': 'sardula',
    'upajatih': 'upajati',
    'upajati': 'upajati',
    'indravajra': 'upajati',
    'upendravajra': 'upajati',
    'ihamrgi': 'upajati',
    'sumukhi': 'upajati',
    'vamsasthavilam': 'vamsastha',
    'vamsasthavila': 'vamsastha',
    'vamsastha': 'vamsastha',
    'indravamsa': 'vamsastha',
    'bhujangaprayatam': 'vamsastha',
    'bhujangaprayata': 'vamsastha',
    'candravartma': 'vamsastha',
    'vasantatilakam': 'vasantatilaka',
    'vasantatilaka': 'vasantatilaka',
    'tunaka': 'tunaka',
    'camara': 'tunaka',
    'tunakam': 'tunaka',
    'pancacamaram': 'pancacamara',
    'pancacamara': 'pancacamara',
    'srih': 'nari',
    'stri': 'nari',
    'nari': 'nari',
    'sragdhara': 'sragdhara',
    'pancakavali': 'sragdhara',
    'mandakranta': 'mandakranta',
    'atisayini': 'mandakranta',
    'praharsini': 'praharsini',
    'kalahamsa': 'praharsini',
    'bhujangasangata': 'bhujanga',
    'bhujagasisubhrta': 'bhujanga',
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def normalize_rigveda_meter(name):
    """Normalize meter name from IAST to Devanagari for Rigveda tests"""
    if not name:
        return None
    name = name.strip().lower()
    if name.startswith('('):
        return None
    if name in METER_NORMALIZATION:
        return METER_NORMALIZATION[name]
    simple_name = (
        name.replace('ṭ', 't')
        .replace('ṣ', 's')
        .replace('ṇ', 'n')
        .replace('ī', 'i')
        .replace('ā', 'a')
        .replace('ṛ', 'r')
        .replace('ṅ', 'n')
        .replace('ḥ', 'h')
    )
    for key, value in METER_NORMALIZATION.items():
        simple_key = (
            key.replace('ṭ', 't')
            .replace('ṣ', 's')
            .replace('ṇ', 'n')
            .replace('ī', 'i')
            .replace('ā', 'a')
            .replace('ṛ', 'r')
            .replace('ṅ', 'n')
            .replace('ḥ', 'h')
        )
        if simple_name == simple_key:
            return value
    return None


def to_iast(text):
    """Convert Devanagari to IAST"""
    try:
        return transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
    except Exception:
        return text


def normalize_csv_meter(name):
    """Normalize meter name for CSV accuracy comparison"""
    name = name.lower().strip()
    name = to_iast(name)
    name = unicodedata.normalize('NFD', name)
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))
    return name


def get_csv_family(name):
    """Get meter family for CSV comparison"""
    norm = normalize_csv_meter(name)
    return CSV_METER_FAMILIES.get(norm, norm)


def rigveda_meters_match(expected, predicted):
    """Check if two meter names match for Rigveda validation"""
    if not expected or not predicted:
        return False, False
    if expected == predicted:
        return True, True
    if expected in COMPOSITE_METERS:
        if predicted in COMPOSITE_METERS[expected]:
            return False, True
    for _family, members in METER_FAMILIES.items():
        if expected in members and predicted in members:
            return False, True
    return False, False


def csv_meters_match(expected, predicted):
    """Check if two meter names match for CSV accuracy"""
    exp_fam = get_csv_family(expected)
    pred_fam = get_csv_family(predicted)
    if exp_fam == pred_fam:
        return True
    if exp_fam in pred_fam or pred_fam in exp_fam:
        return True
    return False


def load_rigveda_dataset(filepath, limit=None):
    """Load Rigveda dataset"""
    data = []
    errors = []

    if not os.path.exists(filepath):
        return data, [f"File not found: {filepath}"]

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                verse_text = row.get('verse_text', '').strip()
                meter_raw = row.get('meter', '').strip()
                ref = row.get('ref', f'row_{row_num}').strip()

                if not verse_text or not meter_raw:
                    continue

                expected_meter = normalize_rigveda_meter(meter_raw)
                if not expected_meter:
                    errors.append(f"Row {row_num}: Unknown meter '{meter_raw}'")
                    continue

                data.append({'verse_text': verse_text, 'expected_meter': expected_meter, 'ref': ref})

                if limit and len(data) >= limit:
                    break

            except Exception as e:
                errors.append(f"Row {row_num}: {e}")

    return data, errors


def load_csv_dataset(filepath, limit=147):
    """Load CSV accuracy test dataset (first 147 real verses)"""
    data = []

    if not os.path.exists(filepath):
        return data

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    row_index = 0
    for row in rows:
        if len(row) >= 4:
            verse = row[0].strip()
            expected = row[3].strip()

            if not verse or expected.lower() == 'chanda':
                continue

            row_index += 1
            if row_index > limit:
                break

            data.append({'verse': verse, 'expected': expected, 'row_index': row_index})

    return data


# ============================================================================
# TEST RUNNERS
# ============================================================================


def test_rigveda_with_iitk(chanda_class, data_path, limit=1000):
    """Test IITK Chanda implementation against Rigveda dataset"""

    # Initialize Chanda
    try:
        chanda = chanda_class(data_path=data_path)
    except Exception as e:
        return {
            'error': f"Failed to initialize: {e}",
            'total': 0,
            'exact_matches': 0,
            'family_matches': 0,
            'mismatches': 0,
            'exact_accuracy': 0,
            'family_accuracy': 0,
        }

    # Load Rigveda dataset
    data, parse_errors = load_rigveda_dataset(RIGVEDA_CSV, limit=limit)

    if not data:
        return {
            'error': f"No data loaded. Errors: {parse_errors[:5]}",
            'total': 0,
            'exact_matches': 0,
            'family_matches': 0,
            'mismatches': 0,
            'exact_accuracy': 0,
            'family_accuracy': 0,
        }

    total = len(data)
    exact_matches = 0
    family_matches = 0
    mismatches = 0

    start_time = time.time()

    for entry in data:
        verse_text = entry['verse_text']
        expected_meter = entry['expected_meter']

        # Get prediction using IITK's identify_line
        try:
            result = chanda.identify_line(verse_text)
            predicted_meter = None

            if result.get('found') and result.get('chanda'):
                first_chanda = result['chanda'][0]
                if isinstance(first_chanda, tuple):
                    predicted_meter = first_chanda[0]
                else:
                    predicted_meter = first_chanda

            # Check match
            exact, family = rigveda_meters_match(expected_meter, predicted_meter)

            if exact:
                exact_matches += 1
            elif family:
                family_matches += 1
            else:
                mismatches += 1

        except Exception:
            mismatches += 1

    elapsed_time = time.time() - start_time

    exact_accuracy = (exact_matches / total * 100) if total > 0 else 0
    family_accuracy = ((exact_matches + family_matches) / total * 100) if total > 0 else 0

    return {
        'total': total,
        'exact_matches': exact_matches,
        'family_matches': family_matches,
        'mismatches': mismatches,
        'exact_accuracy': exact_accuracy,
        'family_accuracy': family_accuracy,
        'time_seconds': elapsed_time,
        'time_per_verse_ms': (elapsed_time / total * 1000) if total > 0 else 0,
    }


def test_csv_with_iitk(chanda_class, data_path):
    """Test IITK Chanda implementation against CSV accuracy test"""

    # Initialize Chanda
    try:
        chanda = chanda_class(data_path=data_path)
    except Exception as e:
        return {
            'error': f"Failed to initialize: {e}",
            'total': 0,
            'correct': 0,
            'incorrect': 0,
            'accuracy': 0,
        }

    # Load CSV dataset
    data = load_csv_dataset(PAGE_CSV)

    if not data:
        return {
            'error': "No data loaded",
            'total': 0,
            'correct': 0,
            'incorrect': 0,
            'accuracy': 0,
        }

    total = len(data)
    correct = 0
    incorrect = 0

    start_time = time.time()

    for entry in data:
        verse = entry['verse']
        expected = entry['expected']

        try:
            # Use identify_from_text for line-level analysis
            result = chanda.identify_from_text(verse, verse=False)

            predicted = None
            if result and 'result' in result and result['result'].get('line'):
                first_line = result['result']['line'][0]
                if first_line and 'result' in first_line and first_line['result'].get('chanda'):
                    first_chanda = first_line['result']['chanda'][0]
                    if isinstance(first_chanda, tuple):
                        predicted = first_chanda[0]
                    else:
                        predicted = first_chanda

            if predicted and csv_meters_match(expected, predicted):
                correct += 1
            else:
                incorrect += 1

        except Exception:
            incorrect += 1

    elapsed_time = time.time() - start_time

    accuracy = (correct / total * 100) if total > 0 else 0

    return {
        'total': total,
        'correct': correct,
        'incorrect': incorrect,
        'accuracy': accuracy,
        'time_seconds': elapsed_time,
        'time_per_verse_ms': (elapsed_time / total * 1000) if total > 0 else 0,
    }


def test_rigveda_with_our_chanda(limit=1000):
    """Test our Chanda implementation against Rigveda dataset"""

    from backend.config import settings
    from backend.core import Chanda

    # Initialize Chanda
    try:
        chanda = Chanda(data_path=str(settings.DATA_DIR))
    except Exception as e:
        return {
            'error': f"Failed to initialize: {e}",
            'total': 0,
            'exact_matches': 0,
            'family_matches': 0,
            'mismatches': 0,
            'exact_accuracy': 0,
            'family_accuracy': 0,
        }

    # Load Rigveda dataset
    data, parse_errors = load_rigveda_dataset(RIGVEDA_CSV, limit=limit)

    if not data:
        return {
            'error': f"No data loaded. Errors: {parse_errors[:5]}",
            'total': 0,
            'exact_matches': 0,
            'family_matches': 0,
            'mismatches': 0,
            'exact_accuracy': 0,
            'family_accuracy': 0,
        }

    total = len(data)
    exact_matches = 0
    family_matches = 0
    mismatches = 0

    start_time = time.time()

    for entry in data:
        verse_text = entry['verse_text']
        expected_meter = entry['expected_meter']

        try:
            # Use _identify_vedic_mode for Vedic texts
            result = chanda._identify_vedic_mode(verse_text)
            predicted_meter = result.get('meter')

            # Also try standard identification
            if not predicted_meter:
                line_result = chanda.identify_line(verse_text)
                if line_result.get('found') and line_result.get('chanda'):
                    first_chanda = line_result['chanda'][0]
                    if isinstance(first_chanda, tuple):
                        predicted_meter = first_chanda[0]
                    else:
                        predicted_meter = first_chanda

            # Check match
            exact, family = rigveda_meters_match(expected_meter, predicted_meter)

            if exact:
                exact_matches += 1
            elif family:
                family_matches += 1
            else:
                mismatches += 1

        except Exception:
            mismatches += 1

    elapsed_time = time.time() - start_time

    exact_accuracy = (exact_matches / total * 100) if total > 0 else 0
    family_accuracy = ((exact_matches + family_matches) / total * 100) if total > 0 else 0

    return {
        'total': total,
        'exact_matches': exact_matches,
        'family_matches': family_matches,
        'mismatches': mismatches,
        'exact_accuracy': exact_accuracy,
        'family_accuracy': family_accuracy,
        'time_seconds': elapsed_time,
        'time_per_verse_ms': (elapsed_time / total * 1000) if total > 0 else 0,
    }


def test_csv_with_our_chanda():
    """Test our Chanda implementation against CSV accuracy test"""

    from backend.config import settings
    from backend.core import Chanda

    # Initialize Chanda
    try:
        chanda = Chanda(data_path=str(settings.DATA_DIR))
    except Exception as e:
        return {
            'error': f"Failed to initialize: {e}",
            'total': 0,
            'correct': 0,
            'incorrect': 0,
            'accuracy': 0,
        }

    # Load CSV dataset
    data = load_csv_dataset(PAGE_CSV)

    if not data:
        return {
            'error': "No data loaded",
            'total': 0,
            'correct': 0,
            'incorrect': 0,
            'accuracy': 0,
        }

    total = len(data)
    correct = 0
    incorrect = 0

    start_time = time.time()

    for entry in data:
        verse = entry['verse']
        expected = entry['expected']

        try:
            # Use identify_from_text for line-level analysis
            result = chanda.identify_from_text(verse, verse=False)

            predicted = None
            if result and 'result' in result and result['result'].get('line'):
                first_line = result['result']['line'][0]
                if first_line and 'result' in first_line and first_line['result'].get('chanda'):
                    first_chanda = first_line['result']['chanda'][0]
                    if isinstance(first_chanda, tuple):
                        predicted = first_chanda[0]
                    else:
                        predicted = first_chanda

            if predicted and csv_meters_match(expected, predicted):
                correct += 1
            else:
                incorrect += 1

        except Exception:
            incorrect += 1

    elapsed_time = time.time() - start_time

    accuracy = (correct / total * 100) if total > 0 else 0

    return {
        'total': total,
        'correct': correct,
        'incorrect': incorrect,
        'accuracy': accuracy,
        'time_seconds': elapsed_time,
        'time_per_verse_ms': (elapsed_time / total * 1000) if total > 0 else 0,
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def print_separator(char='=', length=70):
    print(char * length)


def print_results(title, results, test_type='rigveda'):
    """Print formatted results"""
    print(f"\n{title}")
    print_separator('-', len(title))

    if 'error' in results:
        print(f"  ❌ ERROR: {results['error']}")
        return

    if test_type == 'rigveda':
        print(f"  📊 Total verses tested:    {results['total']}")
        print(f"  ✅ Exact matches:          {results['exact_matches']} ({results['exact_accuracy']:.2f}%)")
        print(
            f"  🔶 Family matches:         {results['family_matches']} ({results['family_matches'] / results['total'] * 100:.2f}%)"
            if results['total'] > 0
            else ""
        )
        print(
            f"  ❌ Mismatches:             {results['mismatches']} ({results['mismatches'] / results['total'] * 100:.2f}%)"
            if results['total'] > 0
            else ""
        )
        print(f"  📈 EXACT ACCURACY:         {results['exact_accuracy']:.2f}%")
        print(f"  📈 FAMILY ACCURACY:        {results['family_accuracy']:.2f}%")
    else:  # csv
        print(f"  📊 Total verses tested:    {results['total']}")
        print(f"  ✅ Correct:                {results['correct']} ({results['accuracy']:.2f}%)")
        print(f"  ❌ Incorrect:              {results['incorrect']} ({100 - results['accuracy']:.2f}%)")
        print(f"  📈 ACCURACY:               {results['accuracy']:.2f}%")

    if 'time_seconds' in results:
        print(
            f"  ⏱️  Time:                   {results['time_seconds']:.2f}s ({results['time_per_verse_ms']:.2f}ms/verse)"
        )


def main():
    print_separator('=')
    print("🔬 COMPREHENSIVE PERFORMANCE COMPARISON")
    print("   Comparing chanda_iitk.py vs chanda.py implementations")
    print_separator('=')

    # Check if IITK implementation exists
    iitk_path = os.path.join(ROOT_DIR, 'reference', 'alternative_implementations', 'chanda_iitk.py')
    if not os.path.exists(iitk_path):
        print(f"❌ IITK implementation not found at: {iitk_path}")
        return 1

    # Import IITK Chanda
    import importlib.util

    spec = importlib.util.spec_from_file_location("chanda_iitk", iitk_path)
    chanda_iitk_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chanda_iitk_module)
    ChandaIITK = chanda_iitk_module.Chanda

    # Dataset info
    print("\n📁 Dataset Information:")
    print(f"   Small dataset (IITK original): {SMALL_DATA_PATH}")
    print(f"   Large dataset (Our enhanced):  {LARGE_DATA_PATH}")
    print(f"   Rigveda test file:             {RIGVEDA_CSV}")
    print(f"   CSV test file:                 {PAGE_CSV}")

    # Count meters in datasets
    small_count = 0
    large_count = 0
    for f in ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv']:
        small_file = os.path.join(SMALL_DATA_PATH, f)
        large_file = os.path.join(LARGE_DATA_PATH, f)
        if os.path.exists(small_file):
            small_count += sum(1 for _ in open(small_file)) - 1  # minus header
        if os.path.exists(large_file):
            large_count += sum(1 for _ in open(large_file)) - 1

    print(f"\n   Small dataset meter count:     ~{small_count} meters")
    print(f"   Large dataset meter count:     ~{large_count} meters")

    # Run all tests
    results = {}

    # 1. IITK + Small Dataset + Rigveda
    print_separator()
    print("\n🧪 Test 1: chanda_iitk.py + Small Dataset vs Rigveda Validation")
    results['iitk_small_rigveda'] = test_rigveda_with_iitk(ChandaIITK, SMALL_DATA_PATH, limit=1000)
    print_results("Results:", results['iitk_small_rigveda'], 'rigveda')

    # 2. IITK + Large Dataset + Rigveda
    print_separator()
    print("\n🧪 Test 2: chanda_iitk.py + Large Dataset vs Rigveda Validation")
    results['iitk_large_rigveda'] = test_rigveda_with_iitk(ChandaIITK, LARGE_DATA_PATH, limit=1000)
    print_results("Results:", results['iitk_large_rigveda'], 'rigveda')

    # 3. IITK + Small Dataset + CSV
    print_separator()
    print("\n🧪 Test 3: chanda_iitk.py + Small Dataset vs CSV Accuracy Test")
    results['iitk_small_csv'] = test_csv_with_iitk(ChandaIITK, SMALL_DATA_PATH)
    print_results("Results:", results['iitk_small_csv'], 'csv')

    # 4. IITK + Large Dataset + CSV
    print_separator()
    print("\n🧪 Test 4: chanda_iitk.py + Large Dataset vs CSV Accuracy Test")
    results['iitk_large_csv'] = test_csv_with_iitk(ChandaIITK, LARGE_DATA_PATH)
    print_results("Results:", results['iitk_large_csv'], 'csv')

    # 5. Our Chanda + Large Dataset + Rigveda
    print_separator()
    print("\n🧪 Test 5: chanda.py (Our) + Large Dataset vs Rigveda Validation")
    results['ours_large_rigveda'] = test_rigveda_with_our_chanda(limit=1000)
    print_results("Results:", results['ours_large_rigveda'], 'rigveda')

    # 6. Our Chanda + Large Dataset + CSV
    print_separator()
    print("\n🧪 Test 6: chanda.py (Our) + Large Dataset vs CSV Accuracy Test")
    results['ours_large_csv'] = test_csv_with_our_chanda()
    print_results("Results:", results['ours_large_csv'], 'csv')

    # Summary comparison
    print_separator('=')
    print("\n📊 SUMMARY COMPARISON TABLE")
    print_separator('=')

    print("\n┌─────────────────────────────────────────────────────────────────────────┐")
    print("│                    RIGVEDA VALIDATION RESULTS                            │")
    print("├─────────────────────────────────────────────────────────────────────────┤")
    print("│ Implementation          │ Dataset  │ Exact Acc  │ Family Acc │ Time/v   │")
    print("├─────────────────────────────────────────────────────────────────────────┤")

    def fmt_acc(r, key):
        if 'error' in r:
            return "ERROR"
        return f"{r[key]:.1f}%"

    def fmt_time(r):
        if 'error' in r or 'time_per_verse_ms' not in r:
            return "N/A"
        return f"{r['time_per_verse_ms']:.1f}ms"

    print(
        f"│ chanda_iitk.py          │ Small    │ {fmt_acc(results['iitk_small_rigveda'], 'exact_accuracy'):>10} │ {fmt_acc(results['iitk_small_rigveda'], 'family_accuracy'):>10} │ {fmt_time(results['iitk_small_rigveda']):>8} │"
    )
    print(
        f"│ chanda_iitk.py          │ Large    │ {fmt_acc(results['iitk_large_rigveda'], 'exact_accuracy'):>10} │ {fmt_acc(results['iitk_large_rigveda'], 'family_accuracy'):>10} │ {fmt_time(results['iitk_large_rigveda']):>8} │"
    )
    print(
        f"│ chanda.py (Ours)        │ Large    │ {fmt_acc(results['ours_large_rigveda'], 'exact_accuracy'):>10} │ {fmt_acc(results['ours_large_rigveda'], 'family_accuracy'):>10} │ {fmt_time(results['ours_large_rigveda']):>8} │"
    )
    print("└─────────────────────────────────────────────────────────────────────────┘")

    print("\n┌─────────────────────────────────────────────────────────────────────────┐")
    print("│                    CSV ACCURACY TEST RESULTS                             │")
    print("├─────────────────────────────────────────────────────────────────────────┤")
    print("│ Implementation          │ Dataset  │ Accuracy   │ Time/verse            │")
    print("├─────────────────────────────────────────────────────────────────────────┤")
    print(
        f"│ chanda_iitk.py          │ Small    │ {fmt_acc(results['iitk_small_csv'], 'accuracy'):>10} │ {fmt_time(results['iitk_small_csv']):>21} │"
    )
    print(
        f"│ chanda_iitk.py          │ Large    │ {fmt_acc(results['iitk_large_csv'], 'accuracy'):>10} │ {fmt_time(results['iitk_large_csv']):>21} │"
    )
    print(
        f"│ chanda.py (Ours)        │ Large    │ {fmt_acc(results['ours_large_csv'], 'accuracy'):>10} │ {fmt_time(results['ours_large_csv']):>21} │"
    )
    print("└─────────────────────────────────────────────────────────────────────────┘")

    # Analysis
    print("\n" + "=" * 70)
    print("📝 ANALYSIS")
    print("=" * 70)

    # Compare IITK small vs large
    if 'error' not in results['iitk_small_rigveda'] and 'error' not in results['iitk_large_rigveda']:
        diff = results['iitk_large_rigveda']['exact_accuracy'] - results['iitk_small_rigveda']['exact_accuracy']
        if diff > 0:
            print(f"✅ Larger dataset improves IITK accuracy by {diff:.1f}% on Rigveda")
        elif diff < 0:
            print(f"⚠️  Larger dataset decreases IITK accuracy by {abs(diff):.1f}% on Rigveda")
        else:
            print("➡️  Larger dataset has no effect on IITK accuracy on Rigveda")

    # Compare Our implementation vs IITK
    if 'error' not in results['ours_large_rigveda'] and 'error' not in results['iitk_large_rigveda']:
        diff = results['ours_large_rigveda']['exact_accuracy'] - results['iitk_large_rigveda']['exact_accuracy']
        if diff > 0:
            print(f"✅ Our implementation outperforms IITK by {diff:.1f}% on Rigveda (same dataset)")
        elif diff < 0:
            print(f"⚠️  Our implementation underperforms IITK by {abs(diff):.1f}% on Rigveda (same dataset)")
        else:
            print("➡️  Our implementation matches IITK on Rigveda (same dataset)")

    if 'error' not in results['ours_large_csv'] and 'error' not in results['iitk_large_csv']:
        diff = results['ours_large_csv']['accuracy'] - results['iitk_large_csv']['accuracy']
        if diff > 0:
            print(f"✅ Our implementation outperforms IITK by {diff:.1f}% on CSV test (same dataset)")
        elif diff < 0:
            print(f"⚠️  Our implementation underperforms IITK by {abs(diff):.1f}% on CSV test (same dataset)")
        else:
            print("➡️  Our implementation matches IITK on CSV test (same dataset)")

    print("\n" + "=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
