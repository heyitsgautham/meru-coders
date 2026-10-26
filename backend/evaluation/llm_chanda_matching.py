"""Meter-name matching and the test-data loader for llm_chanda_prediction.py."""

import csv
import random
import unicodedata
from typing import Dict, List, Optional, Tuple

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


def to_iast(text: str) -> str:
    """Convert Devanagari to IAST."""
    try:
        return transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
    except Exception:
        return text


def normalize(name: str) -> str:
    """Normalize meter name for comparison."""
    if not name:
        return ""
    name = name.lower().strip()
    name = to_iast(name)
    name = unicodedata.normalize('NFD', name)
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))
    # Remove common suffixes and variations
    for suffix in ['m', 'h', 'am', 'a', 'ā']:
        if name.endswith(suffix) and len(name) > len(suffix) + 2:
            name = name[: -len(suffix)]
            break
    return name.strip()


# Meter family mappings for flexible matching
METER_FAMILIES = {
    # Anuṣṭup family
    'anustup': 'anustubh',
    'anustubh': 'anustubh',
    'sloka': 'anustubh',
    # Śārdūlavikrīḍita family
    'sardulavkridita': 'sardula',
    'sardulavikriditam': 'sardula',
    'sardulavikridita': 'sardula',
    'sardula': 'sardula',
    'shardulavikridita': 'sardula',
    'saardulavikriidita': 'sardula',
    # Mandākrāntā family
    'mandakranta': 'mandakranta',
    'mandaakraantaa': 'mandakranta',
    # Vasantatilakā family
    'vasantatilaka': 'vasantatilaka',
    'vasantatilakam': 'vasantatilaka',
    # Bhujangaprayāta family
    'bhujangaprayata': 'bhujangaprayata',
    'bhujangaprayatam': 'bhujangaprayata',
    # Upajāti family
    'upajati': 'upajati',
    'upajatih': 'upajati',
    'indravajra': 'upajati',
    'upendravajra': 'upajati',
    # Drutavilaṃbita family
    'drutavilambita': 'drutavilambita',
    'drutavilambitam': 'drutavilambita',
    # Sragdharā family
    'sragdhara': 'sragdhara',
    'sragdharaa': 'sragdhara',
    # Śikhariṇī family
    'sikharini': 'sikharini',
    'sikharina': 'sikharini',
    # Mālinī family
    'malini': 'malini',
    'maalini': 'malini',
}


def get_family(name: str) -> str:
    """Get the meter family for flexible matching."""
    normalized = normalize(name)
    return METER_FAMILIES.get(normalized, normalized)


def load_test_data(csv_path: str, num_samples: Optional[int] = None) -> List[Dict]:
    """
    Load test verses from CSV file.

    Args:
        csv_path: Path to the CSV file
        num_samples: Number of samples to load (None for all)

    Returns:
        List of dictionaries with 'verse' and 'expected_meter' keys
    """
    test_data = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Skip header rows (first 2 rows)
    for row in rows[2:]:
        if len(row) >= 4:
            verse = row[0].strip()
            expected_meter = row[3].strip()

            # Skip empty verses or meters
            if verse and expected_meter and len(verse) > 10:
                test_data.append({'verse': verse, 'expected_meter': expected_meter})

    # Sample if requested
    if num_samples and num_samples < len(test_data):
        test_data = random.sample(test_data, num_samples)

    return test_data


def compare_meters(predicted: str, expected: str) -> Tuple[bool, str]:
    """
    Compare predicted and expected meter names.

    Returns:
        Tuple of (is_match, match_type)
        match_type: 'exact', 'normalized', 'family', or 'no_match'
    """
    if not predicted:
        return False, 'no_prediction'

    # Exact match (case-insensitive)
    if predicted.lower() == expected.lower():
        return True, 'exact'

    # Normalized match
    pred_norm = normalize(predicted)
    exp_norm = normalize(expected)

    if pred_norm == exp_norm:
        return True, 'normalized'

    # Family match
    pred_family = get_family(predicted)
    exp_family = get_family(expected)

    if pred_family == exp_family:
        return True, 'family'

    # Partial match (one contains the other)
    if pred_norm in exp_norm or exp_norm in pred_norm:
        return True, 'partial'

    return False, 'no_match'
