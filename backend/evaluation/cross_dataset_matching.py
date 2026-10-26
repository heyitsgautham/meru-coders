"""Meter aliases and name matching for cross_dataset_comparison.py."""

import re

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

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
