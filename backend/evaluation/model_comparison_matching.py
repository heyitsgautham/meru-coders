"""Meter-name normalisation, families and the test-data loader for model_comparison.py."""

import csv
import re
import unicodedata

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate

    TRANSLITERATION_AVAILABLE = True
except ImportError:
    TRANSLITERATION_AVAILABLE = False


def is_devanagari(text):
    """Check if text contains Devanagari characters"""
    for char in text:
        if '\u0900' <= char <= '\u097f':
            return True
    return False


def normalize_meter_name(name):
    """Normalize meter name for comparison - handles both Devanagari and IAST"""
    if not name:
        return ''

    name = name.strip()

    # Convert Devanagari to IAST if needed
    if TRANSLITERATION_AVAILABLE and is_devanagari(name):
        name = transliterate(name, sanscript.DEVANAGARI, sanscript.IAST)

    # Convert to lowercase
    name = name.lower()

    # Standard IAST to ASCII simplification (do this BEFORE suffix handling)
    ascii_map = {
        'ā': 'a',
        'ī': 'i',
        'ū': 'u',
        'ṛ': 'r',
        'ṝ': 'r',
        'ṣ': 'sh',
        'ś': 'sh',
        'ñ': 'n',
        'ṇ': 'n',
        'ṅ': 'n',
        'ṭ': 't',
        'ḍ': 'd',
        'ṃ': 'm',
        'ḥ': 'h',
        'ä': 'a',
        'ü': 'u',  # German-style diacritics from test data
        'ṁ': 'm',
    }
    for k, v in ascii_map.items():
        name = name.replace(k, v)

    # Remove Devanagari suffixes
    name = re.sub(r'[म्ःा]+$', '', name)

    # Remove remaining diacritics using unicode normalization
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))

    # Additional transliteration mappings for specific meter names
    meter_aliases = {
        # Anushtubh variants (p/b variation at end)
        'anushtup': 'anushtubh',
        'anustup': 'anushtubh',
        'anustubh': 'anushtubh',
        'anushtub': 'anushtubh',
        # Shardula variants (with/without 'k' in vikridita)
        'shardulavkridita': 'shardulavikridita',
        'shardulavrikridita': 'shardulavikridita',
        # Vamshastha variants
        'vamshasthavila': 'vamshastha',
        'vamshastham': 'vamshastha',
        'vamshasthavilam': 'vamshastha',
        # Upajati variants
        'upajatih': 'upajati',
        # With 'am' suffix
        'totakam': 'totaka',
        'vasantatilakam': 'vasantatilaka',
        'bhujangaprayatam': 'bhujangaprayata',
        'drutavilambitam': 'drutavilambita',
        'shardulavikriditam': 'shardulavikridita',
        'pancacamaram': 'pancacamara',
        # Totaka variants
        'toṭakam': 'totaka',
        'toṭaka': 'totaka',
        'तोटक': 'totaka',
        # Vasantatilaka variants
        'vasantatilakā': 'vasantatilaka',
        'वसन्ततिलका': 'vasantatilaka',
        # Malini variants
        'mālinī': 'malini',
        'मालिनी': 'malini',
        # Mandakranta variants
        'mandākrāntā': 'mandakranta',
        'mandäkräntä': 'mandakranta',
        'मन्दाक्रान्ता': 'mandakranta',
        # Shardula variants
        'śārdūlavikrīḍitam': 'shardula',
        'śārdülavkrīḍita': 'shardula',
        'śārdülavikrīḍita': 'shardula',
        'शार्दूलविक्रीडित': 'shardula',
        # Praharsini variants
        'praharṣiṇī': 'praharsini',
        'प्रहर्षिणी': 'praharsini',
        # Drutavilambita variants
        'drutavilambita': 'drutavilambita',
        'द्रुतविलम्बित': 'drutavilambita',
        # Udgatā variants
        'udgatā': 'udgata',
        'उद्गता': 'udgata',
        # Gajagati variants
        'gajagati': 'gajagati',
        'गजगति': 'gajagati',
        # Tvaritagati variants
        'tvaritagati': 'tvaritagati',
        # Upacitra variants
        'upacitrā': 'upacitra',
        # Trishtubh variants
        'triṣṭubh': 'trishtubh',
        'triṣṭup': 'trishtubh',
        'त्रिष्टुभ्': 'trishtubh',
        # Jagati variants
        'jagatī': 'jagati',
        'जगती': 'jagati',
        # Sragdhara
        'sragdharā': 'sragdhara',
        'स्रग्धरा': 'sragdhara',
        # Shikhirini
        'śikhariṇī': 'shikharini',
        'शिखरिणी': 'shikharini',
        # Arya
        'āryā': 'arya',
        'आर्या': 'arya',
        # Tunaka
        'tūṇakam': 'tunaka',
        'तूणक': 'tunaka',
        # Panchacamara
        'pañcacāmaram': 'pancacamara',
        'पञ्चचामर': 'pancacamara',
    }

    # Apply mapping
    if name in meter_aliases:
        return meter_aliases[name]

    # Try Unicode normalization
    normalized = unicodedata.normalize('NFKD', name)
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    normalized = normalized.lower()

    if normalized in meter_aliases:
        return meter_aliases[normalized]

    return name


TRISHTUBH_FAMILY = {
    'indravajra',
    'upendravajra',
    'upajati',
    'shalini',
    'rathoddhata',
    'svagata',
    'dodhaka',
    'trishtubh',
}
JAGATI_FAMILY = {'vamshastham', 'indravamsha', 'bhujangaprayata', 'totaka', 'sragvini', 'drutavilambita', 'jagati'}
ANUSHTUBH_FAMILY = {'anushtubh', 'anustubh', 'sloka'}


def get_meter_family(meter_name):
    """Get the family of a meter"""
    normalized = normalize_meter_name(meter_name)

    if normalized in TRISHTUBH_FAMILY:
        return 'trishtubh'
    elif normalized in JAGATI_FAMILY:
        return 'jagati'
    elif normalized in ANUSHTUBH_FAMILY:
        return 'anushtubh'
    else:
        return normalized


def load_test_data(csv_path):
    """Load test data from CSV"""
    test_cases = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)

        for _row_num, row in enumerate(reader):
            if len(row) < 4:
                continue

            shloka = row[0].strip() if row[0] else ''
            lg_pattern = row[1].strip() if len(row) > 1 and row[1] else ''
            gana = row[2].strip() if len(row) > 2 and row[2] else ''
            expected_meter = row[3].strip() if len(row) > 3 and row[3] else ''

            # Skip header rows (rows containing "Shloka", "L/G", "Gana", "chanda" as values)
            if not shloka or not expected_meter:
                continue
            if expected_meter.lower() in ('chanda', 'meter', 'type'):
                continue
            if shloka.lower() in ('shloka', 'verse', 'text'):
                continue

            # Clean up shloka - normalize multiple spaces but PRESERVE newlines
            # Newlines are important for pada boundary detection
            lines = shloka.split('\n')
            cleaned_lines = [' '.join(line.split()) for line in lines]
            shloka = '\n'.join(cleaned_lines)

            test_cases.append(
                {
                    'shloka': shloka,
                    'lg_pattern': lg_pattern,
                    'gana': gana,
                    'expected': expected_meter,
                    'expected_normalized': normalize_meter_name(expected_meter),
                    'expected_family': get_meter_family(expected_meter),
                }
            )

    return test_cases
