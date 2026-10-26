"""Meter-name matching and dataset loaders for autodetect_accuracy.py."""

import csv
import unicodedata

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate

    HAS_TRANSLITERATION = True
except ImportError:
    HAS_TRANSLITERATION = False

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
    # Extended Vedic meters
    'virāṭ': 'विराट्',
    'virat': 'विराट्',
    'pragāthaḥ': 'प्रगाथ',
    'pragātha': 'प्रगाथ',
    'mahāpaṅktiḥ': 'महापङ्क्ति',
    'mahāpaṅkti': 'महापङ्क्ति',
    'kakup': 'ककुभ्',
    'kakubh': 'ककुभ्',
    'dvipadā virāṭ': 'द्विपदा विराट्',
    'dvipadā triṣṭup': 'द्विपदा त्रिष्टुभ्',
}


# Meter families for fuzzy matching
METER_FAMILIES = {
    'गायत्री': ['गायत्री'],
    'उष्णिक्': ['उष्णिक्', 'ककुभ्'],
    'अनुष्टुभ्': ['अनुष्टुभ्'],
    'बृहती': ['बृहती', 'प्रगाथ', 'पङ्क्ति'],
    'पङ्क्ति': ['पङ्क्ति', 'बृहती', 'प्रगाथ', 'त्रिष्टुभ्'],
    'त्रिष्टुभ्': ['त्रिष्टुभ्', 'जगती', 'पङ्क्ति'],
    'जगती': ['जगती', 'त्रिष्टुभ्'],
    'विराट्': ['विराट्', 'गायत्री', 'उष्णिक्'],
    'प्रगाथ': ['प्रगाथ', 'बृहती', 'पङ्क्ति', 'त्रिष्टुभ्', 'जगती'],
    'ककुभ्': ['ककुभ्', 'उष्णिक्', 'बृहती'],
    'महापङ्क्ति': ['महापङ्क्ति', 'पङ्क्ति', 'जगती'],
}


def normalize_meter_name(name):
    """Normalize meter name from IAST to Devanagari"""
    if not name:
        return None
    name = name.strip().lower()
    if name.startswith('('):
        return None
    if name in METER_NORMALIZATION:
        return METER_NORMALIZATION[name]
    # Try without diacritics
    simple = name.replace('ṭ', 't').replace('ṣ', 's').replace('ṇ', 'n').replace('ī', 'i').replace('ā', 'a')
    for key, value in METER_NORMALIZATION.items():
        simple_key = key.replace('ṭ', 't').replace('ṣ', 's').replace('ṇ', 'n').replace('ī', 'i').replace('ā', 'a')
        if simple == simple_key:
            return value
    return None


def get_meter_family(meter_name):
    """Get the family of a meter"""
    for family, members in METER_FAMILIES.items():
        if meter_name in members:
            return family
    return meter_name


def meters_match_vedic(expected, predicted):
    """Check if meters match for Vedic dataset (with family matching)"""
    if not expected or not predicted:
        return False, False
    if expected == predicted:
        return True, True
    # Family match
    exp_family = get_meter_family(expected)
    pred_family = get_meter_family(predicted)
    if exp_family == pred_family:
        return False, True
    # Check cross-family
    for _family, members in METER_FAMILIES.items():
        if expected in members and predicted in members:
            return False, True
    return False, False


def to_iast(text):
    """Convert Devanagari to IAST"""
    if not HAS_TRANSLITERATION:
        return text
    try:
        return transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
    except Exception:
        return text


def normalize_csv(name):
    """Normalize meter name for CSV comparison"""
    name = name.lower().strip()
    name = to_iast(name)
    name = unicodedata.normalize('NFD', name)
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))
    return name


CSV_METER_FAMILIES = {
    'anustup': 'anustubh',
    'anustubh': 'anustubh',
    'sardulavkridita': 'sardula',
    'sardulavikriditam': 'sardula',
    'sardulavikridita': 'sardula',
    'upajatih': 'upajati',
    'upajati': 'upajati',
    'indravajra': 'upajati',
    'upendravajra': 'upajati',
    'vasantatilakam': 'vasantatilaka',
    'vasantatilaka': 'vasantatilaka',
    'mandakranta': 'mandakranta',
    'mandakrantam': 'mandakranta',
    'sragdhara': 'sragdhara',
    'pancakavali': 'sragdhara',
    'bhujangaprayatam': 'bhujanga',
    'bhujangaprayata': 'bhujanga',
}


def get_csv_family(name):
    """Get meter family for CSV comparison"""
    norm = normalize_csv(name)
    return CSV_METER_FAMILIES.get(norm, norm)


def meters_match_csv(expected, predicted):
    """Check if two meter names match for CSV dataset"""
    exp_fam = get_csv_family(expected)
    pred_fam = get_csv_family(predicted)
    if exp_fam == pred_fam:
        return True
    if exp_fam in pred_fam or pred_fam in exp_fam:
        return True
    return False


def load_rigveda_dataset(filepath, limit=None):
    """Load the Rigveda dataset"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for _row_num, row in enumerate(reader, start=2):
            verse_text = row.get('verse_text', '').strip()
            meter = row.get('meter', '').strip()
            if not verse_text or not meter or meter.startswith('('):
                continue
            normalized = normalize_meter_name(meter)
            if not normalized:
                continue
            data.append(
                {
                    'ref': f"{row.get('mandala', '')}.{row.get('sukta', '')}.{row.get('rik', '')}",
                    'verse_text': verse_text,
                    'expected_meter': normalized,
                    'original_meter': meter,
                }
            )
            if limit and len(data) >= limit:
                break
    return data


REAL_VERSE_COUNT = 147  # First 147 rows are real verses


def load_csv_dataset(filepath):
    """Load the classical CSV dataset"""
    data = []
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
            if row_index > REAL_VERSE_COUNT:
                break
            data.append(
                {
                    'verse': verse,
                    'expected_meter': expected,
                    'row': row_index,
                }
            )
    return data
