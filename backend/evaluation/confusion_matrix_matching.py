"""Meter-name synonyms and family rules confusion_matrix.py scores predictions with."""

import re

# Map various spellings/transliterations to canonical names
# Format: {normalized_name: [list of variants]}
METER_SYNONYMS = {
    # Vedic/Common meters
    'anushtubh': ['anuṣṭup', 'anushtup', 'anushtubh', 'anustubh', 'anustup', 'अनुष्टुभ्', 'अनुष्टुप्', 'anuṣṭubh', 'अनुष्टुभ'],
    'trishtubh': ['triṣṭubh', 'trishtubh', 'त्रिष्टुभ्', 'त्रिष्टुभ', 'trishtup'],
    'jagati': ['jagatī', 'jagati', 'जगती', 'जगति'],
    'gayatri': ['gāyatrī', 'gayatri', 'gayatree', 'गायत्री'],
    'ushnik': ['uṣṇik', 'ushnik', 'उष्णिक्', 'उष्णिक'],
    'pankti': ['paṅkti', 'pankti', 'पङ्क्ति', 'पंक्ति'],
    'brihati': ['bṛhatī', 'brihati', 'बृहती'],
    # Classical meters - 11 syllable patterns (Trishtubh family)
    'indravajra': ['indravajrā', 'indravajra', 'इन्द्रवज्रा', 'इन्द्रवज्र'],
    'upendravajra': ['upendravajra', 'upendravajrā', 'उपेन्द्रवज्रा', 'उपेन्द्रवज्र'],
    'upajati': ['upajātiḥ', 'upajāti', 'upajati', 'उपजाति', 'उपजातिः'],
    'shalini': ['śālinī', 'shalini', 'salini', 'शालिनी'],
    'rathoddhata': ['rathoddhata', 'rathoddhātā', 'रथोद्धता', 'rathōddhata'],
    'svagata': ['svāgatā', 'svagata', 'स्वागता'],
    # Classical meters - 12 syllable patterns (Jagati family)
    'vamshastham': ['vaṁśasthavilam', 'vamshasthavila', 'vaṁśastha', 'vamshastham', 'वंशस्थ', 'वंशस्थविल', 'वंशशथविल'],
    'drutavilambita': ['drutavilambita', 'द्रुतविलम्बित', 'द्रुतविलंबित', 'druta-vilambita'],
    'totaka': ['toṭakam', 'totaka', 'toṭaka', 'तोटक', 'तोटकम्'],
    'bhujangaprayata': ['bhujangaprayātam', 'bhujangaprayāta', 'bhujangaprayata', 'भुजङ्गप्रयात', 'भुजंगप्रयात'],
    # Classical meters - 13+ syllable patterns
    'vasantatilaka': ['vasantatilakam', 'vasantatilaka', 'vasantatilakā', 'वसन्ततिलका', 'वसन्ततिलक'],
    'malini': ['mālinī', 'malini', 'mālini', 'मालिनी'],
    'praharsini': ['praharṣinī', 'praharsini', 'praharshini', 'प्रहर्षिणी'],
    # Classical meters - 17+ syllable patterns
    'mandakranta': ['mandäkräntä', 'mandākrāntā', 'mandakranta', 'mandākrānta', 'मन्दाक्रान्ता', 'मन्दाक्रान्त', 'मंदाक्रांता'],
    'shardula': [
        'śārdülavkrīḍita',
        'śārdūlavikrīḍita',
        'shardula',
        'shardulavikridit',
        'शार्दूलविक्रीडित',
        'शार्दूलविक्रीडितम्',
        'sārdulavikrīḍita',
    ],
    'sragdhara': ['sragdharā', 'sragdhara', 'स्रग्धरा'],
    # Other meters
    'pancacamara': ['pañcacāmaram', 'pancacamara', 'pañcacāmara', 'पञ्चचामर', 'पंचचामर'],
    'tunaka': ['tūṇakam', 'tunaka', 'tūṇaka', 'तूणक', 'चामर'],
    'tvaritagati': ['tvaritagati', 'त्वरितगति'],
    'upacitra': ['upacitrā', 'upacitra', 'उपचित्रा'],
    'udgata': ['udgatā', 'udgata', 'उद्गता'],
    'gajagati': ['gajagati', 'गजगति'],
    # Meters that may be confused - special mapping
    'kalahansa': ['kalahaṁsa', 'kalahansa', 'कलहंस'],
    'apavaha': ['apavāha', 'apavaha', 'अपवाह'],
    'arnadandaka': ['arṇadaṇḍaka', 'arnadandaka', 'अर्णदण्डक'],
    'meghavispurjita': ['meghavispūrjita', 'meghavispurjita', 'मेघविस्फूर्जिता'],
    'atishayini': ['atiśāyinī', 'atishayini', 'अतिशायिनी'],
}


def normalize_meter_name(name):
    """
    Normalize meter name to a canonical form for comparison.
    Handles IAST, Devanagari, and various transliteration schemes.
    """
    if not name:
        return ''

    # Convert to lowercase for comparison
    name_lower = name.lower().strip()

    # Remove common suffixes/prefixes
    name_lower = re.sub(r'^(श्री|śrī)', '', name_lower)
    name_lower = re.sub(r'(छन्दस्|chandas)$', '', name_lower)

    # Check against synonyms
    for canonical, variants in METER_SYNONYMS.items():
        for variant in variants:
            if name_lower == variant.lower() or name.strip() == variant:
                return canonical

    # If no match found, return cleaned version
    return name_lower.replace(' ', '').replace('-', '').replace('_', '')


# Define meter families for lenient matching
# Trishtubh family: 11 syllables per pada (44 total for 4 padas)
TRISHTUBH_FAMILY = {
    'trishtubh',
    'indravajra',
    'upendravajra',
    'upajati',
    'shalini',
    'rathoddhata',
    'svagata',
    'dodhaka',
    'shalinivishama',
}


# Jagati family: 12 syllables per pada (48 total for 4 padas)
JAGATI_FAMILY = {
    'jagati',
    'vamshastham',
    'totaka',
    'bhujangaprayata',
    'drutavilambita',
    'indravamsha',
    'vamshasthavilam',
    'praharshini',
}


def is_family_match(expected_norm, predicted_norm):
    """
    Check if expected and predicted meters belong to the same family.
    Returns True for Trishtubh-family or Jagati-family matches.
    """
    # Trishtubh family match
    if expected_norm in TRISHTUBH_FAMILY and predicted_norm in TRISHTUBH_FAMILY:
        return True

    # Jagati family match
    if expected_norm in JAGATI_FAMILY and predicted_norm in JAGATI_FAMILY:
        return True

    return False


def extract_top_meter(result, expected_meter=None):
    """
    Extract the top predicted meter from identification result.
    Returns (meter_name, confidence, match_rank) tuple.

    match_rank is:
    - 1 if expected meter is top-1
    - 2-3 if expected meter is in top-3
    - 0 if not found in top results
    """
    if not result or 'chanda' not in result:
        return None, 0.0, 0

    chanda_list = result.get('chanda', [])
    confidence_scores = result.get('confidence_scores', {})

    if not chanda_list:
        return None, 0.0, 0

    # Get top meter
    top_item = chanda_list[0]
    if isinstance(top_item, tuple):
        top_meter = top_item[0]
    else:
        top_meter = str(top_item)

    # Get confidence
    if confidence_scores and top_meter in confidence_scores:
        confidence = confidence_scores[top_meter][0]
    else:
        confidence = 0.0

    # Check match rank if expected_meter provided
    match_rank = 0
    if expected_meter:
        normalized_expected = normalize_meter_name(expected_meter)
        for idx, item in enumerate(chanda_list[:5]):  # Check top 5
            if isinstance(item, tuple):
                pred_name = item[0]
            else:
                pred_name = str(item)

            if normalize_meter_name(pred_name) == normalized_expected:
                match_rank = idx + 1
                break

    return top_meter, confidence, match_rank
