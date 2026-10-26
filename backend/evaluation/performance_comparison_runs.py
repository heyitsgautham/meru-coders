"""The four accuracy runs performance_comparison.py reports: IITK and our engine, each on the Rigveda and classical lists."""

import time

from backend.evaluation.performance_comparison_data import (
    PAGE_CSV,
    RIGVEDA_CSV,
    csv_meters_match,
    load_csv_dataset,
    load_rigveda_dataset,
    rigveda_meters_match,
)


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
