"""Reads the WSC 2023 Anukramani meter annotations and matches meter names for wsc2023_validation.py."""

import os
import re
import unicodedata


def normalize_meter_name(name):
    """
    Normalize meter name for comparison.
    Handles IAST diacritics, case, and common variants.
    """
    if not name:
        return ""

    # Handle tuples (meter name, details) - extract just the name
    if isinstance(name, tuple):
        name = name[0] if name else ""

    if not isinstance(name, str):
        name = str(name)

    name = name.lower().strip()

    # Unicode normalization - remove diacritics
    name = unicodedata.normalize('NFD', name)
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))

    # Remove trailing 'h' for visarga variants (except known meters ending in h)
    keep_h = ['tristubh', 'anustubh', 'kakubh']
    if name.endswith('h') and name not in keep_h and len(name) > 3:
        name = name[:-1]

    # Normalize common variants
    normalizations = {
        'tristup': 'tristubh',
        'anustup': 'anustubh',
        'panktih': 'pankti',
        'brhati': 'brhati',
        'brihati': 'brhati',
        'usnik': 'usnik',
        'gayatri': 'gayatri',
        'jagati': 'jagati',
        'jagatii': 'jagati',
        'virat': 'virat',
        'viraj': 'virat',
    }

    return normalizations.get(name, name)


# Mapping from Anukramani meter names to our canonical names
CANONICAL_METERS = {
    # 7 Major Vedic Meters
    'gayatri': 'gayatri',
    'usnik': 'usnik',
    'anustubh': 'anustubh',
    'anustup': 'anustubh',
    'tristubh': 'tristubh',
    'tristup': 'tristubh',
    'jagati': 'jagati',
    'jagatii': 'jagati',
    'brhati': 'brhati',
    'brihati': 'brhati',
    'pankti': 'pankti',
    'panktih': 'pankti',
    # Extended Vedic Meters
    'virat': 'virat',
    'viraj': 'virat',
    'kakup': 'kakup',
    'kakubh': 'kakup',
    'atyasti': 'atyasti',
    'atyastih': 'atyasti',
    'asti': 'asti',
    'astih': 'asti',
    'dhrti': 'dhrti',
    'adhrti': 'adhrti',
    'atisakvari': 'atisakvari',
    'sakvari': 'sakvari',
    'pragatha': 'pragatha',
    'pragathah': 'pragatha',
    'atijagati': 'atijagati',
    'mahapankti': 'mahapankti',
    'mahapanktih': 'mahapankti',
    'mahabrhati': 'mahabrhati',
}


def get_canonical_form(meter_name):
    """Get canonical form of meter name for comparison."""
    normalized = normalize_meter_name(meter_name)
    return CANONICAL_METERS.get(normalized, normalized)


def parse_meter_field(meter_info):
    """
    Parse the meter field from Anukramani which may contain composite meters.

    Examples:
        "gāyatrī" → ['gayatri']
        "(1-6)jagatī,(7-9)triṣṭup" → ['jagati', 'tristubh']
        "(1-5,12)agniḥ,(6)devīrdvāraḥ" → ignores divinity info, extracts meters

    Returns list of unique meter names found.
    """
    if not meter_info:
        return []

    meters = []

    # Known meter names to look for (in IAST without diacritics)
    known_meters = {
        'gayatri',
        'usnik',
        'anustup',
        'anustubh',
        'tristup',
        'tristubh',
        'jagati',
        'brhati',
        'brihati',
        'pankti',
        'panktih',
        'virat',
        'viraj',
        'atyastih',
        'atyasti',
        'astih',
        'asti',
        'dhrtih',
        'dhrti',
        'adhrtih',
        'adhrti',
        'atisakvari',
        'sakvari',
        'pragathah',
        'pragatha',
        'atijagati',
        'mahapanktih',
        'mahapankti',
        'mahabrhati',
        'kakup',
        'kakubh',
        'krtih',
        'krti',
        'nastarupi',
        'tanusira',
        'abhisarini',
        'dvipada',
        'atinicrt',
        'jyotih',
        'prastarapanktih',
        'nyankurarini',
        'kakumnyankusira',
        'pipilikamadhya',
        'vardhamana',
    }

    # First, try to extract meter names by removing verse range markers
    # Pattern: (n) or (n-m) or (n,m) or (n-m,p-q) etc
    cleaned = re.sub(r'\([0-9,\-]+\)', '', meter_info)

    # Split by comma and process each part
    parts = cleaned.split(',')

    for part in parts:
        part = part.strip()

        if not part:
            continue

        # Skip pure numbers
        if re.match(r'^[0-9\-]+$', part):
            continue

        # Remove leading/trailing numbers that might be artifacts
        part = re.sub(r'^[0-9\-]+\)', '', part)
        part = re.sub(r'\([0-9\-]+$', '', part)
        part = part.strip()

        if not part or len(part) < 2:
            continue

        # Normalize and check if it's a known meter
        normalized = normalize_meter_name(part)

        # Check against known meters
        if normalized in known_meters or any(km in normalized for km in known_meters):
            meters.append(part)
        # Also accept if it looks like a meter name (no digits, reasonable length)
        elif not any(c.isdigit() for c in part) and 3 <= len(part) <= 20:
            # Skip obvious non-meter words
            skip_words = [
                'agni',
                'indra',
                'soma',
                'deva',
                'mitra',
                'varuna',
                'visnu',
                'rudra',
                'pusa',
                'asvin',
                'usa',
                'surya',
            ]
            if not any(sw in normalized for sw in skip_words):
                meters.append(part)

    # Deduplicate while preserving order
    seen = set()
    unique_meters = []
    for m in meters:
        normalized = normalize_meter_name(m)
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_meters.append(m)

    return unique_meters


def parse_anukramani_file(filepath):
    """
    Parse an Anukramani file and extract hymn-meter mappings.

    Format: hymn.verses.seer.divinity.meter
    Example: 1.9.vaiśvāmitro madhucchandāḥ.agniḥ.gāyatrī
    """
    hymns = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Skip header
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        parts = line.split('.')
        if len(parts) < 5:
            continue

        hymn_num = parts[0]
        verse_count = parts[1]
        # Meter is always the last part
        meter_info = parts[-1]

        # Parse all meters mentioned
        meters = parse_meter_field(meter_info)

        if not meters:
            # Fallback: just use the raw meter info
            meters = [meter_info]

        # Get primary meter (first one)
        primary_meter = meters[0] if meters else meter_info

        hymns.append(
            {
                'hymn': hymn_num,
                'verses': verse_count,
                'primary_meter': primary_meter,
                'all_meters': meters,
                'is_composite': len(meters) > 1,
                'raw_meter_info': meter_info,
            }
        )

    return hymns


def load_all_anukramani_data():
    """Load Anukramani data from all 10 Mandalas."""
    base_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'repos', 'WSC2023', 'Anukramani'
    )

    all_data = {}
    total_hymns = 0

    for i in range(1, 11):
        filepath = os.path.join(base_path, f'Mandala_{i}.txt')
        if os.path.exists(filepath):
            hymns = parse_anukramani_file(filepath)
            all_data[i] = hymns
            total_hymns += len(hymns)
            print(f"  Mandala {i}: {len(hymns)} hymns loaded")
        else:
            print(f"  Warning: {filepath} not found")

    print(f"\n  Total: {total_hymns} hymns across {len(all_data)} Mandalas\n")
    return all_data


def meters_match(predicted, expected):
    """
    Check if predicted meter matches expected meter.
    Uses canonical form comparison.
    """
    pred_canonical = get_canonical_form(predicted)
    exp_canonical = get_canonical_form(expected)

    return pred_canonical == exp_canonical
