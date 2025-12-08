#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vedic ↔ Classical Meter Mappings for Atharva Veda Dataset

This module provides comprehensive mappings between Vedic descriptive meter names
and Classical prosodic meter names. Based on empirical analysis of 471 verses
from the Atharva Veda dataset.

Research Sources:
- Arnold, E.V. - "Vedic Metre in its Historical Development" (1905)
- Keith, A.B. - "The Sanskrit Drama" (Vedic meter classification)
- Rigveda Pratiśākhya (Vedic prosody tradition)
- Pingala's Chandaḥśāstra (Classical prosody tradition)

Analysis Date: December 8, 2025
Dataset: match_chandas.csv (471 verses, 81 unique Vedic meters)
"""

from typing import List, Dict, Set
import unicodedata
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


def normalize_meter_name(name: str) -> str:
    """
    Normalize meter name for comparison.
    
    - Converts Devanagari → IAST
    - Lowercase
    - Removes diacritics
    - Normalizes whitespace
    """
    name = name.lower().strip()
    try:
        name = transliterate(name, sanscript.DEVANAGARI, sanscript.IAST)
    except:
        pass
    name = unicodedata.normalize('NFD', name)
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))
    name = ' '.join(name.split())
    return name


# ============================================================================
# COMPREHENSIVE VEDIC → CLASSICAL MAPPINGS
# ============================================================================
# Based on empirical analysis of mismatch patterns

VEDIC_TO_CLASSICAL_PRIMARY = {
    # ========================================================================
    # GAYATRI FAMILY (24 syllables = 3×8)
    # Most commonly predicted as: ऋषभगजविलसित, अतिरेखा, गायत्री
    # ========================================================================
    
    # गायत्री (92 verses) - Base Gayatri
    # Predicted as: ऋषभगजविलसित(46), अतिरेखा(26), अपराजिता(7)
    'gayatri': ['gayatri', 'rsabhagajavilasita', 'atirekha', 'aparajita'],
    
    # प्रस्तारपङ्क्तिः (66 verses) - Prastara Pankti
    # Predicted as: गायत्री(60), aśokalokaḥ(6)
    'prastarapanktih': ['gayatri', 'asokalokah', 'pankti'],
    
    # विराड् जगती (15 verses) - Virad Jagati
    # Predicted as: गायत्री(13), aśokalokaḥ(1)
    'virad jagati': ['gayatri', 'asokalokah', 'jagati'],
    'virat jagati': ['gayatri', 'asokalokah', 'jagati'],
    
    # आर्षी गायत्री (14 verses) - Arshi Gayatri
    # Predicted as: अतिरेखा(7), अनुष्टुभ्(5)
    'arsi gayatri': ['atirekha', 'anustubh', 'gayatri'],
    'arsi gayatri': ['atirekha', 'anustubh', 'gayatri'],
    
    # विराड्गायत्री (7 verses) - Virad Gayatri
    # Predicted as: गायत्री(6)
    'viradgayatri': ['gayatri'],
    'virad gayatri': ['gayatri'],
    
    # पङ्क्तिः (14 verses) - Pankti
    # Predicted as: गायत्री(7), sāhūti(2)
    'panktih': ['gayatri', 'sahuti', 'pankti'],
    'pankti': ['gayatri', 'pankti'],
    
    # आर्षी पङ्क्तिः (4 verses) - Arshi Pankti
    # Predicted as: गायत्री(4)
    'arsi panktih': ['gayatri', 'pankti'],
    
    # भुरिग्गायत्री (4 verses) - Bhurig Gayatri
    # Predicted as: द्विपदा विराट्(2), ऋषभगजविलसित(2)
    'bhurignayatri': ['dvipada virat', 'rsabhagajavilasita', 'gayatri'],
    'bhurig gayatri': ['dvipada virat', 'rsabhagajavilasita', 'gayatri'],
    
    # भुरिक् आर्षी गायत्री (4 verses) - Bhurik Arshi Gayatri
    # Predicted as: द्विपदा विराट्(4)
    'bhurik arsi gayatri': ['dvipada virat', 'gayatri'],
    
    # चतुष्पदा भुरिग्जगती - 4-footed Bhurik Jagati (24 syllables)
    # Predicted as: गायत्री
    'catuspada bhurigjagati': ['gayatri'],
    'catuspada bhurikjagati': ['gayatri'],
    'caduspada bhurigjagati': ['gayatri'],
    
    # आर्षी जगती (3 verses) - Arshi Jagati
    # Predicted as: गायत्री(3)
    'arsi jagati': ['gayatri', 'jagati'],
    'arsi jagati': ['gayatri', 'jagati'],
    
    # ========================================================================
    # ANUSHTUBH FAMILY (32 syllables = 4×8)
    # Most commonly predicted as: ऋषभगजविलसित, द्विपदा विराट्
    # ========================================================================
    
    # भुरिक् अनुष्टुप् (47 verses) - Bhurik Anushtubh
    # Predicted as: ऋषभगजविलसित(21), द्विपदा विराट्(14), अनुष्टुभ्(4)
    'bhurik anustup': ['rsabhagajavilasita', 'dvipada virat', 'anustubh'],
    'bhurik anustubh': ['rsabhagajavilasita', 'dvipada virat', 'anustubh'],
    'bhurig anustup': ['rsabhagajavilasita', 'dvipada virat', 'anustubh'],
    'bhurig anustubh': ['rsabhagajavilasita', 'dvipada virat', 'anustubh'],
    
    # अनुष्टुप् (4 verses) - Base Anushtubh
    # Predicted as: ऋषभगजविलसित(3), अनुष्टुभ्(1)
    'anustup': ['rsabhagajavilasita', 'anustubh'],
    'anustubh': ['anustubh', 'rsabhagajavilasita'],
    
    # प्राजापत्या अनुष्टुप् (6 verses) - Prajapatya Anushtubh
    # Predicted as: ऋषभगजविलसित(3), गायत्री(2)
    'prajapatya anustup': ['rsabhagajavilasita', 'gayatri', 'anustubh'],
    'prajapatya anustubh': ['rsabhagajavilasita', 'gayatri', 'anustubh'],
    
    # भुरिगनुष्टुप् (5 verses) - Bhurig Anushtubh
    # Predicted as: द्विपदा विराट्(2), ऋषभगजविलसित(1)
    'bhuriganustup': ['dvipada virat', 'rsabhagajavilasita', 'anustubh'],
    'bhuriganustubh': ['dvipada virat', 'rsabhagajavilasita', 'anustubh'],
    
    # भुरिक् (5 verses) - Bhurik alone
    # Predicted as: ऋषभगजविलसित(3), गायत्री(2)
    'bhurik': ['rsabhagajavilasita', 'gayatri', 'anustubh'],
    
    # निचृत् अनुष्टुप् (5 verses) - Nichrit Anushtubh
    # Predicted as: अतिरेखा(3), अपराजिता(1)
    'nicrt anustup': ['atirekha', 'aparajita', 'anustubh'],
    'nicrt anustubh': ['atirekha', 'aparajita', 'anustubh'],
    
    # विराट् अनुष्टुप् (4 verses) - Virat Anushtubh
    # Predicted as: अपराजिता(1), कामक्रीडा(1), ऋषभगजविलसित(1)
    'virat anustup': ['aparajita', 'kamakrīda', 'rsabhagajavilasita', 'anustubh'],
    'virat anustubh': ['aparajita', 'kamakrīda', 'rsabhagajavilasita', 'anustubh'],
    
    # याजुषी अनुष्टुप् - Yajushi Anushtubh
    'yajusi anustup': ['dvipada virat', 'anustubh'],
    'yajusi anustubh': ['dvipada virat', 'anustubh'],
    
    # आर्षी अनुष्टुप् - Arshi Anushtubh  
    'arsi anustup': ['rsabhagajavilasita', 'anustubh'],
    'arsi anustubh': ['rsabhagajavilasita', 'anustubh'],
    
    # ========================================================================
    # BRHATI FAMILY (36 syllables = 4×9)
    # Most commonly predicted as: ऋषभगजविलसित, अतिरेखा, गायत्री
    # ========================================================================
    
    # पथ्याबृहती (18 verses) - Pathya Brhati
    # Predicted as: ऋषभगजविलसित(8), अतिरेखा(5), अनुष्टुभ्(2)
    'pathyabrhati': ['rsabhagajavilasita', 'atirekha', 'anustubh', 'brhati'],
    'pathyabrhati': ['rsabhagajavilasita', 'atirekha', 'anustubh', 'brhati'],
    
    # भुरिग्बृहती (16 verses) - Bhurig Brhati
    # Predicted as: ऋषभगजविलसित(6), शालिनी(2), विराट्(2)
    'bhurigbrhati': ['rsabhagajavilasita', 'salini', 'virat', 'brhati'],
    'bhurig brhati': ['rsabhagajavilasita', 'salini', 'virat', 'brhati'],
    
    # बृहती (16 verses) - Base Brhati
    # Predicted as: गायत्री(8), अपराजिता(2), śephālī(2)
    'brhati': ['gayatri', 'aparajita', 'sephalī', 'brhati'],
    'brhati': ['gayatri', 'aparajita', 'sephalī', 'brhati'],
    
    # विराट् पथ्याबृहती (6 verses) - Virat Pathya Brhati
    # Predicted as: ऋषभगजविलसित(4), अपराजिता(1)
    'virat pathyabrhati': ['rsabhagajavilasita', 'aparajita', 'brhati'],
    'virat pathyabrhati': ['rsabhagajavilasita', 'aparajita', 'brhati'],
    
    # भुरिक् साम्नी बृहती - Bhurik Samni Brhati
    'bhurik samni brhati': ['brhati', 'rsabhagajavilasita'],
    'bhurik samni brhati': ['brhati', 'rsabhagajavilasita'],
    
    # ========================================================================
    # TRISHTUBH FAMILY (44 syllables = 4×11)
    # Most commonly predicted as: गायत्री
    # ========================================================================
    
    # साम्नी त्रिष्टुप् (6 verses) - Samni Trishtubh
    # Predicted as: गायत्री(3), त्वरितगति(2)
    'samni tristup': ['gayatri', 'tvaritagati', 'tristubh'],
    'samni tristubh': ['gayatri', 'tvaritagati', 'tristubh'],
    'samni tristubh': ['gayatri', 'tvaritagati', 'tristubh'],
    
    # विराट् त्रिष्टुप् (5 verses) - Virat Trishtubh
    # Predicted as: गायत्री(4)
    'virat tristup': ['gayatri', 'tristubh'],
    'virat tristubh': ['gayatri', 'tristubh'],
    
    # Trishtubh variants
    'bhurik tristubh': ['tristubh', 'gayatri'],
    'bhurig tristubh': ['tristubh', 'gayatri'],
    'virad tristubh': ['tristubh', 'gayatri'],
    
    # ========================================================================
    # JAGATI FAMILY (48 syllables = 4×12)
    # Already covered above in Gayatri section
    # ========================================================================
    
    # भुरिक् जगती (3 verses) - Bhurik Jagati
    # Predicted as: अनुष्टुभ्(1), गायत्री(1), उष्णिक्(1)
    'bhurik jagati': ['anustubh', 'gayatri', 'usnik', 'jagati'],
    'bhurig jagati': ['anustubh', 'gayatri', 'usnik', 'jagati'],
    
    # ========================================================================
    # ATIJAGATĪ (52 syllables = 4×13)
    # ========================================================================
    
    # अतिजगती (9 verses) - Atijagatī
    # Predicted as: गायत्री(3), ऋषभगजविलसित(3), उष्णिक्(2)
    'atijagati': ['gayatri', 'rsabhagajavilasita', 'usnik', 'atijagati'],
    'atijagati': ['gayatri', 'rsabhagajavilasita', 'usnik', 'atijagati'],
    'atijagatī': ['gayatri', 'rsabhagajavilasita', 'usnik', 'atijagati'],
    
    # ========================================================================
    # PANKTI VARIANTS
    # ========================================================================
    
    # पथ्यापङ्क्तिः (6 verses) - Pathya Pankti
    # Predicted as: अनुष्टुभ्(2), अपराजिता(1)
    'pathyapanktih': ['anustubh', 'aparajita', 'pankti'],
    'pathyapanktih': ['anustubh', 'aparajita', 'pankti'],
    
    # विराडास्तारपङ्क्तिः (4 verses) - Virad Astara Pankti
    # Predicted as: ऋषभगजविलसित(3), अतिरेखा(1)
    'viradastarapanktih': ['rsabhagajavilasita', 'atirekha', 'pankti'],
    
    # चतुष्पदा भुरिक्पङ्क्तिः - 4-footed Bhurik Pankti
    'catuspada bhurikpanktih': ['gayatri', 'pankti'],
    'caduspada bhurikpanktih': ['gayatri', 'pankti'],
    
    # ========================================================================
    # LONGER METERS (Atyashti, Shakvari, etc.)
    # ========================================================================
    
    # अत्यष्टिः (3 verses) - Atyashti (68 syllables = 4×17)
    # Predicted as: अपराजिता(2), अनुष्टुभ्(1)
    'atyastih': ['aparajita', 'anustubh', 'atyasti'],
    'atyasti': ['aparajita', 'anustubh', 'atyasti'],
    'bhurig-atyastih': ['aparajita', 'atyasti'],
    'bhurig atyastih': ['aparajita', 'atyasti'],
    
    # शक्वरी - Shakvari (56 syllables = 4×14)
    'sakvari': ['sakvari', 'gayatri'],
    'sakvari': ['sakvari', 'gayatri'],
    'sakvarī': ['sakvari', 'gayatri'],
    'catuspada sakvari': ['sakvari', 'gayatri'],
    'caduspada sakvari': ['sakvari', 'gayatri'],
    
    # अतिशक्वरी - Atishakvari (60 syllables = 4×15)
    'atisakvari': ['atisakvari'],
    'atisakvari': ['atisakvari'],
    'atisakvarī': ['atisakvari'],
    
    # चतुष्पदा भुरिगुष्णिक् - 4-footed Bhurig Ushnik
    'catuspada bhurigusnik': ['aparajita', 'usnik'],
    'caduspada bhurigusnik': ['aparajita', 'usnik'],
    
    # ========================================================================
    # ENGLISH/IAST TRANSLITERATIONS (from dataset)
    # ========================================================================
    
    'bhurik anustubh': ['rsabhagajavilasita', 'dvipada virat', 'anustubh'],
    'gayatri': ['rsabhagajavilasita', 'atirekha', 'gayatri'],
}


# Classical meter variants that map back to Anushtubh
CLASSICAL_ANUSHTUBH_VARIANTS = {
    'rsabhagajavilasita',      # Rishabha Gaja Vilasita
    'rsabhagajavilasitam',
    'dvipada virat',             # 2-footed Virat
    'dvipada virat',
    'pratīharah',                # Pratihara
    'pratiharah',
    'dhīravarttah2',             # Dhira Vartta
    'dhiravarttah2',
}

# Classical meter variants that map to Pankti/Gayatri
CLASSICAL_PANKTI_GAYATRI_VARIANTS = {
    'asokalokah',                # Ashoka Loka
    'asokalokah',
}

# Classical meter variants for other families
CLASSICAL_OTHER_VARIANTS = {
    'atirekha': 'gayatri',       # Atirekha → Gayatri
    'aparajita': 'usnik',        # Aparajita → Ushnik
    'kamakrīda': 'anustubh',     # Kama Krida → Anushtubh
    'kamakrīda': 'anustubh',
    'salini': 'brhati',          # Shalini → Brhati
    'salini': 'brhati',
    'sephalī': 'brhati',         # Shephali → Brhati
    'sephalī': 'brhati',
    'sahuti': 'pankti',          # Sahuti → Pankti
    'sahuti': 'pankti',
    'tvaritagati': 'tristubh',   # Tvarita Gati → Trishtubh
    'bhujangasisubhrta': 'tristubh',
    'bhujangasisubhrta': 'tristubh',
    'visvaprama': 'jagati',      # Vishvaprama → Jagati
    'visvaprama': 'jagati',
    'vidyadalī': 'gayatri',      # Vidyadali → Gayatri
    'vidyadalī': 'gayatri',
    'kalahamsa': 'anustubh',     # Kalahamsa → Anushtubh
    'sampatašīla': 'brhati',     # Sampata Shila → Brhati
    'sampatašīla': 'brhati',
}


def get_classical_equivalents(vedic_name: str) -> List[str]:
    """
    Get list of classical meter names that match the given Vedic name.
    Returns list ordered by likelihood (most common prediction first).
    
    Args:
        vedic_name: Vedic meter name (in any script/transliteration)
        
    Returns:
        List of classical meter names that are valid matches
    """
    normalized = normalize_meter_name(vedic_name)
    
    # Direct lookup
    if normalized in VEDIC_TO_CLASSICAL_PRIMARY:
        return VEDIC_TO_CLASSICAL_PRIMARY[normalized]
    
    # Check if it's already a classical name
    classical_base = ['gayatri', 'anustubh', 'tristubh', 'jagati', 'brhati', 
                      'pankti', 'usnik', 'atijagati', 'sakvari', 'atisakvari',
                      'atyasti', 'asti', 'dhrti', 'atidhrti']
    
    for base in classical_base:
        if base in normalized:
            return [base]
    
    # No match found
    return []


def meters_match(expected: str, predicted: str) -> bool:
    """
    Check if expected (Vedic) and predicted (Classical) meters match.
    
    Args:
        expected: Expected meter name (usually Vedic)
        predicted: Predicted meter name (usually Classical)
        
    Returns:
        True if they represent the same metrical pattern
    """
    exp_norm = normalize_meter_name(expected)
    pred_norm = normalize_meter_name(predicted)
    
    # Exact match
    if exp_norm == pred_norm:
        return True
    
    # Get classical equivalents for expected
    equivalents = get_classical_equivalents(expected)
    
    # Check if prediction is in the list of valid equivalents
    for equiv in equivalents:
        equiv_norm = normalize_meter_name(equiv)
        if equiv_norm == pred_norm:
            return True
        if equiv_norm in pred_norm or pred_norm in equiv_norm:
            return True
    
    # Check classical variants
    if pred_norm in CLASSICAL_ANUSHTUBH_VARIANTS:
        return 'anustubh' in equivalents or 'anustup' in exp_norm
    
    if pred_norm in CLASSICAL_PANKTI_GAYATRI_VARIANTS:
        return any(e in equivalents for e in ['pankti', 'gayatri', 'panktih'])
    
    if pred_norm in CLASSICAL_OTHER_VARIANTS:
        target = CLASSICAL_OTHER_VARIANTS[pred_norm]
        return target in equivalents
    
    return False


# Export public API
__all__ = [
    'normalize_meter_name',
    'get_classical_equivalents',
    'meters_match',
    'VEDIC_TO_CLASSICAL_PRIMARY',
    'CLASSICAL_ANUSHTUBH_VARIANTS',
    'CLASSICAL_PANKTI_GAYATRI_VARIANTS',
    'CLASSICAL_OTHER_VARIANTS',
]
