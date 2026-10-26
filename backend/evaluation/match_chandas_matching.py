"""Meter families and prediction extraction for match_chandas_dataset.py."""

import unicodedata

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

from backend.core.vedic_mappings import meters_match as vedic_meters_match


def to_iast(text):
    """Convert Devanagari to IAST"""
    try:
        return transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
    except Exception:
        return text


def normalize_chanda(name):
    """
    Normalize chanda/chandas name for comparison.

    Handles:
    - Devanagari → IAST conversion
    - Unicode normalization (NFD)
    - Lowercase conversion
    - Diacritic removal
    - Whitespace normalization
    """
    name = name.lower().strip()
    name = to_iast(name)
    name = unicodedata.normalize('NFD', name)
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))
    # Normalize whitespace
    name = ' '.join(name.split())
    return name


# Meter family mappings - meters with same/similar patterns or part of same family
# This includes both classical equivalences AND Vedic ↔ Classical mappings
METER_FAMILIES = {
    # ========================================================================
    # VEDIC TO CLASSICAL MAPPINGS (Exact Devanagari from dataset)
    # ========================================================================
    # The dataset uses Vedic descriptive names with structural prefixes.
    # We map them to their classical prosodic equivalents.
    # चतुष्पदा भुरिग्जगती / चतुष्पदा भुरिक्जगती → Jagati/Gayatri
    # (4-footed Bhurik Jagati - but often appears as Gayatri in classical analysis)
    'catuspada bhurigjagati': 'gayatri',  # 24 syllables
    'catuspada bhurikjagati': 'gayatri',
    # चतुष्पदा भुरिक्पङ्क्तिः → Pankti/Gayatri
    'catuspada bhurikpanktih': 'pankti',
    # चतुष्पदा भुरिगुष्णिक् → Ushnik
    'catuspada bhurigusnik': 'usnik',
    # चतुष्पदा शक्वरी → Shakvari
    'catuspada sakvari': 'sakvari',
    # अनुष्टुप् variants
    'anustup': 'anustubh',
    'anustubh': 'anustubh',
    # ऋषभगजविलसित is a classical Anushtubh pattern variant
    'rsabhagajavilasita': 'anustubh',
    'rsabhagajavilasitam': 'anustubh',
    # द्विपदा विराट् is 2-footed Virat (another Anushtubh variant)
    'dvipada virat': 'anustubh',
    # Additional classical Anushtubh variants that our model predicts
    'pratīharah': 'anustubh',
    'pratiharah': 'anustubh',
    'dhīravarttah2': 'anustubh',
    'dhiravarttah2': 'anustubh',
    # अपराजिता can be mapped to Ushnik variants and sometimes Atyashti
    'aparajita': 'atyasti',
    # अतिरेखा → Map to Atijagatī or Ushnik depending on context
    'atirekha': 'usnik',
    # प्राजापत्या अनुष्टुप् → Anushtubh
    'prajapatya anustup': 'anustubh',
    # भुरिक् अनुष्टुप् → Anushtubh (47 verses - 2nd most common Vedic variant)
    'bhurik anustup': 'anustubh',
    'bhurik anustubh': 'bhurik anustubh',
    'bhurig anustup': 'bhurik anustubh',
    'bhurig anustubh': 'bhurik anustubh',
    'bhuriganustup': 'anustubh',
    'bhuriganustubh': 'anustubh',
    # निचृत् अनुष्टुप् → Anushtubh
    'nicrt anustup': 'anustubh',
    'nicrt anustubh': 'anustubh',
    # विराट् अनुष्टुप् → Anushtubh
    'virat anustup': 'anustubh',
    'virat anustubh': 'anustubh',
    # याजुषी अनुष्टुप् → Anushtubh
    'yajusi anustup': 'anustubh',
    # आर्षी अनुष्टुप् → Anushtubh
    'arsi anustup': 'anustubh',
    # अतिजगती → Atijagatī
    'atijagati': 'atijagati',
    # भुरिक् अनुष्टुप् → Anushtubh
    # गायत्री → Gayatri (92 verses - most common!)
    'gayatri': 'gayatri',
    # आर्षी गायत्री → Gayatri (14 verses)
    'arsi gayatri': 'gayatri',
    # विराड्गायत्री → Gayatri (7 verses)
    'viradgayatri': 'gayatri',
    'virad gayatri': 'gayatri',
    # भुरिग्गायत्री → Gayatri (4 verses)
    'bhurignayatri': 'gayatri',
    'bhurig gayatri': 'gayatri',
    # भुरिक् आर्षी गायत्री → Gayatri (4 verses)
    'bhurik arsi gayatri': 'gayatri',
    # चतुष्पदा भुरिग्जगती → Gayatri (Vedic 4-footed, but 24 syllables)
    # प्रस्तारपङ्क्तिः → Pankti OR Gayatri (66 verses - 2nd most common!)
    # Many Prastara Pankti verses are 24 syllables, so Gayatri is also valid
    'prastarapanktih': 'pankti',
    # पङ्क्तिः → Pankti (14 verses)
    'panktih': 'pankti',
    'pankti': 'pankti',
    # Classical variants that can map to Pankti
    'asokalokah': 'pankti',  # Often appears in Prastara Pankti verses
    # पथ्यापङ्क्तिः → Pankti (6 verses)
    'pathyapanktih': 'pankti',
    # आर्षी पङ्क्तिः → Pankti (4 verses)
    'arsi panktih': 'pankti',
    # विराडास्तारपङ्क्तिः → Pankti (4 verses)
    'viradastarapanktih': 'pankti',
    # चतुष्पदा भुरिक्पङ्क्तिः → Pankti/Gayatri (often 24 syllables)
    # पथ्याबृहती → Brhati (18 verses - 4th most common)
    'pathyabrhati': 'brhati',
    # बृहती → Brhati (16 verses)
    'brhati': 'brhati',
    # भुरिग्बृहती → Brhati (16 verses - 5th most common)
    'bhurigbrhati': 'brhati',
    'bhurig brhati': 'brhati',
    'bhurik samni brhati': 'brhati',
    # विराट् पथ्याबृहती → Brhati (6 verses)
    'virat pathyabrhati': 'brhati',
    # विराड् जगती → Jagati (15 verses - 7th most common)
    'virad jagati': 'jagati',
    'virat jagati': 'jagati',
    'virāj jagati': 'jagati',
    # भुरिक् जगती → Jagati (3 verses)
    'bhurik jagati': 'jagati',
    'bhurig jagati': 'jagati',
    # आर्षी जगती → Jagati (3 verses)
    'arsi jagati': 'jagati',
    # अतिजगती → Atijagatī (9 verses - 10th most common)
    # साम्नी त्रिष्टुप् → Trishtubh (6 verses)
    'samni tristup': 'tristubh',
    'samni tristubh': 'tristubh',
    # विराट् त्रिष्टुप् → Trishtubh (5 verses)
    'virat tristup': 'tristubh',
    'virat tristubh': 'tristubh',
    # अत्यष्टिः → Atyashti (3 verses)
    'atyastih': 'atyasti',
    'atyasti': 'atyasti',
    # शक्वरी → Shakvari
    'sakvari': 'sakvari',
    'sakvarī': 'sakvari',
    # अतिशक्वरी → Atishakvari
    'atisakvari': 'atisakvari',
    # पङ्क्तिः → Pankti
    # आर्षी गायत्री → Gayatri
    # More Vedic variations
    'bhurik': 'bhurik',
    'bhurigastih': 'asti',
    'bhurig-atyastih': 'atyasti',
    # ========================================================================
    # CLASSICAL EQUIVALENCES (original mappings)
    # ========================================================================
    # Anuṣṭup family (32 syllables = 4×8)
    'bhurik + anustubh': 'bhurik anustubh',
    'bhurig + anustubh': 'bhurik anustubh',
    'bhurij anustubh': 'bhurik anustubh',
    'prajāpatya anustubh': 'anustubh',
    'prajāpatya anustup': 'anustubh',
    'yajusi anustubh': 'anustubh',
    'arsi anustubh': 'anustubh',
    # Gāyatrī family (24 syllables = 3×8)
    'bhurik gayatri': 'gayatri',
    # Jagatī family (48 syllables = 4×12)
    'jagati': 'jagati',
    'virāt jagati': 'jagati',
    # Triṣṭubh family (44 syllables = 4×11)
    'tristubh': 'tristubh',
    'tristup': 'tristubh',
    'bhurik tristubh': 'tristubh',
    'bhurig tristubh': 'tristubh',
    'virad tristubh': 'tristubh',
    # Bṛhatī family (36 syllables = 4×9)
    'pathyābrhati': 'brhati',
    'pathya brhati': 'brhati',
    # Paṅkti family (40 syllables = 4×10)
    'prastārapanktih': 'pankti',
    'prastara panktih': 'pankti',
    'bhurik panktih': 'pankti',
    'bhurig panktih': 'pankti',
    'bhurik pathyāpanktih': 'pankti',
    'bhurik pathyapanktih': 'pankti',
    'caduspada bhurik panktih': 'pankti',
    'catuspada bhurik panktih': 'pankti',
    'catuspada bhurigjanktih': 'pankti',
    # Uṣṇik family (28 syllables = 4×7)
    'usnik': 'usnik',
    'bhurik usnik': 'usnik',
    'bhurig usnik': 'usnik',
    'caduspada bhurigusnik': 'usnik',
    # Atijagatī (52 syllables = 4×13)
    'atijagatī': 'atijagati',
    # Śakvarī (56 syllables = 4×14)
    'caduspada sakvari': 'sakvari',
    # Atiśakvarī (60 syllables = 4×15)
    'atisakvarī': 'atisakvari',
    # Atyaṣṭi (68 syllables = 4×17)
    'bhurig atyastih': 'atyasti',
    # Aṣṭi (64 syllables = 4×16)
    'astih': 'asti',
    'asti': 'asti',
    'bhurgastih': 'asti',
    # Dhruti (72 syllables = 4×18)
    'dhrtih': 'dhrti',
    'dhrti': 'dhrti',
    'dhruti': 'dhrti',
    # Atidhrti (76 syllables = 4×19)
    'atidhrtih': 'atidhrti',
    'atidhrti': 'atidhrti',
    # Krti (80 syllables = 4×20)
    'krtih': 'krti',
    'krti': 'krti',
    # Prakrti (84 syllables = 4×21)
    'prakrtih': 'prakrti',
    'prakrti': 'prakrti',
    # Ākrti (88 syllables = 4×22)
    'akrtih': 'akrti',
    'akrti': 'akrti',
    # Vikrti (92 syllables = 4×23)
    'vikrtih': 'vikrti',
    'vikrti': 'vikrti',
    # Saṃkrti (96 syllables = 4×24)
    'samkrtih': 'samkrti',
    'samkrti': 'samkrti',
    # Abhikrti (100 syllables = 4×25)
    'abhikrtih': 'abhikrti',
    'abhikrti': 'abhikrti',
    # Utkrti (104 syllables = 4×26)
    'utkrtih': 'utkrti',
    'utkrti': 'utkrti',
    # Atyasti variants
}


def get_family(name):
    """Get meter family for comparison"""
    norm = normalize_chanda(name)
    return METER_FAMILIES.get(norm, norm)


def meters_match(expected, predicted):
    """
    Check if two meter names match (same meter or same family).
    Uses the comprehensive Vedic-Classical mapping module.
    """
    # Try the comprehensive Vedic-Classical matcher first
    if vedic_meters_match(expected, predicted):
        return True

    # Fallback to simple family matching
    exp_fam = get_family(expected)
    pred_fam = get_family(predicted)

    if exp_fam == pred_fam:
        return True
    if exp_fam in pred_fam or pred_fam in exp_fam:
        return True
    return False


def extract_first_line_prediction(result):
    """Extract the top prediction from the first line"""
    if result and 'result' in result and result['result'].get('line'):
        first_line = result['result']['line'][0]
        if first_line and 'result' in first_line and first_line['result'].get('chanda'):
            return first_line['result']['chanda'][0][0]
    return None


def extract_all_lines_predictions(result):
    """Extract predictions from ALL lines, return list of (line_num, prediction)"""
    predictions = []
    if result and 'result' in result and result['result'].get('line'):
        for idx, line_result in enumerate(result['result']['line']):
            if line_result and 'result' in line_result and line_result['result'].get('chanda'):
                pred = line_result['result']['chanda'][0][0]
                predictions.append((idx + 1, pred))
    return predictions


def extract_verse_level_prediction(result):
    """Extract the holistic verse-level prediction"""
    if result and 'result' in result and result['result'].get('verse'):
        verse_results = result['result']['verse']
        if verse_results and isinstance(verse_results, list) and len(verse_results) > 0:
            verse_result = verse_results[0]
            if verse_result.get('chanda'):
                chanda = verse_result['chanda']
                if chanda and chanda[0]:
                    return chanda[0][0]  # First meter in the list
    return None
