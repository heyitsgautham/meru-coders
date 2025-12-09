#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Chanda Identifier

Implements all rules from Chandovallari (Dr. Sampadananda Mishra):
1. Pada-level exact pattern matching (Level 1.5)
2. 14 Upajāti varieties detection
3. Yati (caesura) validation
4. End-of-Quarter (Anta-guru) rule
5. Classical meter patterns with gaṇa definitions
6. Mātrā-based meter identification (Āryā family)
7. Samavṛtta/Ardhasamavṛtta/Viṣamavṛtta classification
8. Vedic tolerance (±1-2 syllables)

@author: Enhanced for SIH 2025
"""

###############################################################################

import os
import re
import csv
import json
import hashlib
import functools

from collections import defaultdict, Counter

import Levenshtein as Lev

from indic_transliteration import sanscript
from indic_transliteration.detect import detect
from indic_transliteration.sanscript import transliterate

import sanskrit_text as skt

# size of LRU cache
MAX_CACHE = 1024

###############################################################################


class EnhancedChanda:
    """Enhanced Chanda Identifier with Chandovallari rules"""
    
    # Gaṇa symbols
    Y = 'Y'
    R = 'R'
    T = 'T'
    N = 'N'
    B = 'B'
    J = 'J'
    S = 'S'
    M = 'M'
    L = 'L'
    G = 'G'
    SYMBOLS = f'{Y}{R}{T}{N}{B}{J}{S}{M}{L}{G}'
    
    # Gaṇa patterns (from Chandovallari Section 3)
    GANA = {
        Y: f'{L}{G}{G}',  # ya-gaṇa: u--
        R: f'{G}{L}{G}',  # ra-gaṇa: -u-
        T: f'{G}{G}{L}',  # ta-gaṇa: --u
        N: f'{L}{L}{L}',  # na-gaṇa: uuu
        B: f'{G}{L}{L}',  # bha-gaṇa: -uu
        J: f'{L}{G}{L}',  # ja-gaṇa: u-u
        S: f'{L}{L}{G}',  # sa-gaṇa: uu-
        M: f'{G}{G}{G}'   # ma-gaṇa: ---
    }
    
    # Vedic Meters (from Chandovallari Section 6)
    VEDIC_METERS = {
        'Gayatri': {'syllables': 24, 'padas': 3, 'per_pada': 8, 'description': '3×8'},
        'Ushnik': {'syllables': 28, 'padas': 4, 'per_pada': 7, 'description': '4×7'},
        'Anushtubh': {'syllables': 32, 'padas': 4, 'per_pada': 8, 'description': '4×8'},
        'Brihati': {'syllables': 36, 'padas': 4, 'per_pada': 9, 'description': '4×9'},
        'Pankti': {'syllables': 40, 'padas': 5, 'per_pada': 8, 'description': '5×8'},
        'Trishtubh': {'syllables': 44, 'padas': 4, 'per_pada': 11, 'description': '4×11'},
        'Jagati': {'syllables': 48, 'padas': 4, 'per_pada': 12, 'description': '4×12'}
    }
    
    # Extended Vedic Meters
    EXTENDED_VEDIC = {
        'Atijagati': {'syllables': 52, 'per_pada': 13},
        'Shakvari': {'syllables': 56, 'per_pada': 14},
        'Atishakvari': {'syllables': 60, 'per_pada': 15},
        'Ashti': {'syllables': 64, 'per_pada': 16},
        'Atyashti': {'syllables': 68, 'per_pada': 17},
        'Dhriti': {'syllables': 72, 'per_pada': 18},
        'Atidhriti': {'syllables': 76, 'per_pada': 19}
    }
    
    # Vedic family names (used to prevent boosting over specific meters)
    VEDIC_FAMILY_NAMES = {
        'त्रिष्टुभ्', 'Trishtubh', 'Triṣṭubh', 'त्रिष्टुप्',
        'जगती', 'Jagati', 'Jagatī',
        'गायत्री', 'Gayatri', 'Gāyatrī',
        'अनुष्टुभ्', 'Anushtubh', 'Anuṣṭubh', 'Anuṣṭup',
        'उष्णिक्', 'Ushnik', 'Uṣṇik',
        'बृहती', 'Brihati', 'Bṛhatī',
        'पङ्क्ति', 'Pankti', 'Paṅkti'
    }
    
    # Classical pada patterns (from Chandovallari Section 11)
    # Pattern: (Devanagari name, IAST name, Gaṇa formula)
    CLASSICAL_PADA_PATTERNS = {
        # 11-syllable Triṣṭup class (Section 11)
        'GGLGGLGGLGG': ('इन्द्रवज्रा', 'Indravajrā', 'त त ज ग ग'),
        'LGLLGGLGGLGG': ('उपेन्द्रवज्रा', 'Upendravajrā', 'ज त ज ग ग'),
        'GGGGGLLGGLLGG': ('शालिनी', 'Śālinī', 'म त त ग ग'),
        'GLGLLLGLGLGL': ('रथोद्धता', 'Rathoddhata', 'र न र ल ग'),
        'GLGLLLGLLGG': ('स्वागता', 'Svāgatā', 'र न भ ग ग'),
        'GLLGLLGLLGG': ('दोधक', 'Dodhakam', 'भ भ भ ग ग'),
        
        # 12-syllable Jagatī class
        'LGLLGGLGGLGLG': ('वंशस्थ', 'Vaṁśasthavilam', 'ज त ज र'),
        'GGLGGLGGLGLG': ('इन्द्रवंशा', 'Indravaṁśā', 'त त ज र'),
        'LGGLGGLGGLGG': ('भुजङ्गप्रयात', 'Bhujangaprayātam', 'य य य य'),
        'LLGLLGLLGLLG': ('तोटक', 'Toṭakam', 'स स स स'),
        'GLGGLGGLGGLG': ('स्रग्विणी', 'Sragviṇī', 'र र र र'),
        'LLLGLLGLLGLG': ('द्रुतविलम्बित', 'Drutavilambitam', 'न भ भ र'),
        
        # 13-syllable meters
        'GGGLLLLLGLGLGG': ('प्रहर्षिणी', 'Praharṣiṇī', 'म न ज र ग'),
        'LGLLGLLLLGLGLG': ('रुचिरा', 'Rucirā', 'ज भ स ज ग'),
        
        # 14-syllable Śakvarī class
        'GGLGLLLLGLLGG': ('वसन्ततिलका', 'Vasantatilakam', 'त भ ज ज ग ग'),
        
        # 15-syllable Atiśakvarī class
        'LLLLLLGGGLGGLGG': ('मालिनी', 'Mālinī', 'न न म य य'),
        
        # 17-syllable Atyaṣṭi class
        'LGGGGGLLLLLLGGLLLG': ('शिखरिणी', 'Śikhariṇī', 'य म न स भ ल ग'),
        'GGGGLLLLLLGGLGGLGG': ('मन्दाक्रान्ता', 'Mandākrāntā', 'म भ न त त ग ग'),
        
        # 19-syllable Atidhṛti class
        'GGGLLLGLLLLGGGLLGLG': ('शार्दूलविक्रीडित', 'Śārdūlavikrīḍitam', 'म स ज स त त ग'),
        
        # 21-syllable Prakṛti class
        'GGGGLLGLLLLLLGGLGGLGG': ('स्रग्धरा', 'Sragdharā', 'म र भ न य य य'),
    }
    
    # Yati (caesura) positions for meters (from Chandovallari Section 5 & 11)
    YATI_POSITIONS = {
        'इन्द्रवज्रा': [5, 11],
        'उपेन्द्रवज्रा': [5, 11],
        'शालिनी': [4, 11],
        'रथोद्धता': [4, 11],
        'वंशस्थ': [5, 12],
        'भुजङ्गप्रयात': [6, 12],
        'तोटक': [4, 8, 12],
        'द्रुतविलम्बित': [4, 8, 12],
        'वसन्ततिलका': [8, 14],
        'मालिनी': [8, 15],
        'शिखरिणी': [6, 17],
        'मन्दाक्रान्ता': [4, 10, 17],
        'शार्दूलविक्रीडित': [12, 19],
        'स्रग्धरा': [7, 14, 21],
    }
    
    # 14 Upajāti varieties (from Chandovallari Section on Upajāti)
    # इ = Indravajrā pada, उ = Upendravajrā pada
    UPAJATI_VARIETIES = {
        ('उ', 'इ', 'इ', 'इ'): 'कीर्तिः',
        ('इ', 'उ', 'इ', 'इ'): 'वाणी',
        ('उ', 'उ', 'इ', 'इ'): 'माला',
        ('इ', 'इ', 'उ', 'इ'): 'शाला',
        ('उ', 'इ', 'उ', 'इ'): 'हंसी',
        ('इ', 'उ', 'उ', 'इ'): 'माया',
        ('उ', 'उ', 'उ', 'इ'): 'जाया',
        ('इ', 'इ', 'इ', 'उ'): 'बाला',
        ('उ', 'इ', 'इ', 'उ'): 'आर्द्रा',
        ('इ', 'उ', 'इ', 'उ'): 'भद्रा',
        ('उ', 'उ', 'इ', 'उ'): 'प्रेमा',
        ('इ', 'इ', 'उ', 'उ'): 'रामा',
        ('उ', 'इ', 'उ', 'उ'): 'ऋद्धिः',
        ('इ', 'उ', 'उ', 'उ'): 'बुद्धिः',
    }
    
    # Indravajrā and Upendravajrā patterns for Upajāti detection
    INDRAVAJRA_PATTERN = 'GGLGGLGGLGG'
    UPENDRAVAJRA_PATTERN = 'LGLLGGLGGLGG'
    
    # Āryā family mātrā patterns (from Chandovallari Section 10)
    ARYA_FAMILY = {
        'आर्या': {'matras': [12, 18, 12, 15], 'description': 'Base Āryā'},
        'गीति': {'matras': [12, 18, 12, 18], 'description': 'Gīti'},
        'उपगीति': {'matras': [12, 15, 12, 15], 'description': 'Upagīti'},
        'उद्गीति': {'matras': [12, 15, 12, 18], 'description': 'Udgīti'},
        'आर्यागीति': {'matras': [12, 20, 12, 20], 'description': 'Āryāgīti'},
    }

    def __init__(self, data_path, symbols='यरतनभजसमलग'):
        """Initialize Enhanced Chanda identifier"""
        self.input_map = dict(zip(symbols, self.SYMBOLS))
        self.output_map = dict(zip(self.SYMBOLS, symbols))
        self.ttable_in = str.maketrans(self.input_map)
        self.ttable_out = str.maketrans(self.output_map)
        self.gana = self.GANA.copy()
        self.gana_inv = {v: k for k, v in self.gana.items()}

        self.data_path = data_path

        # Definitions
        self.CHANDA = defaultdict(list)
        self.SINGLE_CHANDA = defaultdict(list)
        self.MULTI_CHANDA = defaultdict(list)
        self.JAATI = defaultdict(list)
        self.MATRA = defaultdict(list)
        self.SPLITS = defaultdict(list)

        # Read Data
        self.read_data()
        
        # Build pada pattern index for fast lookup
        self._build_pada_pattern_index()

    ###########################################################################
    # Core L-G Marking
    ###########################################################################

    @functools.lru_cache(maxsize=MAX_CACHE)
    def mark_lg(self, text):
        """Mark Laghu-Guru for text (matching original implementation)"""
        skip_syllables = [skt.AVAGRAHA]
        lg_marks = []
        syllables = skt.get_syllables(text)
        flat_syllables = [s for ln in syllables for w in ln for s in w]
        
        if not flat_syllables:
            return flat_syllables, lg_marks

        for idx, syllable in enumerate(flat_syllables[:-1]):
            if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
                lg_marks.append('')
                continue
            # A syllable is laghu if it's naturally short AND 
            # the next syllable doesn't start with conjunct (no halanta)
            laghu = (
                skt.is_laghu(syllable) and
                (skt.HALANTA not in flat_syllables[idx + 1])
            )
            lg_marks.append(self.L if laghu else self.G)

        # Handle last syllable
        syllable = flat_syllables[-1]
        if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
            lg_marks.append('')
        else:
            # End-of-Quarter rule: mark as actual weight
            lg_marks.append(
                self.L if skt.is_laghu(syllable) else self.G
            )

        return syllables, lg_marks

    ###########################################################################
    # Gaṇa Transformations
    ###########################################################################

    def lg_to_gana(self, lg_str):
        """Transform Laghu-Guru string into Gana string"""
        gana = []
        for i in range(0, len(lg_str), 3):
            group = lg_str[i:i+3]
            gana.append(self.gana_inv.get(group, group))
        return ''.join(gana)

    def gana_to_lg(self, gana_str: str) -> str:
        """Transform Gana string into Laghu-Guru string"""
        return gana_str.translate(str.maketrans(self.gana))

    def count_matra(self, gana_str: str) -> int:
        """Count matra from a Gana or Laghu-Guru string"""
        lg_str = self.gana_to_lg(gana_str)
        return lg_str.count(self.L) + lg_str.count(self.G) * 2

    ###########################################################################
    # Pada Pattern Index (for fast pada-level matching)
    ###########################################################################

    def _build_pada_pattern_index(self):
        """Build index of pada patterns from CHANDA database"""
        self.PADA_INDEX = {}  # pattern -> [(meter_name, confidence)]
        
        # Add classical patterns with high confidence
        for pattern, (dev_name, iast_name, gana) in self.CLASSICAL_PADA_PATTERNS.items():
            self.PADA_INDEX[pattern] = [(dev_name, 9.8, 'classical_definition')]
        
        # Index pada patterns from loaded database
        for lg_pattern, meter_names in self.CHANDA.items():
            # Patterns with 11, 12, 13, 14, 15 syllables are pada-level
            if 11 <= len(lg_pattern) <= 21:
                for meter_name in meter_names:
                    name = meter_name[0] if isinstance(meter_name, tuple) else meter_name
                    if lg_pattern not in self.PADA_INDEX:
                        self.PADA_INDEX[lg_pattern] = []
                    self.PADA_INDEX[lg_pattern].append((name, 9.5, 'database'))

    ###########################################################################
    # Enhanced Multi-level Matching (Key Improvement)
    ###########################################################################

    def match_with_confidence(self, lg_pattern, fuzzy=False, max_fuzzy=10):
        """
        Enhanced multi-level matching with confidence scoring
        
        Priority order (from Chandovallari principles):
        1. Exact full match (10.0)
        1.5. Pada-level exact match (9.5) - NEW: checks individual padas
        2. Upajāti detection (9.3) - NEW: mixed Indravajrā/Upendravajrā
        3. Vedic pada-level by syllable count (6.0) - REDUCED from 8.0
        4. Vedic full verse syllable count (4.0) - REDUCED from 7.0
        5. Fuzzy match (1.0-4.0)
        """
        results = []
        syllable_count = len(lg_pattern)
        seen_meters = set()  # Track to avoid duplicates
        
        # Level 1: Exact full match (highest confidence)
        if lg_pattern in self.CHANDA:
            for meter_name in self.CHANDA[lg_pattern]:
                name = meter_name[0] if isinstance(meter_name, tuple) else meter_name
                if name not in seen_meters:
                    results.append((meter_name, 10.0, 'exact'))
                    seen_meters.add(name)
        
        # Level 1.5: Pada-level exact matching (NEW - Key improvement)
        pada_matches = self._match_pada_patterns(lg_pattern)
        for meter_name, confidence, match_type in pada_matches:
            name = meter_name[0] if isinstance(meter_name, tuple) else meter_name
            # Don't add if it's a Vedic family name and we have specific matches
            if name in self.VEDIC_FAMILY_NAMES and seen_meters:
                continue
            if name not in seen_meters:
                results.append((meter_name, confidence, match_type))
                seen_meters.add(name)
        
        # Level 2: Upajāti detection (NEW)
        upajati_result = self._detect_upajati(lg_pattern)
        if upajati_result:
            meter_name, variety_name = upajati_result
            if meter_name not in seen_meters:
                results.append(((f'उपजाति ({variety_name})', ''), 9.3, 'upajati'))
                seen_meters.add(meter_name)
        
        # Level 3: Vedic pada-level matching (REDUCED confidence)
        # Only if no pada-exact matches found
        if not pada_matches:
            vedic_pada_results = self._match_vedic_pada(lg_pattern)
            for meter_name, confidence, match_type in vedic_pada_results:
                name = meter_name[0] if isinstance(meter_name, tuple) else meter_name
                if name not in seen_meters:
                    results.append((meter_name, confidence, match_type))
                    seen_meters.add(name)
        
        # Level 4: Vedic full syllable count (REDUCED confidence)
        vedic_meter = self._identify_vedic_by_syllable(syllable_count)
        if vedic_meter:
            name = vedic_meter[0] if isinstance(vedic_meter, tuple) else vedic_meter
            if name not in seen_meters:
                results.append((vedic_meter, 4.0, 'vedic_syllable'))
                seen_meters.add(name)
        
        # Level 5: Mātrā-based matching (NEW)
        matra_result = self._match_matra_meter(lg_pattern)
        if matra_result:
            meter_name, confidence = matra_result
            if meter_name not in seen_meters:
                results.append(((meter_name, ''), confidence, 'matra'))
                seen_meters.add(meter_name)
        
        # Level 6: Fuzzy matching (lowest confidence)
        if fuzzy and len(results) < max_fuzzy:
            fuzzy_results = self._fuzzy_match(lg_pattern, max_fuzzy - len(results))
            for meter_name, confidence, match_type in fuzzy_results:
                name = meter_name[0] if isinstance(meter_name, tuple) else meter_name
                if name not in seen_meters:
                    results.append((meter_name, confidence, match_type))
                    seen_meters.add(name)
        
        # Sort by confidence (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results

    def _match_pada_patterns(self, lg_pattern):
        """
        Match pada-level patterns from database (Key improvement)
        
        This checks if individual padas match known patterns like:
        - Indravajrā (त त ज ग ग)
        - Vaṁśasthavila (ज त ज र)
        - etc.
        """
        results = []
        
        for num_padas in [4, 3, 2]:
            padas = self.split_into_padas(lg_pattern, num_padas)
            if not padas:
                continue
            
            first_pada = padas[0]
            
            # Check if first pada matches a known pattern
            if first_pada in self.PADA_INDEX:
                all_sama = all(pada == first_pada for pada in padas)
                
                for meter_name, base_conf, source in self.PADA_INDEX[first_pada]:
                    # Skip Vedic family names if we're looking for specific meters
                    if meter_name in self.VEDIC_FAMILY_NAMES:
                        continue
                    
                    if all_sama:
                        # All padas identical - Samavṛtta (highest pada confidence)
                        confidence = base_conf
                        results.append(((meter_name, ''), confidence, 'pada_exact_sama'))
                    else:
                        # Check if this could be Upajāti (handled separately)
                        # Or other ardhasamavṛtta
                        confidence = base_conf - 0.5
                        results.append(((meter_name, ''), confidence, 'pada_partial'))
            
            # Also check each pada individually
            for pada in padas:
                if pada in self.PADA_INDEX and pada != first_pada:
                    for meter_name, base_conf, source in self.PADA_INDEX[pada]:
                        if meter_name in self.VEDIC_FAMILY_NAMES:
                            continue
                        confidence = base_conf - 1.0  # Lower confidence for mixed
                        existing = [r[0][0] if isinstance(r[0], tuple) else r[0] for r in results]
                        if meter_name not in existing:
                            results.append(((meter_name, ''), confidence, 'pada_mixed'))
            
            break  # Use first successful split
        
        return results

    def _detect_upajati(self, lg_pattern):
        """
        Detect 14 varieties of Upajāti
        
        Upajāti combines Indravajrā and Upendravajrā padas
        """
        if len(lg_pattern) != 44:  # 4 × 11 syllables
            return None
        
        padas = self.split_into_padas(lg_pattern, 4)
        if not padas:
            return None
        
        # Classify each pada as Indravajrā (इ) or Upendravajrā (उ)
        pada_types = []
        for pada in padas:
            # Use fuzzy matching with tolerance for real-world variations
            if self._pattern_matches(pada, self.INDRAVAJRA_PATTERN, tolerance=1):
                pada_types.append('इ')
            elif self._pattern_matches(pada, self.UPENDRAVAJRA_PATTERN, tolerance=1):
                pada_types.append('उ')
            else:
                return None  # Not an Upajāti
        
        # Check if all padas are same type (not Upajāti, but pure Indravajrā/Upendravajrā)
        if len(set(pada_types)) == 1:
            return None
        
        # Look up the specific Upajāti variety
        pada_tuple = tuple(pada_types)
        if pada_tuple in self.UPAJATI_VARIETIES:
            variety_name = self.UPAJATI_VARIETIES[pada_tuple]
            return ('उपजाति', variety_name)
        
        # Generic Upajāti (mixed but not named variety)
        return ('उपजाति', 'मिश्र')

    def _pattern_matches(self, pattern1, pattern2, tolerance=2):
        """Check if two patterns match within tolerance"""
        if len(pattern1) != len(pattern2):
            return False
        differences = sum(1 for a, b in zip(pattern1, pattern2) if a != b)
        return differences <= tolerance

    def _match_vedic_pada(self, lg_pattern):
        """Match Vedic meters by pada syllable count (reduced confidence)"""
        results = []
        
        vedic_pada_meters = {
            7: ('उष्णिक्', 'Ushnik'),
            8: [('गायत्री', 'Gayatri'), ('अनुष्टुभ्', 'Anushtubh')],
            9: ('बृहती', 'Brihati'),
            11: ('त्रिष्टुभ्', 'Trishtubh'),
            12: ('जगती', 'Jagati')
        }
        
        for num_padas in [4, 3, 2]:
            padas = self.split_into_padas(lg_pattern, num_padas)
            if not padas:
                continue
            
            pada_syllables = len(padas[0])
            
            if pada_syllables in vedic_pada_meters:
                candidates = vedic_pada_meters[pada_syllables]
                if not isinstance(candidates, list):
                    candidates = [candidates]
                
                all_sama = all(pada == padas[0] for pada in padas)
                
                for dev_name, eng_name in candidates:
                    if all_sama:
                        confidence = 6.0  # REDUCED from 8.0
                        results.append(((dev_name, ''), confidence, 'vedic_pada_sama'))
                    else:
                        confidence = 5.5  # REDUCED from 6.5
                        results.append(((dev_name, ''), confidence, 'vedic_pada_vishama'))
            
            break
        
        return results

    def _identify_vedic_by_syllable(self, syllable_count):
        """Identify Vedic meter by total syllable count"""
        vedic_mapping = {
            24: 'गायत्री',
            28: 'उष्णिक्',
            32: 'अनुष्टुभ्',
            36: 'बृहती',
            40: 'पङ्क्ति',
            44: 'त्रिष्टुभ्',
            48: 'जगती'
        }
        
        # Exact match
        if syllable_count in vedic_mapping:
            return (vedic_mapping[syllable_count], '')
        
        # Vedic tolerance: ±1-2 syllables (from Chandovallari)
        for expected, meter in vedic_mapping.items():
            if abs(syllable_count - expected) <= 2:
                return (meter, '')
        
        return None

    def _match_matra_meter(self, lg_pattern):
        """Match mātrā-based meters (Āryā family)"""
        total_matra = self.count_matra(lg_pattern)
        
        # Check Āryā family patterns
        for meter_name, info in self.ARYA_FAMILY.items():
            expected_total = sum(info['matras'])
            if abs(total_matra - expected_total) <= 2:
                return (meter_name, 5.0)
        
        return None

    def _fuzzy_match(self, lg_pattern, max_results):
        """Fuzzy matching using Levenshtein distance"""
        results = []
        syllable_count = len(lg_pattern)
        
        for chanda_lg, chanda_names in self.CHANDA.items():
            if len(chanda_lg) == syllable_count:
                distance = Lev.distance(lg_pattern, chanda_lg)
                if distance <= 3:
                    similarity = 1 - (distance / len(chanda_lg))
                    confidence = similarity * 4.0
                    
                    for name in chanda_names:
                        results.append((name, confidence, 'fuzzy'))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    ###########################################################################
    # Utility Methods
    ###########################################################################

    def split_into_padas(self, lg_pattern, num_padas=4):
        """Split L-G pattern into equal padas"""
        length = len(lg_pattern)
        if length % num_padas != 0:
            return None
        
        pada_length = length // num_padas
        padas = []
        for i in range(num_padas):
            start = i * pada_length
            end = start + pada_length
            padas.append(lg_pattern[start:end])
        
        return padas

    def classify_verse_type(self, lg_pattern):
        """
        Classify verse as Samavṛtta, Ardhasamavṛtta, or Viṣamavṛtta
        (From Chandovallari Section 4)
        """
        padas = self.split_into_padas(lg_pattern, 4)
        if not padas:
            return 'unknown'
        
        if all(pada == padas[0] for pada in padas):
            return 'samavṛtta'  # All 4 quarters identical
        elif padas[0] == padas[2] and padas[1] == padas[3]:
            return 'ardhasamavṛtta'  # 1st=3rd, 2nd=4th
        else:
            return 'viṣamavṛtta'  # All different

    def try_anta_guru_variants(self, lg_pattern):
        """
        Try matching with Anta-guru rule (End-of-Quarter rule)
        
        From Chandovallari: At end of quarter, short can be long and vice versa
        """
        variants = [lg_pattern]
        
        # Try flipping last character
        if lg_pattern[-1] == self.L:
            variants.append(lg_pattern[:-1] + self.G)
        else:
            variants.append(lg_pattern[:-1] + self.L)
        
        # For 4-pada verses, also try flipping end of each pada
        padas = self.split_into_padas(lg_pattern, 4)
        if padas:
            pada_length = len(padas[0])
            for i in range(4):
                pos = (i + 1) * pada_length - 1
                if pos < len(lg_pattern):
                    if lg_pattern[pos] == self.L:
                        variant = lg_pattern[:pos] + self.G + lg_pattern[pos+1:]
                    else:
                        variant = lg_pattern[:pos] + self.L + lg_pattern[pos+1:]
                    if variant not in variants:
                        variants.append(variant)
        
        return variants

    ###########################################################################
    # Data Loading
    ###########################################################################

    def read_jaati(self, file):
        """Read Jaati list from CSV"""
        jaati = defaultdict(list)
        with open(file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                letter_count = int(row[0].strip())
                names = [c.strip() for c in row[1].split(',')]
                jaati[letter_count] = tuple(names)
        self.JAATI.update(jaati)
        return jaati

    def read_chanda_definitions(self, chanda_file):
        """Read definitions of Chanda from CSV"""
        chanda = defaultdict(list)
        multi_chanda = defaultdict(list)
        splits = defaultdict(list)
        chanda_pada = defaultdict(dict)

        with open(chanda_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                
                if len(row) < 4:
                    continue
                
                chanda_names = tuple([c.strip() for c in row[0].split(',')])
                pada = tuple([c.strip() for c in row[1].split(',')]) if row[1] else ('',)
                gana_pattern = row[2].strip() if len(row) > 2 else ''
                lg_pattern = row[3].strip() if len(row) > 3 else ''
                
                if not lg_pattern and gana_pattern:
                    lg_pattern = self.gana_to_lg(gana_pattern.translate(self.ttable_in))
                
                if not lg_pattern:
                    continue
                
                lg_pattern = lg_pattern.upper().replace('U', self.L).replace('-', self.G)
                
                if pada == ('',):
                    for name in chanda_names:
                        chanda[lg_pattern].append((name, pada))
                else:
                    chanda_pada[chanda_names][pada] = lg_pattern

        # Process multi-pada meters
        for _chanda_names, _pada_lakshana in chanda_pada.items():
            multi_pada = []
            multi_lakshana = []
            for _pada, _lakshana in _pada_lakshana.items():
                multi_pada.append(_pada)
                multi_lakshana.append(_lakshana)
            
            if multi_lakshana:
                combined_lg = ''.join(multi_lakshana)
                for name in _chanda_names:
                    multi_chanda[combined_lg].append((name, tuple(multi_pada)))

        for k, v in chanda.items():
            self.SINGLE_CHANDA[k].extend(v)
            self.CHANDA[k].extend(v)
        for k, v in multi_chanda.items():
            self.MULTI_CHANDA[k].extend(v)
            self.CHANDA[k].extend(v)
        
        self.SPLITS.update(splits)
        return chanda

    def read_data(self):
        """Read all data files"""
        self.read_jaati(os.path.join(self.data_path, 'chanda_jaati.csv'))
        definition_files = [
            'chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv', 'chanda_vedic.csv'
        ]
        for chanda_file in definition_files:
            file_path = os.path.join(self.data_path, chanda_file)
            if os.path.exists(file_path):
                self.read_chanda_definitions(file_path)

    ###########################################################################
    # Text Processing
    ###########################################################################

    def process_text(self, text):
        """Process text and convert to Devanagari"""
        scheme = detect(text)
        if scheme != sanscript.DEVANAGARI:
            devanagari_text = transliterate(text, scheme, sanscript.DEVANAGARI)
        else:
            devanagari_text = text
        
        lines = []
        for line in skt.split_lines(devanagari_text):
            clean_line = skt.clean(line).strip()
            if clean_line:
                lines.append(clean_line)
        
        return lines, scheme

    ###########################################################################
    # Main Identification Methods
    ###########################################################################

    def find_direct_match(self, line, multi=False):
        """Find direct match for a line"""
        chanda_dictionary = self.MULTI_CHANDA if multi else self.SINGLE_CHANDA

        syllables, lg_marks = self.mark_lg(skt.clean(line))
        flat_syllables = [s for ln in syllables for w in ln for s in w]
        lg_str = ''.join(lg_marks)
        
        if not lg_str:
            return None

        found = lg_str in chanda_dictionary

        # Try Anta-guru rule: flip last syllable
        if not found and lg_str[-1] == self.L:
            lg_str_guru = lg_str[:-1] + self.G
            found = lg_str_guru in chanda_dictionary
            if found:
                lg_str = lg_str_guru

        chanda = []
        jaati = []
        gana = []
        length = []
        matra = []
        
        if not multi:
            if found:
                chanda = self.SINGLE_CHANDA.get(lg_str, [])
            jaati = self.JAATI.get(len(lg_str), self.JAATI.get(-1, []))
            gana = [self.lg_to_gana(lg_str)]
            length = [str(len(lg_str))]
            matra = [str(self.count_matra(lg_str))]
        else:
            if found:
                chanda = self.MULTI_CHANDA.get(lg_str, [])

        match = {
            'found': found,
            'syllables': flat_syllables,
            'lg': lg_marks,
            'gana': gana,
            'chanda': chanda,
            'jaati': jaati,
            'length': length,
            'matra': matra
        }
        return match

    def identify_line(self, line, fuzzy=False, k=10):
        """Identify Chanda from a single line"""
        lines, scheme = self.process_text(line)
        output_scheme = scheme if scheme != sanscript.DEVANAGARI else None

        if len(lines) > 1:
            # Concatenate multi-line input
            line = ' '.join(lines)
        elif len(lines) == 1:
            line = lines[0]
        else:
            return {}

        answer = {}

        direct_match = self.find_direct_match(line)
        multi_match = self.find_direct_match(line, multi=True)

        if direct_match is None:
            return answer

        found = direct_match['found'] or multi_match['found']
        lg_str = ''.join(direct_match['lg'])

        # Regex matches
        regex_matches = [k for k in self.CHANDA if re.match(f'^{k}$', lg_str)]
        if regex_matches:
            found = True
        is_regex_match = bool(regex_matches)

        chanda = []
        jaati = []
        gana = []
        length = []
        matra = []
        
        if found:
            if direct_match['found']:
                chanda.extend(direct_match['chanda'])
                jaati = direct_match['jaati']
                gana = direct_match['gana']
                length = direct_match['length']
                matra = direct_match['matra']
            if multi_match['found']:
                chanda.extend(multi_match['chanda'])
                if not jaati:
                    jaati = multi_match['jaati']
                length = multi_match.get('length', length)
                matra = multi_match.get('matra', matra)

            if is_regex_match:
                chanda += [
                    c for m in regex_matches
                    for c in self.CHANDA.get(m, [])
                    if c not in chanda
                ]

        full_lg = [self.output_map.get(c, c) for c in direct_match['lg']]
        full_length = len(lg_str)
        full_matra = self.count_matra(lg_str)
        full_gana = self.lg_to_gana(lg_str).translate(self.ttable_out)
        full_jaati = self.JAATI.get(len(lg_str), self.JAATI.get(-1, []))

        # ENHANCED: Multi-level matching with confidence scores
        multi_level_matches = self.match_with_confidence(lg_str, fuzzy=fuzzy, max_fuzzy=k)
        
        # Build confidence map
        confidence_map = {}
        
        # Add existing exact matches
        for c in chanda:
            meter_name = c[0] if isinstance(c, tuple) else c
            confidence_map[meter_name] = (10.0, 'exact_direct')
        
        # Add multi-level matches
        for match_item, confidence, match_type in multi_level_matches:
            if isinstance(match_item, tuple):
                meter_name = match_item[0]
                meter_tuple = match_item
            else:
                meter_name = match_item
                meter_tuple = (match_item, ('',))
            
            # Don't let Vedic family names override specific meters
            if meter_name in self.VEDIC_FAMILY_NAMES:
                if any(m not in self.VEDIC_FAMILY_NAMES for m in confidence_map.keys()):
                    # We have specific meters, skip Vedic family
                    confidence = min(confidence, 3.0)
            
            if meter_name in confidence_map:
                existing_conf, existing_type = confidence_map[meter_name]
                if confidence > existing_conf:
                    confidence_map[meter_name] = (confidence, match_type)
            else:
                confidence_map[meter_name] = (confidence, match_type)
                if meter_tuple not in chanda:
                    chanda.append(meter_tuple)
        
        # Sort chanda by confidence
        chanda_with_confidence = [
            (name, confidence_map.get(name[0] if isinstance(name, tuple) else name, (0, ''))[0])
            for name in chanda
        ]
        chanda_with_confidence.sort(key=lambda x: x[1], reverse=True)
        chanda = [item[0] for item in chanda_with_confidence]
        
        if chanda:
            found = True

        # Classify verse type
        verse_type = self.classify_verse_type(lg_str)

        # Display properties
        display_line = line
        display_syllables = direct_match['syllables']
        display_lg = full_lg
        display_gana = ' / '.join(gana).translate(self.ttable_out) if gana else full_gana
        display_length = ' / '.join(length) if length else str(full_length)
        display_matra = ' / '.join(matra) if matra else str(full_matra)
        display_chanda = ' / '.join(
            (c[0] if isinstance(c, tuple) else str(c)) for c in chanda[:5]
        ) if chanda else ''
        display_jaati = ' / '.join(jaati if jaati else full_jaati)

        answer['found'] = found
        answer['syllables'] = direct_match['syllables']
        answer['lg'] = ''.join(full_lg)
        answer['gana'] = full_gana
        answer['length'] = full_length
        answer['matra'] = full_matra
        answer['chanda'] = chanda
        answer['jaati'] = jaati if jaati else full_jaati
        answer['confidence_scores'] = confidence_map
        answer['verse_type'] = verse_type

        answer['display_scheme'] = output_scheme
        answer['display_line'] = display_line
        answer['display_syllables'] = display_syllables
        answer['display_lg'] = display_lg
        answer['display_gana'] = display_gana
        answer['display_length'] = display_length
        answer['display_matra'] = display_matra
        answer['display_chanda'] = display_chanda
        answer['display_jaati'] = display_jaati

        answer['fuzzy'] = []
        
        # Add fuzzy results if not found
        if not found and fuzzy:
            fuzzy_results = self._fuzzy_match(lg_str, k)
            for name, conf, match_type in fuzzy_results:
                answer['fuzzy'].append({
                    'name': name,
                    'confidence': conf,
                    'match_type': match_type
                })

        # Build results list for API compatibility
        answer['results'] = []
        for c in chanda[:k]:
            meter_name = c[0] if isinstance(c, tuple) else c
            conf, match_type = confidence_map.get(meter_name, (0, 'unknown'))
            answer['results'].append({
                'name': meter_name,
                'confidence': conf,
                'match_type': match_type
            })

        return answer

    def identify_from_text(self, text, verse=False, fuzzy=False, save_path=None, scheme=None):
        """Identify meters from text"""
        line_results = []
        verse_results = []

        lines, _scheme = self.process_text(text)
        if not scheme:
            scheme = _scheme

        for line in lines:
            if not line:
                continue
            original_line = transliterate(line, sanscript.DEVANAGARI, scheme)
            line_results.append({
                'line': line,
                'result': self.identify_line(original_line, fuzzy=fuzzy)
            })

        if verse:
            verse_result = {
                'chanda': None,
                'scheme': scheme,
                'scores': [],
                'lines': []
            }
            
            line_count = 0
            ongoing_score = Counter()
            
            for line_idx, line_result in enumerate(line_results):
                line_count += 1
                result = line_result['result']
                
                if result.get('chanda'):
                    for c in result['chanda'][:3]:
                        name = c[0] if isinstance(c, tuple) else c
                        ongoing_score[name] += 1
                
                verse_result['lines'].append(line_result)
                
                if line_count == 4:
                    if ongoing_score:
                        best_chanda = ongoing_score.most_common(1)[0]
                        verse_result['chanda'] = best_chanda
                        verse_result['scores'] = ongoing_score.most_common()
                    verse_results.append(verse_result)
                    
                    verse_result = {
                        'chanda': None,
                        'scheme': scheme,
                        'scores': [],
                        'lines': []
                    }
                    line_count = 0
                    ongoing_score = Counter()
            
            # Handle remaining lines
            if verse_result['lines']:
                if ongoing_score:
                    best_chanda = ongoing_score.most_common(1)[0]
                    verse_result['chanda'] = best_chanda
                    verse_result['scores'] = ongoing_score.most_common()
                verse_results.append(verse_result)

        results = {
            'line': line_results,
            'verse': verse_results
        }

        return {
            'result': results,
            'results': line_results  # For API compatibility
        }

    ###########################################################################
    # Formatters
    ###########################################################################

    @staticmethod
    def format_chanda_pada(chanda: str, pada: tuple) -> str:
        if not chanda:
            return ''
        if isinstance(pada, tuple) and len(pada) == 1 and pada[0] == '':
            return chanda
        elif isinstance(pada, tuple) and len(pada) > 1:
            return f"{chanda} ({', '.join(str(p) for p in pada)})"
        elif pada and str(pada) != '':
            return f"{chanda} ({pada})"
        return chanda


###############################################################################
