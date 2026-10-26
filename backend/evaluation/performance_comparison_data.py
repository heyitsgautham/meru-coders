"""Meter-name matching and dataset loaders for performance_comparison.py."""

import csv
import os
import unicodedata

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)


# Dataset paths
SMALL_DATA_PATH = os.path.join(ROOT_DIR, 'repos', 'chanda', 'data')
LARGE_DATA_PATH = os.path.join(BACKEND_DIR, 'data')


# Test data paths
RIGVEDA_CSV = os.path.join(LARGE_DATA_PATH, 'rigveda_with_meters_complete.csv')
PAGE_CSV = os.path.join(LARGE_DATA_PATH, 'page 1-47 chanda list - complete.csv')


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
