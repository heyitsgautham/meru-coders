#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Rigveda Test Dataset by Merging:
1. Verse texts from Rigveda_api (repos/Rigveda_api/data/rigveda.json)
2. Meter annotations from WSC2023 Anukramani (repos/WSC2023/Anukramani/)

This creates an authentic test dataset with ground truth meters.
"""

import json
import os
import re
import unicodedata
from collections import defaultdict

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RIGVEDA_JSON = os.path.join(BASE_DIR, 'repos', 'Rigveda_api', 'data', 'rigveda.json')
ANUKRAMANI_DIR = os.path.join(BASE_DIR, 'repos', 'WSC2023', 'Anukramani')
OUTPUT_FILE = os.path.join(BASE_DIR, 'backend', 'evaluation', 'data', 'rigveda_authentic.py')


# Meter syllable counts (Vedic tradition)
VEDIC_METERS = {
    'gāyatrī': {'devanagari': 'गायत्री', 'syllables': 24, 'padas': '3×8'},
    'gayatri': {'devanagari': 'गायत्री', 'syllables': 24, 'padas': '3×8'},
    'uṣṇik': {'devanagari': 'उष्णिक्', 'syllables': 28, 'padas': '4×7'},
    'usnik': {'devanagari': 'उष्णिक्', 'syllables': 28, 'padas': '4×7'},
    'anuṣṭup': {'devanagari': 'अनुष्टुभ्', 'syllables': 32, 'padas': '4×8'},
    'anustup': {'devanagari': 'अनुष्टुभ्', 'syllables': 32, 'padas': '4×8'},
    'bṛhatī': {'devanagari': 'बृहती', 'syllables': 36, 'padas': '4×9'},
    'brhati': {'devanagari': 'बृहती', 'syllables': 36, 'padas': '4×9'},
    'paṅkti': {'devanagari': 'पङ्क्ति', 'syllables': 40, 'padas': '5×8'},
    'pankti': {'devanagari': 'पङ्क्ति', 'syllables': 40, 'padas': '5×8'},
    'triṣṭup': {'devanagari': 'त्रिष्टुभ्', 'syllables': 44, 'padas': '4×11'},
    'tristup': {'devanagari': 'त्रिष्टुभ्', 'syllables': 44, 'padas': '4×11'},
    'jagatī': {'devanagari': 'जगती', 'syllables': 48, 'padas': '4×12'},
    'jagati': {'devanagari': 'जगती', 'syllables': 48, 'padas': '4×12'},
}


def normalize_meter_name(name):
    """Normalize meter name for lookup."""
    if not name:
        return ""
    name = name.lower().strip()
    # Remove diacritics for matching
    name = unicodedata.normalize('NFD', name)
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))
    # Remove trailing h variants
    name = re.sub(r'h$', '', name)
    return name


def parse_anukramani():
    """Parse WSC2023 Anukramani files to get hymn-meter mappings."""
    hymn_meters = {}  # {(mandala, hymn): meter_name}

    for i in range(1, 11):
        filepath = os.path.join(ANUKRAMANI_DIR, f'Mandala_{i}.txt')
        if not os.path.exists(filepath):
            print(f"  Warning: {filepath} not found")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines[1:]:  # Skip header
            line = line.strip()
            if not line:
                continue

            parts = line.split('.')
            if len(parts) < 5:
                continue

            try:
                hymn = int(parts[0])
                meter_field = parts[4] if len(parts) > 4 else ""

                # Parse meter field (may have verse ranges like "(1-6)jagatī,(7-9)triṣṭup")
                # For simplicity, take the first/primary meter
                meter_match = re.search(r'([a-zA-Zāīūṛḷṅñṭḍṇśṣḥṃ]+)(?:\s|,|$)', meter_field)
                if meter_match:
                    primary_meter = meter_match.group(1).lower()
                    hymn_meters[(i, hymn)] = primary_meter
            except (ValueError, IndexError):
                continue

    return hymn_meters


def clean_sanskrit_text(text):
    """Remove Vedic accent marks and normalize text."""
    if not text:
        return ""

    # Remove Vedic accent marks (svarita, anudatta, etc.)
    # These are Unicode characters in the range U+0951-U+0954 and others
    accent_chars = [
        '\u0951',  # Devanagari stress sign udatta
        '\u0952',  # Devanagari stress sign anudatta
        '\u0953',  # Devanagari grave accent
        '\u0954',  # Devanagari acute accent
        '\u1cd0',
        '\u1cd1',
        '\u1cd2',  # Vedic tone marks
        '॒',
        '॑',
        '᳚',  # Common accent representations
    ]

    for char in accent_chars:
        text = text.replace(char, '')

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text.strip()


def load_rigveda_verses():
    """Load verses from Rigveda_api JSON."""
    if not os.path.exists(RIGVEDA_JSON):
        print(f"ERROR: {RIGVEDA_JSON} not found!")
        return []

    with open(RIGVEDA_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Deduplicate (some verses appear multiple times with different formats)
    seen = set()
    unique_verses = []

    for v in data:
        key = (v.get('mandala'), v.get('hymn'), v.get('verse'))
        sanskrit = v.get('sanskrit', '')

        # Skip if no Sanskrit text or already seen
        if not sanskrit or key in seen:
            continue

        # Prefer verses with more content
        if len(sanskrit) > 20:  # Minimum length filter
            seen.add(key)
            unique_verses.append(
                {
                    'mandala': v.get('mandala'),
                    'hymn': v.get('hymn'),
                    'verse': v.get('verse'),
                    'sanskrit': clean_sanskrit_text(sanskrit),
                    'translation': v.get('translation', ''),
                }
            )

    return unique_verses


def build_dataset():
    """Build the merged dataset."""
    print("=" * 60)
    print("Building Rigveda Authentic Test Dataset")
    print("=" * 60)

    # Load data sources
    print("\n1. Parsing WSC2023 Anukramani...")
    hymn_meters = parse_anukramani()
    print(f"   Found meter annotations for {len(hymn_meters)} hymns")

    print("\n2. Loading Rigveda_api verses...")
    verses = load_rigveda_verses()
    print(f"   Loaded {len(verses)} unique verses")

    # Merge datasets
    print("\n3. Merging datasets...")
    merged = []
    meter_counts = defaultdict(int)

    for v in verses:
        key = (v['mandala'], v['hymn'])
        meter_iast = hymn_meters.get(key)

        if not meter_iast:
            continue  # Skip verses without meter annotation

        # Normalize meter name
        meter_norm = normalize_meter_name(meter_iast)

        # Look up meter info
        meter_info = None
        for m_key, m_val in VEDIC_METERS.items():
            if normalize_meter_name(m_key) == meter_norm:
                meter_info = m_val
                break

        if not meter_info:
            # Unknown meter - skip for now
            continue

        merged.append(
            {
                'mandala': v['mandala'],
                'hymn': v['hymn'],
                'verse': v['verse'],
                'text': v['sanskrit'],
                'meter': meter_info['devanagari'],
                'meter_iast': meter_iast,
                'syllables': meter_info['syllables'],
                'padas': meter_info['padas'],
                'source': f"RV {v['mandala']}.{v['hymn']}.{v['verse']} (Rigveda_api + WSC2023)",
            }
        )

        meter_counts[meter_iast] += 1

    print(f"   Merged {len(merged)} verses with ground truth meters")

    # Print meter distribution
    print("\n4. Meter Distribution:")
    for meter, count in sorted(meter_counts.items(), key=lambda x: -x[1]):
        print(f"   {meter}: {count} verses")

    return merged


def generate_python_file(verses):
    """Generate Python file with the dataset."""

    content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHENTIC Rigveda Test Verses with Ground Truth Meters

AUTO-GENERATED from:
- Verse texts: repos/Rigveda_api/data/rigveda.json
- Meter annotations: repos/WSC2023/Anukramani/

DO NOT EDIT MANUALLY - regenerate using:
    python backend/scripts/build_rigveda_dataset.py
"""

# ============================================================================
# AUTHENTIC RIGVEDA VERSES WITH GROUND TRUTH METERS
# ============================================================================

RIGVEDA_AUTHENTIC = [
'''

    for v in verses:
        content += f'''    {{
        'mandala': {v['mandala']},
        'hymn': {v['hymn']},
        'verse': {v['verse']},
        'text': '{v['text']}',
        'meter': '{v['meter']}',
        'meter_iast': '{v['meter_iast']}',
        'syllables': {v['syllables']},
        'padas': '{v['padas']}',
        'source': '{v['source']}'
    }},
'''

    content += ''']

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_by_meter(meter_name):
    """Get verses by meter name."""
    return [v for v in RIGVEDA_AUTHENTIC 
            if meter_name.lower() in v['meter'].lower() 
            or meter_name.lower() in v['meter_iast'].lower()]

def get_by_mandala(mandala):
    """Get verses by mandala number."""
    return [v for v in RIGVEDA_AUTHENTIC if v['mandala'] == mandala]

def summary():
    """Print dataset summary."""
    from collections import Counter
    meters = Counter(v['meter_iast'] for v in RIGVEDA_AUTHENTIC)
    
    print(f"\\nTotal verses: {len(RIGVEDA_AUTHENTIC)}")
    print(f"\\nBy meter:")
    for meter, count in meters.most_common():
        info = next((v for v in RIGVEDA_AUTHENTIC if v['meter_iast'] == meter), None)
        if info:
            print(f"  {info['meter']} ({meter}): {count} verses, {info['syllables']} syllables")


if __name__ == '__main__':
    summary()
'''

    return content


def main():
    # Build dataset
    verses = build_dataset()

    if not verses:
        print("\nERROR: No verses merged! Check data sources.")
        return

    # Generate output file
    print(f"\n5. Generating {OUTPUT_FILE}...")
    content = generate_python_file(verses)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"   Written {len(verses)} verses to {OUTPUT_FILE}")
    print("\n" + "=" * 60)
    print("DONE! Run the test with:")
    print("  cd backend && python tests/test_true_vedic_accuracy.py")
    print("=" * 60)


if __name__ == '__main__':
    main()
