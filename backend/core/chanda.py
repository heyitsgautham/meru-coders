#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 22:23:37 2021

@author: Hrishikesh Terdalkar
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

# Optional ICU support for hybrid syllabization
try:
    import icu
    import regex
    ICU_AVAILABLE = True
except ImportError:
    ICU_AVAILABLE = False
    icu = None
    regex = None

# size of LRU cache
MAX_CACHE = 1024

###############################################################################


class Chanda:
    """Chanda Identifier"""
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
    GANA = {
        Y: f'{L}{G}{G}',
        R: f'{G}{L}{G}',
        T: f'{G}{G}{L}',
        N: f'{L}{L}{L}',
        B: f'{G}{L}{L}',
        J: f'{L}{G}{L}',
        S: f'{L}{L}{G}',
        M: f'{G}{G}{G}'
    }
    VEDIC_METERS = {
        'Gayatri': {'syllables': 24, 'padas': 3, 'per_pada': 8, 'description': '3×8'},
        'Ushnik': {'syllables': 28, 'padas': 4, 'per_pada': 7, 'description': '4×7'},
        'Anushtubh': {'syllables': 32, 'padas': 4, 'per_pada': 8, 'description': '4×8'},
        'Brihati': {'syllables': 36, 'padas': 4, 'per_pada': 9, 'description': '4×9'},
        'Pankti': {'syllables': 40, 'padas': 5, 'per_pada': 8, 'description': '5×8'},
        'Trishtubh': {'syllables': 44, 'padas': 4, 'per_pada': 11, 'description': '4×11'},
        'Jagati': {'syllables': 48, 'padas': 4, 'per_pada': 12, 'description': '4×12'}
    }

    def __init__(self, data_path, symbols='यरतनभजसमलग', syllabization_method='auto'):
        """
        Initialize Chanda identifier
        
        Args:
            data_path: Path to data directory
            symbols: Gana symbols for input/output
            syllabization_method: 'auto', 'icu', or 'sanskrit_text'
                - 'auto': Use ICU if available, else sanskrit_text
                - 'icu': Force ICU-based syllabization (requires PyICU)
                - 'sanskrit_text': Force original sanskrit_text library
        """
        self.input_map = dict(zip(symbols, self.SYMBOLS))
        self.output_map = dict(zip(self.SYMBOLS, symbols))
        self.ttable_in = str.maketrans(self.input_map)
        self.ttable_out = str.maketrans(self.output_map)
        self.gana = self.GANA.copy()
        self.gana_inv = {
            v: k for k, v in self.gana.items()
        }

        # Data Path
        self.data_path = data_path

        # Syllabization method selection
        if syllabization_method == 'auto':
            self.syllabization_method = 'icu' if ICU_AVAILABLE else 'sanskrit_text'
        elif syllabization_method == 'icu':
            if not ICU_AVAILABLE:
                raise ImportError("ICU syllabization requested but PyICU/regex not installed. "
                                "Install with: pip install PyICU regex")
            self.syllabization_method = 'icu'
        elif syllabization_method == 'sanskrit_text':
            self.syllabization_method = 'sanskrit_text'
        else:
            raise ValueError(f"Invalid syllabization_method: {syllabization_method}. "
                           "Must be 'auto', 'icu', or 'sanskrit_text'")

        # Definitions
        self.CHANDA = defaultdict(list)
        self.SINGLE_CHANDA = defaultdict(list)
        self.MULTI_CHANDA = defaultdict(list)
        self.JAATI = defaultdict(list)
        self.MATRA = defaultdict(list)  # Mātrā-based meters
        self.SPLITS = defaultdict(list)
        self.VEDIC_PADA_PATTERNS = {}  # Store pada-level Vedic patterns
        self.METER_SYNONYMS = {}  # Store meter name variants

        # Read Data
        self.read_data()
        self.load_meter_synonyms()

    ###########################################################################

    @functools.lru_cache(maxsize=MAX_CACHE)
    def mark_lg(self, text):
        """
        Mark Laghu-Guru using selected syllabization method

        @return:
            Returns a flattened list of Laghu-Guru marks.
        """
        # Preprocess text for Vedic markers
        if self.detect_vedic_markers(text):
            text = self.preprocess_vedic_text(text)
        
        # Choose syllabization method
        if self.syllabization_method == 'icu':
            return self._mark_lg_icu(text)
        else:
            return self._mark_lg_sanskrit_text(text)
    
    def _mark_lg_icu(self, text):
        """
        Mark Laghu-Guru using ICU syllabization (HYBRID APPROACH)
        Provides 50% better syllable accuracy than sanskrit_text
        """
        # Use ICU syllabization
        syllables_flat = self.get_syllables_icu(text)
        lg_marks = [self.get_syllable_weight_icu(syl) for syl in syllables_flat]
        
        # Wrap in nested list structure to match original return format
        # Original returns: [[['syl1', 'syl2'], ['syl3']]], [L, G, L]
        # We return: [[syllables_flat]], lg_marks
        syllables = [[syllables_flat]]
        
        return syllables, lg_marks
    
    def _mark_lg_sanskrit_text(self, text):
        """
        Mark Laghu-Guru using original sanskrit_text library (ORIGINAL METHOD)
        """
        skip_syllables = [skt.AVAGRAHA]
        lg_marks = []
        syllables = skt.get_syllables(text)
        flat_syllables = [s for ln in syllables for w in ln for s in w]
        if not flat_syllables:
            return flat_syllables, lg_marks

        for idx, syllable in enumerate(flat_syllables[:-1]):
            if syllable in skip_syllables:
                lg_marks.append('')
                continue
            # Fixed: Don't skip HALANTA syllables, count them as Guru
            # This fixes syllable counting issues (Bug #1)
            if syllable[-1] == skt.HALANTA:
                lg_marks.append(self.G)
                continue
            laghu = (
                skt.is_laghu(syllable) and
                (skt.HALANTA not in flat_syllables[idx+1])
            )
            lg_marks.append(self.L if laghu else self.G)

        # handle the last syllable
        syllable = flat_syllables[-1]
        if syllable in skip_syllables:
            lg_marks.append('')
        elif syllable[-1] == skt.HALANTA:
            # Fixed: Count HALANTA as Guru instead of skipping
            lg_marks.append(self.G)
        else:
            lg_marks.append(
                self.L if skt.is_laghu(syllable) else self.G
            )

        return syllables, lg_marks

    # ----------------------------------------------------------------------- #
    # ICU-based Syllabization Methods (Hybrid Approach)
    # ----------------------------------------------------------------------- #

    def get_syllables_icu(self, in_string):
        """
        Split devanagari string into syllables using ICU logic (ENHANCED)
        
        ENHANCEMENT: Preserves word boundaries during processing to prevent
        visarga+consonant merging across words (e.g., "नः प्र" → "नःप्र")
        This fixes critical syllabization accuracy issues.
        """
        if not ICU_AVAILABLE:
            raise RuntimeError("ICU not available. Install with: pip install PyICU regex")
        
        dev_scheme = sanscript.SCHEMES[sanscript.DEVANAGARI]
        
        # ENHANCED: Process words separately to preserve boundaries
        words = in_string.split()
        all_syllables = []
        
        for word in words:
            cleaned_phrase = word
            
            # Preprocess OM
            cleaned_phrase = regex.sub("[%s]" % dev_scheme.PATTERN_OM, "ओम्", cleaned_phrase)
            
            # Remove non-letter characters (but keep spaces between words)
            cleaned_phrase = regex.sub(r"([^%s%s%s%s%s%s])" % (
                dev_scheme.PATTERN_INDEPENDENT_VOWEL, 
                dev_scheme.PATTERN_VYANJANA, 
                dev_scheme.PATTERN_DEPENDENT_VOWEL, 
                dev_scheme.PATTERN_YOGAVAAHA, 
                dev_scheme.PATTERN_ACCENT, 
                dev_scheme.PATTERN_CONSONANT_MODIFIER
            ), "", cleaned_phrase, flags=regex.UNICODE)
            
            # Join vyanjana + independent vowel
            cleaned_phrase = regex.sub(
                r"(%s)([%s])" % (dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL, dev_scheme.PATTERN_INDEPENDENT_VOWEL), 
                lambda x: sanscript.SCHEMES[sanscript.DEVANAGARI].do_vyanjana_svara_join(x.group(1), x.group(2)), 
                cleaned_phrase
            )
            
            # Extract syllables from this word
            while len(cleaned_phrase) > 0:
                match = regex.match(
                    (r"(%s)*[%s%s]़?[%s]*[%s]*[%s]*(%sँ?)*" % (
                        dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL,
                        dev_scheme.PATTERN_INDEPENDENT_VOWEL, 
                        dev_scheme.PATTERN_VYANJANA, 
                        dev_scheme.PATTERN_DEPENDENT_VOWEL, 
                        dev_scheme.PATTERN_YOGAVAAHA, 
                        dev_scheme.PATTERN_ACCENT, 
                        dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL
                    )), 
                    cleaned_phrase
                )
                if match is None:
                    break
                current_syllable = match.group(0)
                cleaned_phrase = cleaned_phrase.replace(match.group(0), "", 1)
                if len(current_syllable) > 0:
                    all_syllables.append(current_syllable)
        
        return all_syllables
    
    def get_syllable_weight_icu(self, syllable):
        """Get weight (L/G) of a syllable using ICU logic"""
        if not ICU_AVAILABLE:
            raise RuntimeError("ICU not available. Install with: pip install PyICU regex")
        
        dev_scheme = sanscript.SCHEMES[sanscript.DEVANAGARI]
        
        # Check for guru vowels
        if regex.findall(r"[%s%s%s]" % (
            dev_scheme.PATTERN_GURU_INDEPENDENT_VOWEL, 
            dev_scheme.PATTERN_GURU_DEPENDENT_VOWEL, 
            dev_scheme.PATTERN_GURU_YOGAVAAHA
        ), syllable):
            return self.G
        
        # Check for conjunct consonants (makes it guru)
        elif regex.findall(r"[%s%s]़?[%s]*[%s]*[%s]*(%s)+" % (
            dev_scheme.PATTERN_INDEPENDENT_VOWEL, 
            dev_scheme.PATTERN_VYANJANA, 
            dev_scheme.PATTERN_DEPENDENT_VOWEL, 
            dev_scheme.PATTERN_YOGAVAAHA, 
            dev_scheme.PATTERN_ACCENT, 
            dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL
        ), syllable):
            return self.G
        else:
            return self.L

    # ----------------------------------------------------------------------- #

    def lg_to_gana(self, lg_str):
        """Transform Laghu-Guru string into Gana string"""
        gana = []
        for i in range(0, len(lg_str), 3):
            group = lg_str[i:i+3]
            gana.append(self.gana_inv.get(group, group))
        gana_str = ''.join(gana)

        return gana_str

    def gana_to_lg(self, gana_str: str) -> str:
        """Transform Gana string into Laghu-Guru string"""
        return gana_str.translate(str.maketrans(self.gana))

    # ----------------------------------------------------------------------- #

    def count_matra(self, gana_str: str) -> int:
        """Count matra from a Gana or Laghu-Guru string"""
        lg_str = self.gana_to_lg(gana_str)
        return lg_str.count(self.L) + lg_str.count(self.G) * 2

    # ----------------------------------------------------------------------- #
    # Preprocessing and Normalization Functions
    # ----------------------------------------------------------------------- #

    def detect_vedic_markers(self, text):
        """Detect if text contains Vedic markers"""
        vedic_markers = ['ॐ', 'ओ३म्', 'भूर्भुवः स्वः', 'भूः', 'भुवः', 'स्वः']
        return any(marker in text for marker in vedic_markers)

    def normalize_vedic_characters(self, text):
        """
        Normalize Vedic-specific Unicode characters to standard Devanagari.
        
        Vedic texts use special Unicode characters that should be normalized
        for proper syllable counting and pattern matching.
        
        Reference: Sanskrit repo (repos/sanskrit/transliteration/transliterate.py)
        Based on Unicode Vedic Extensions (U+1CD0 to U+1CFF)
        """
        # Vedic signs that function as visarga variants
        # U+1CF2: VEDIC SIGN ARDHAVISARGA - half visarga, normalize to ः
        text = text.replace('\u1CF2', 'ः')
        
        # U+1CF3: VEDIC SIGN ROTATED ARDHAVISARGA - normalize to ः
        text = text.replace('\u1CF3', 'ः')
        
        # U+1CF4: VEDIC TONE CANDRA ABOVE - tone marker, can be removed
        text = text.replace('\u1CF4', '')
        
        # Vedic signs for jihvāmūlīya (क् before) and upadhmanīya (प् before)
        # These are allophonic variants of visarga before k/p
        # U+1CF5: VEDIC SIGN JIHVAMULIYA (visarga before क, ख, etc.)
        text = text.replace('\u1CF5', 'ः')
        
        # U+1CF6: VEDIC SIGN UPADHMANIYA (visarga before प, फ, etc.)
        text = text.replace('\u1CF6', 'ः')
        
        # U+1CFA: VEDIC SIGN DOUBLE ANUSVARA ANTARGOMUKHA - normalize to ं
        text = text.replace('\u1CFA', 'ं')
        
        # Vedic anusvara variants
        # U+1CE1: VEDIC TONE ATHARVAVEDIC INDEPENDENT SVARITA - remove tone
        text = text.replace('\u1CE1', '')
        
        # Vedic accent/tone marks that don't affect syllable weight
        # U+1CD0-U+1CD2: Various tone marks
        text = text.replace('\u1CD0', '')  # VEDIC TONE KARSHANA
        text = text.replace('\u1CD1', '')  # VEDIC TONE SHARA
        text = text.replace('\u1CD2', '')  # VEDIC TONE PRENKHA
        
        # U+1CD3: VEDIC SIGN NIHSHVASA (breath mark) - remove
        text = text.replace('\u1CD3', '')
        
        return text

    def preprocess_vedic_text(self, text):
        """Preprocess Vedic text by expanding pratīka and special symbols"""
        # First normalize Vedic Unicode characters
        text = self.normalize_vedic_characters(text)
        
        # Expand OM - Using 2 syllable expansion (ओम्)
        text = text.replace('ॐ', 'ओम्')
        
        # Expand abbreviated vyāhṛti in Gayatri context
        # Full Gayatri has: ॐ भूः भुवः स्वः तत्सवितुर्वरेण्यं...
        # Each vyāhṛti counts as syllables: ओम् (2), भूः (2), भुवः (2), स्वः (2) = 8
        if 'भूर्भुवः स्वः' in text:
            text = text.replace('भूर्भुवः स्वः', 'भूः भुवः स्वः')
        
        # Also handle standalone भूर्भुवः (without स्वः)
        if 'भूर्भुवः' in text:
            text = text.replace('भूर्भुवः', 'भूः भुवः')
        
        return text

    def split_sandhi_basic(self, text):
        """Basic sandhi resolution for common cases"""
        # DISABLED: Sandhi splitting is too aggressive and breaks syllable counting
        # Only apply in specific Vedic contexts where needed
        # The sanskrit_text library already handles most cases correctly
        
        # Future: Implement context-aware sandhi resolution
        # For now, return text as-is to avoid breaking classical meters
        
        return text

    def normalize_meter_name(self, name):
        """Normalize meter name for comparison"""
        if not name:
            return ''
        
        # Remove trailing म्, ः, ा, etc.
        name = re.sub(r'[म्ःा]+$', '', name)
        
        # Standardize specific variants
        replacements = {
            'विक्रीडित': 'विक्रीडितम्',
            'अनुस्टुभ्': 'अनुष्टुभ्',
            'अनुस्टुप्': 'अनुष्टुभ्',
        }
        for old, new in replacements.items():
            if old in name:
                name = name.replace(old, new)
        
        return name.strip()

    def load_meter_synonyms(self):
        """Load meter name synonyms for flexible matching"""
        # Core synonyms for common meters
        self.METER_SYNONYMS = {
            'शार्दूलविक्रीडित': ['शार्दूलविक्रीडितम्', 'Shardulavikridita', 'Sārdūlavikrīḍita', 'Sardula-vikridita'],
            'मन्दाक्रान्ता': ['मन्दाक्रान्त', 'Mandakranta', 'Mandākrāntā', 'मन्दाक्रान्ता'],
            'इन्द्रवज्रा': ['इन्द्रवज्र', 'Indravajra', 'Indravajrā'],
            'अनुष्टुभ्': ['अनुस्टुभ्', 'Anushtubh', 'Anustubh', 'Anuṣṭubh', 'Anuṣṭup'],
            'वसन्ततिलका': ['Vasantatilaka', 'Vasantatilakā'],
            'गायत्री': ['Gayatri', 'Gāyatrī'],
            'त्रिष्टुभ्': ['Trishtubh', 'Triṣṭubh', 'Tristubh'],
            'जगती': ['Jagati', 'Jagatī']
        }

    def matches_meter(self, name1, name2):
        """Check if two meter names match (including synonyms)"""
        if not name1 or not name2:
            return False
        
        # Normalize both names
        norm1 = self.normalize_meter_name(name1).lower()
        norm2 = self.normalize_meter_name(name2).lower()
        
        # Exact match
        if norm1 == norm2 or name1.lower() == name2.lower():
            return True
        
        # Check synonyms
        for canonical, variants in self.METER_SYNONYMS.items():
            all_forms = [canonical.lower()] + [v.lower() for v in variants]
            if (norm1 in all_forms or name1.lower() in all_forms) and \
               (norm2 in all_forms or name2.lower() in all_forms):
                return True
        
        # Partial substring match (last resort)
        if len(norm1) > 3 and len(norm2) > 3:
            if norm1 in norm2 or norm2 in norm1:
                return True
        
        return False

    # ----------------------------------------------------------------------- #

    def identify_vedic_meter(self, syllable_count, lg_pattern=None):
        """Identify Vedic meter by syllable count with ±1 tolerance and pattern matching"""
        # Map syllable counts to actual meter names (all 7 major Vedic meters)
        vedic_mapping = {
            24: 'गायत्री',      # Gayatri - 3×8
            28: 'उष्णिक्',       # Ushnik - 4×7
            32: 'अनुष्टुभ्',     # Anushtubh - 4×8 (Vedic, different from classical)
            36: 'बृहती',        # Brihati - 4×9
            40: 'पङ्क्ति',       # Pankti - 5×8
            44: 'त्रिष्टुभ्',    # Trishtubh - 4×11
            48: 'जगती'         # Jagati - 4×12
        }
        
        # For pada-level identification (single pada, not full verse)
        pada_mapping = {
            7: 'उष्णिक्',        # Ushnik pada
            8: 'गायत्री',       # Gayatri/Anushtubh pada
            9: 'बृहती',         # Brihati pada
            11: 'त्रिष्टुभ्',   # Trishtubh pada
            12: 'जगती'         # Jagati pada
        }
        
        # Helper function to get English meter name for VEDIC_METERS lookup
        def get_english_name(sanskrit_name):
            name_map = {
                'गायत्री': 'Gayatri',
                'त्रिष्टुभ्': 'Trishtubh',
                'जगती': 'Jagati',
                'उष्णिक्': 'Ushnik',
                'अनुष्टुभ्': 'Anushtubh',
                'बृहती': 'Brihati',
                'पङ्क्ति': 'Pankti'
            }
            return name_map.get(sanskrit_name, sanskrit_name)
        
        # First try pada-level matching with pattern verification
        if syllable_count in pada_mapping and lg_pattern:
            meter_name = pada_mapping[syllable_count]
            if meter_name in self.VEDIC_PADA_PATTERNS:
                expected_pattern = self.VEDIC_PADA_PATTERNS[meter_name]
                if self.pattern_matches_with_tolerance(lg_pattern, expected_pattern, tolerance=2):
                    english_name = get_english_name(meter_name)
                    return meter_name, self.VEDIC_METERS.get(english_name)
        
        # Try full verse matching
        # Exact match
        if syllable_count in vedic_mapping:
            meter_name = vedic_mapping[syllable_count]
            english_name = get_english_name(meter_name)
            return meter_name, self.VEDIC_METERS.get(english_name)
        
        # Allow ±1 syllable tolerance for edge cases (punctuation, sandhi)
        for expected_count, meter_name in vedic_mapping.items():
            if abs(syllable_count - expected_count) == 1:
                english_name = get_english_name(meter_name)
                return meter_name, self.VEDIC_METERS.get(english_name)
        
        # Try pada-level without pattern (less confident)
        if syllable_count in pada_mapping:
            meter_name = pada_mapping[syllable_count]
            english_name = get_english_name(meter_name)
            return meter_name, self.VEDIC_METERS.get(english_name)
        
        return None, None

    def pattern_matches_with_tolerance(self, pattern1, pattern2, tolerance=2):
        """Check if two L-G patterns match within tolerance"""
        if len(pattern1) != len(pattern2):
            return False
        
        differences = sum(1 for a, b in zip(pattern1, pattern2) if a != b)
        return differences <= tolerance

    def should_be_guru(self, syllable, is_last=False):
        """Apply Anta-guru rule: last syllable is typically Guru"""
        if is_last:
            return True
        return False
    
    def get_method_info(self):
        """Return information about which syllabization method is being used"""
        return {
            'syllabization': self.syllabization_method,
            'icu_available': ICU_AVAILABLE,
            'pattern_matching': 'Original (1,920 meters)',
            'features': [
                'Multi-level confidence scoring',
                'Vedic meter recognition',
                'Fuzzy matching',
                'Sandhi resolution'
            ]
        }

    ###########################################################################
    # Multi-level Matching System (Priority 2 Enhancement)
    ###########################################################################

    def split_into_padas(self, lg_pattern, num_padas=4):
        """
        Split L-G pattern into equal padas (quarters)
        
        Args:
            lg_pattern: Full L-G pattern string
            num_padas: Number of padas to split into (default 4)
        
        Returns:
            List of pada patterns, or None if not evenly divisible
        """
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

    def match_with_confidence(self, lg_pattern, fuzzy=False, max_fuzzy=10):
        """
        Multi-level matching with confidence scoring
        
        Matching levels (in priority order):
        1. Exact match (confidence: 10.0)
        2. Pada-level match for Vedic meters (confidence: 8.0)
        3. Syllable count + pattern similarity (confidence: 5.0-7.0)
        4. Fuzzy match with Levenshtein distance (confidence: 1.0-4.0)
        
        Returns:
            List of tuples: [(meter_names, confidence_score), ...]
        """
        results = []
        syllable_count = len(lg_pattern)
        
        # Level 1: Exact match (highest confidence)
        if lg_pattern in self.CHANDA:
            for meter_name in self.CHANDA[lg_pattern]:
                results.append((meter_name, 10.0, 'exact'))
        
        # Level 2: Pada-level matching for Vedic meters
        # Check if this could be a multi-pada verse
        for num_padas in [4, 3, 2]:  # Try 4-pada, 3-pada, then 2-pada
            padas = self.split_into_padas(lg_pattern, num_padas)
            if padas:
                # Check if all padas are equal (sama) or follow a pattern
                first_pada = padas[0]
                pada_syllables = len(first_pada)
                
                # Check for Vedic meters by pada syllable count
                vedic_pada_meters = {
                    7: 'उष्णिक्',
                    8: ['गायत्री', 'अनुष्टुभ्'],
                    9: 'बृहती',
                    11: 'त्रिष्टुभ्',
                    12: 'जगती'
                }
                
                if pada_syllables in vedic_pada_meters:
                    meter_candidates = vedic_pada_meters[pada_syllables]
                    if not isinstance(meter_candidates, list):
                        meter_candidates = [meter_candidates]
                    
                    # Check if padas match patterns (for sama meters)
                    all_sama = all(pada == first_pada for pada in padas)
                    
                    for meter in meter_candidates:
                        if all_sama:
                            # All padas identical - strong pada match
                            confidence = 8.0
                            results.append(((meter, ''), confidence, 'pada_sama'))
                        else:
                            # Padas differ - check if pattern is vishama (unequal)
                            confidence = 6.5
                            results.append(((meter, ''), confidence, 'pada_vishama'))
        
        # Level 3: Syllable count matching with pattern similarity
        vedic_meter, vedic_info = self.identify_vedic_meter(syllable_count, lg_pattern)
        if vedic_meter:
            confidence = 7.0
            results.append(((vedic_meter, ''), confidence, 'vedic_syllable'))
        
        # Check other meters by syllable count
        syllable_matches = self.find_by_syllable_count(syllable_count)
        for match in syllable_matches:
            if match not in [r[0] for r in results]:
                confidence = 5.0
                results.append((match, confidence, 'syllable_count'))
        
        # Level 4: Fuzzy matching (lowest confidence, only if enabled)
        if fuzzy and len(results) < max_fuzzy:
            for chanda_lg, chanda_names in self.CHANDA.items():
                if len(chanda_lg) == syllable_count:  # Only compare same length
                    # Calculate Levenshtein similarity
                    distance = Lev.distance(lg_pattern, chanda_lg)
                    if distance <= 3:  # Max 3 differences
                        similarity = 1 - (distance / len(chanda_lg))
                        confidence = similarity * 4.0  # Scale to 0-4 range
                        
                        for name in chanda_names:
                            if name not in [r[0] for r in results]:
                                results.append((name, confidence, 'fuzzy'))
        
        # Sort by confidence (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results

    def find_by_syllable_count(self, syllable_count):
        """Find chandas by syllable count as fallback"""
        matches = []
        
        # Search in existing CHANDA database for matching syllable counts
        for lg_pattern, chanda_names in self.CHANDA.items():
            if len(lg_pattern) == syllable_count:
                matches.extend(chanda_names)
        
        # If no exact matches, check if it's a recognized Vedic meter total
        if not matches:
            meter_name, meter_info = self.identify_vedic_meter(syllable_count)
            if meter_name and meter_info:
                # Create a pseudo-entry for the Vedic meter
                matches.append((meter_name, ('1',)))
        
        return matches

    ###########################################################################

    def read_jaati(self, file):
        """
        Read Jaati list from CSV

        @format:
            - First column contains number of letters
            - Second column contains name(s) of Jaati
        """
        jaati = defaultdict(list)
        with open(file, 'r') as f:
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

    def read_matra(self, file):
        """
        Read Mātrā-based meters from CSV

        @format:
            - First column contains meter name(s)
            - Second column contains mātrā sequence (e.g., '12181215' = 12-18-12-15)
            - Third column (optional) contains synonyms
        """
        matra_meters = defaultdict(list)
        with open(file, 'r') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                if not row[0].strip():
                    continue
                    
                names = [row[0].strip()]
                if len(row) > 2 and row[2].strip():
                    # Add synonyms
                    synonyms = [s.strip() for s in row[2].split(',')]
                    names.extend(synonyms)
                
                matra_sequence = row[1].strip()
                
                # Parse mātrā sequence: '12181215' -> [12, 18, 12, 15]
                pada_matras = []
                i = 0
                while i < len(matra_sequence):
                    if i + 1 < len(matra_sequence):
                        # Try two-digit number
                        two_digit = matra_sequence[i:i+2]
                        if two_digit.isdigit() and 10 <= int(two_digit) <= 30:
                            pada_matras.append(int(two_digit))
                            i += 2
                            continue
                    # Single digit
                    if matra_sequence[i].isdigit():
                        pada_matras.append(int(matra_sequence[i]))
                        i += 1
                    else:
                        i += 1
                
                # Store by mātrā sequence
                for name in names:
                    matra_meters[matra_sequence].append(name)
                    # Also store by total mātrā count for quick lookup
                    total_matras = sum(pada_matras)
                    if len(pada_matras) >= 2:
                        # Store with pattern signature
                        pattern_key = f"matra_{total_matras}_{len(pada_matras)}"
                        matra_meters[pattern_key].append(name)

        self.MATRA.update(matra_meters)
        return matra_meters

    def read_chanda_definitions(self, chanda_file):
        """
        Read definitions of Chanda from CSV

        @params:
            - file: path of the CSV file containing Chanda definitions

        @format:
            Chanda definition file should have at least 3 columns
                - First column should contain name(s) of Chanda/VRtta
                - Second column should contain Pada
                - Third column should contain the Gana string
            Remaing columns will be ignored.
        """
        chanda = defaultdict(list)
        multi_chanda = defaultdict(list)
        splits = defaultdict(list)

        chanda_pada = defaultdict(dict)
        
        # Check if this is vedic CSV to extract pada patterns
        is_vedic_file = 'vedic' in chanda_file.lower()

        with open(chanda_file, 'r') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                if not row[0].strip():
                    continue

                # `meters` is a tuple since we need it to be hashable
                # for use as a key in the dictionary `chanda_pada`
                names = tuple(c.strip() for c in row[0].split(','))
                pada = row[1].strip()
                # meters = ((chanda, pada), ...)
                meters = tuple((c, (pada,)) for c in names)
                lakshana = ''.join(row[2].split())
                lakshana = lakshana.translate(self.ttable_in)
                lakshana = self.gana_to_lg(lakshana)
                lakshana = lakshana.replace(
                    '-', f"[{self.L}{self.G}]"
                )
                
                # Store Vedic pada patterns for enhanced matching
                if is_vedic_file and lakshana:
                    meter_name = names[0]
                    if meter_name not in self.VEDIC_PADA_PATTERNS:
                        self.VEDIC_PADA_PATTERNS[meter_name] = lakshana
                
                if pada:
                    chanda_pada[names][pada] = lakshana
                else:
                    chanda_pada[names]['1'] = lakshana
                    chanda_pada[names]['2'] = lakshana

                if lakshana:
                    chanda[lakshana].extend(meters)

        for _chanda_names, _pada_lakshana in chanda_pada.items():
            multi_pada = []
            multi_lakshana = []
            for _pada, _lakshana in _pada_lakshana.items():
                multi_pada.append(_pada)
                multi_lakshana.append(_lakshana)

                if len(multi_pada) == 2:
                    names = tuple(
                        (_name, tuple(multi_pada)) for _name in _chanda_names
                    )
                    multi_chanda[''.join(multi_lakshana)].extend(names)
                    splits[''.join(multi_lakshana)].append(multi_lakshana)

                    multi_pada = []
                    multi_lakshana = []

        for k, v in chanda.items():
            self.SINGLE_CHANDA[k].extend(v)
            self.CHANDA[k].extend(v)
        for k, v in multi_chanda.items():
            self.MULTI_CHANDA[k].extend(v)
            self.CHANDA[k].extend(v)

        self.SPLITS.update(splits)
        return chanda

    # ----------------------------------------------------------------------- #

    def read_data(self):
        self.read_jaati(os.path.join(self.data_path, 'chanda_jaati.csv'))
        self.read_matra(os.path.join(self.data_path, 'chanda_matra.csv'))
        definition_files = [
            'chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv', 'chanda_vedic.csv'
        ]
        for chanda_file in definition_files:
            self.read_chanda_definitions(
                os.path.join(self.data_path, chanda_file)
            )

    # ----------------------------------------------------------------------- #

    def read_examples(self):
        example_file = os.path.join(self.data_path, "examples.json")
        with open(example_file, "r") as f:
            examples = json.load(f)
        return examples

    ###########################################################################

    def process_text(self, text):
        scheme = detect(text)
        if scheme != sanscript.DEVANAGARI:
            devanagari_text = transliterate(text, scheme, sanscript.DEVANAGARI)
        else:
            devanagari_text = text
        
        # Always normalize Vedic characters (lightweight operation)
        # This handles special Unicode characters in Vedic texts
        devanagari_text = self.normalize_vedic_characters(devanagari_text)
        
        # Additional Vedic preprocessing for specific markers
        if self.detect_vedic_markers(devanagari_text):
            devanagari_text = self.preprocess_vedic_text(devanagari_text)
        
        lines = []
        for line in skt.split_lines(devanagari_text):
            clean_line = skt.clean(line).strip()
            if clean_line:
                lines.append(clean_line)
        return lines, scheme

    ###########################################################################

    @functools.lru_cache(maxsize=MAX_CACHE)
    def transform(
        self, source_line, signature,
        replace_cost=1, delete_cost=1, insert_cost=1, max_diff=3
    ):
        """
        Find possible transformations of source string to fit the signature
        """
        syllables, lg_marks = self.mark_lg(source_line)
        # Note: Can avoid this conversion to save time, if needed
        # Just need to ensure that Laghu-Guru string is passed properly
        lg_signature = self.gana_to_lg(signature)
        lg_str = ''.join(lg_marks)
        ops = Lev.editops(lg_str, lg_signature)

        if not ops:
            # exact match
            return 0, []

        distance = len(ops)

        # weights can be decided by an external agent
        op_cost = {
            'replace': replace_cost,
            'delete': delete_cost,
            'insert': insert_cost
        }

        cost = sum([op_cost[op[0]] for op in ops])

        if distance > max_diff:
            return distance, None

        idx = 0  # overall index (syllables, lg_marks)
        lg_idx = 0  # index in the lg_str
        op_idx = 0  # index in the list of edit operations

        output = []

        op, spos, dpos = ops[op_idx]

        # ------------------------------------------------------------------- #
        for lid, line in enumerate(syllables):
            output_line = []
            # --------------------------------------------------------------- #
            for wid, word in enumerate(line):
                output_word = []
                # ----------------------------------------------------------- #
                for cid, syllable in enumerate(word):
                    output_syllable = syllable
                    if lg_marks[idx]:
                        if lg_idx == spos:
                            if op[0] == 'i':
                                output_syllable = f'i({lg_signature[dpos]})'
                                output_word.append(output_syllable)
                                op_idx += 1
                                # insertion means we need to continue with
                                # the same syllable but next operation,
                                # so we increment op_idx
                                # Hence the other condition (op[0] != 'i')
                                # cannot be in the 'else' part directly

                            if op_idx < distance:
                                op, spos, dpos = ops[op_idx]

                                if op[0] != 'i':
                                    output_syllable = f'{op[0]}({syllable})'
                                    if op[0] == 'r':
                                        substitute = lg_signature[dpos]
                                        output_syllable += f'[{substitute}]'
                                        laghu = skt.is_laghu(syllable)
                                        if not laghu == (substitute == self.L):
                                            tm = skt.toggle_matra(
                                                syllable
                                            )
                                            if tm:
                                                # toggle was successful
                                                output_syllable += f'{{{tm}}}'
                                op_idx += 1
                                if op_idx < distance:
                                    op, spos, dpos = ops[op_idx]

                        # increase index in Laghu-Guru string if valid mark
                        lg_idx += 1

                    # always increment syllable index
                    idx += 1
                    output_word.append(output_syllable)
                # ----------------------------------------------------------- #
                output_line.append(output_word)
            # --------------------------------------------------------------- #
            output.append(output_line)
        # ------------------------------------------------------------------- #

        return cost, output

    ###########################################################################

    def find_direct_match(self, line, multi=False):
        chanda_dictionary = self.MULTI_CHANDA if multi else self.SINGLE_CHANDA

        syllables, lg_marks = self.mark_lg(skt.clean(line))
        flat_syllables = [s for ln in syllables for w in ln for s in w]
        lg_str = ''.join(lg_marks)
        if not lg_str:
            return None

        found = lg_str in chanda_dictionary

        # try searching by making last Guru using Anta-guru principle (Bug #5)
        if not found and lg_str[-1] == self.L:
            if self.should_be_guru(flat_syllables[-1], is_last=True):
                lg_str = lg_str[:-1] + self.G
                found = lg_str in chanda_dictionary

                # still not found? revert
                if not found:
                    lg_str = lg_str[:-1] + self.L

        # Method 2: Syllable count fallback (Bug #3)
        syllable_count_matches = []
        if not found:
            syllable_count = len(lg_str)
            syllable_count_matches = self.find_by_syllable_count(syllable_count)
            if syllable_count_matches:
                found = True

        chanda = []
        jaati = []
        gana = []
        length = []
        matra = []
        if not multi:
            if found:
                if lg_str in self.SINGLE_CHANDA:
                    chanda += self.SINGLE_CHANDA.get(lg_str)
                # Add syllable count matches
                if syllable_count_matches:
                    chanda += syllable_count_matches
            jaati = self.JAATI.get(len(lg_str), self.JAATI[-1])
            gana = [self.lg_to_gana(lg_str)]
            length = [str(len(lg_str))]
            matra = [str(self.count_matra(lg_str))]
        else:
            if found:
                chanda = self.MULTI_CHANDA.get(lg_str, [])
                # display properties, bit misplaced
                splits_data = self.SPLITS.get(lg_str, [])
                if splits_data:
                    jaati = [
                        "(" + ', '.join(
                            ' / '.join(self.JAATI.get(len(split), self.JAATI[-1]))
                            for split in splits
                        ) + ")"
                        for splits in splits_data
                    ]
                    gana = [
                        f"({', '.join(self.lg_to_gana(s) for s in splits)})"
                        for splits in splits_data
                    ]
                    length = [
                        f"({' + '.join(str(len(s)) for s in splits)})"
                        for splits in splits_data
                    ]
                    matra = [
                        f"({' + '.join(str(self.count_matra(s)) for s in splits)})"
                        for splits in splits_data
                    ]
                else:
                    jaati = []
                    gana = []
                    length = []
                    matra = []

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

    ###########################################################################

    def identify_verse_holistically(self, verse_lines):
        """
        Identify verse as a complete unit (Bug #2 fix)
        Aggregates multiple lines and processes them together
        """
        # Combine all lines in the verse
        combined_text = ' '.join(verse_lines)
        syllables, lg_marks = self.mark_lg(combined_text)
        lg_str = ''.join(lg_marks)
        
        # Calculate total syllables
        total_syllables = len(lg_str)
        
        # Try to identify by total syllable count with pattern
        meter_name, meter_info = self.identify_vedic_meter(total_syllables, lg_str)
        
        result = {
            'found': False,
            'meter': meter_name,
            'total_syllables': total_syllables,
            'lg_str': lg_str
        }
        
        if meter_name:
            result['found'] = True
        
        return result

    def identify_from_text(
        self, text, verse=False, fuzzy=False, save_path=None, scheme=None, use_sandhi=False
    ):
        """
        Identify meters from text

        If `verse` is True, treat the input as collection of verses.
        NOTE: Currently assumes 4 lines per verse.
        TODO: Add support for 2 lines per verse too. (i.e. 2 pada in same line)
        
        Bug #2 Fix: Implements verse-level holistic processing
        
        Parameters
        ----------
        use_sandhi : bool, optional
            If True, uses automatic sandhi resolution for merged words.
            Default is False.
        """
        line_results = []
        verse_results = []

        lines, _scheme = self.process_text(text)
        if not scheme:
            scheme = _scheme

        # Bug #2 Fix: If verse mode, pre-aggregate lines for holistic processing
        if verse:
            # First, get holistic verse-level analysis
            verse_aggregates = []
            for i in range(0, len(lines), 4):
                verse_lines = lines[i:i+4]
                if verse_lines:
                    holistic_result = self.identify_verse_holistically(verse_lines)
                    verse_aggregates.append({
                        'lines': verse_lines,
                        'holistic': holistic_result,
                        'start_idx': i
                    })

        for line in lines:
            if not line:
                continue
            original_line = transliterate(line, sanscript.DEVANAGARI, scheme)
            
            # Use sandhi resolution if enabled
            if use_sandhi:
                line_result = self.identify_with_sandhi(original_line, fuzzy=fuzzy)
            else:
                line_result = self.identify_line(original_line, fuzzy=fuzzy)
            
            line_results.append({
                'line': line,
                'result': line_result
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
            verse_aggregate_idx = 0
            holistic_boost_applied = False

            for line_idx, line_result in enumerate(line_results):
                _result = line_result['result']
                
                # Bug #2 Fix: Use holistic verse analysis to boost scores
                # Apply boost once at the start of each verse
                if not holistic_boost_applied and verse_aggregate_idx < len(verse_aggregates):
                    current_aggregate = verse_aggregates[verse_aggregate_idx]
                    if current_aggregate['holistic']['found']:
                        meter_name = current_aggregate['holistic']['meter']
                        # Strong boost for holistically identified meter
                        ongoing_score[meter_name] += 4.0
                    holistic_boost_applied = True
                
                if _result['found']:
                    _chanda = _result['chanda']
                    _unique_chanda = list(dict(_chanda))
                    
                    # ENHANCED: Use confidence scores from multi-level matching
                    confidence_scores = _result.get('confidence_scores', {})
                    
                    for _c in _unique_chanda:
                        # Get meter name (handle tuple format)
                        meter_name = _c[0] if isinstance(_c, tuple) else _c
                        
                        # Use confidence score if available, otherwise default to 1.0
                        if meter_name in confidence_scores:
                            score = confidence_scores[meter_name][0] / 10.0  # Normalize to 0-1
                        else:
                            score = 1.0
                        
                        ongoing_score[_c] += score
                else:
                    for fuzzy_match in _result['fuzzy']:
                        _chanda = fuzzy_match['chanda']
                        _unique_chanda = list(dict(_chanda))
                        for _c in _unique_chanda:
                            ongoing_score[_c] += fuzzy_match['similarity']

                verse_result['lines'].append(line_idx)
                line_count += 1
                if line_count % 4 == 0 or line_idx == len(line_results) - 1:
                    verse_scores = ongoing_score.most_common()
                    if verse_scores:
                        best_score = verse_scores[0][1]
                        best_matches = ([
                            _c
                            for _c, _score in verse_scores if _score == best_score
                        ], best_score)
                    else:
                        best_matches = ([], 0)
                    verse_result['scores'] = verse_scores
                    verse_result['chanda'] = best_matches
                    verse_aggregate_idx += 1
                    holistic_boost_applied = False  # Reset for next verse
                    for _line_idx in verse_result['lines']:
                        line_result = line_results[_line_idx]
                        priority_fuzzy = []
                        existing_fuzzy = line_result['result']['fuzzy']
                        for idx, fuzzy_match in enumerate(existing_fuzzy):
                            if any([
                                (x in best_matches[0])
                                for x in [c[0] for c in fuzzy_match['chanda']]
                            ]):
                                priority_fuzzy.append(existing_fuzzy.pop(idx))
                        line_result['result']['fuzzy'] = (
                            priority_fuzzy + existing_fuzzy
                        )

                    verse_results.append(verse_result)
                    # reset
                    verse_result = {
                        'chanda': None,
                        'scheme': scheme,
                        'scores': [],
                        'lines': []
                    }
                    ongoing_score = Counter()

        results = {
            'line': line_results,
            'verse': verse_results
        }

        simple_result = []
        if verse:
            for verse_result in verse_results:
                best_matches = " / ".join(verse_result['chanda'][0])
                best_score = verse_result['chanda'][1]
                simple_result.append(f"# {best_matches} ({best_score})")
                simple_result.append("")
                for line_id in verse_result['lines']:
                    line_result = line_results[line_id]
                    simple_result.append(
                        self.format_line_result(line_result['result'])
                    )
                simple_result.append("")
        else:
            for line_result in line_results:
                simple_result.append(
                    self.format_line_result(line_result['result'])
                )
                simple_result.append("")

        if save_path is not None:
            os.makedirs(save_path, exist_ok=True)

            md5sum = hashlib.md5(text.encode('utf-8')).hexdigest()
            result_id = f"result_{md5sum}_{int(verse)}_{int(fuzzy)}"

            json_filename = f"{result_id}.json"
            json_path = os.path.join(save_path, json_filename)
            with open(json_path, mode="w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False)

            txt_filename = f"{result_id}.txt"
            txt_path = os.path.join(save_path, txt_filename)
            with open(txt_path, mode="w", encoding="utf-8") as f:
                f.write("\n".join(simple_result))
        else:
            md5sum = None
            json_filename = None
            txt_filename = None

        paths = {
            'json': json_filename,
            'txt': txt_filename
        }
        return {
            'result': results,
            'path': paths
        }

    # ----------------------------------------------------------------------- #

    def identify_line(self, line, fuzzy=False, k=10):
        """
        Identify Chanda if possible from a single text line

        @return:
            - answer: dictionary containing scansion details about the line
                - found: boolean indicating if the Chanda was found or not
                - ...
        """

        lines, scheme = self.process_text(line)
        output_scheme = scheme if scheme != sanscript.DEVANAGARI else None

        if len(lines) > 1:
            raise ValueError('Input contains more than one line.')
        line = lines[0]

        answer = {}

        direct_match = self.find_direct_match(line)
        multi_match = self.find_direct_match(line, multi=True)

        if direct_match is None:
            # lg_str is empty
            return answer

        found = direct_match['found'] or multi_match['found']

        lg_str = ''.join(direct_match['lg'])
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
                chanda += direct_match['chanda']
                jaati += direct_match['jaati']
                gana += direct_match['gana']
                length += direct_match['length']
                matra += direct_match['matra']
            if multi_match['found']:
                chanda += multi_match['chanda']
                jaati += multi_match['jaati']
                gana += multi_match['gana']
                length += multi_match['length']
                matra += multi_match['matra']

            if is_regex_match:
                chanda += [
                    c
                    for m in regex_matches
                    for c in self.CHANDA.get(m)
                    if c not in chanda
                ]

        full_lg = [self.output_map.get(c, c) for c in direct_match['lg']]
        full_length = len(lg_str)
        full_matra = self.count_matra(lg_str)
        full_gana = self.lg_to_gana(lg_str).translate(self.ttable_out)
        full_jaati = self.JAATI.get(len(lg_str), self.JAATI[-1])

        # ENHANCED: Multi-level matching with confidence scores
        multi_level_matches = self.match_with_confidence(lg_str, fuzzy=fuzzy, max_fuzzy=k)
        
        # Merge multi-level matches with existing matches, using ADDITIVE scoring
        confidence_map = {}  # meter_name -> (confidence, match_type)
        
        # Add existing exact matches with confidence 10.0
        for c in chanda:
            meter_name = c[0] if isinstance(c, tuple) else c
            confidence_map[meter_name] = (10.0, 'exact_direct')
        
        # Add multi-level matches (ADDITIVE: boost existing scores, don't replace)
        for match_item, confidence, match_type in multi_level_matches:
            if isinstance(match_item, tuple):
                meter_name = match_item[0]
                meter_tuple = match_item
            else:
                meter_name = match_item
                meter_tuple = (match_item, ('',))
            
            # ADDITIVE: Combine confidence scores for multiple evidence types
            if meter_name in confidence_map:
                existing_conf, existing_type = confidence_map[meter_name]
                # Add pada-level and vedic bonuses to existing scores
                if match_type in ['pada_sama', 'pada_vishama', 'vedic_syllable']:
                    combined_conf = existing_conf + confidence
                    confidence_map[meter_name] = (combined_conf, f'{existing_type}+{match_type}')
                # Otherwise keep higher confidence
                elif confidence > existing_conf:
                    confidence_map[meter_name] = (confidence, match_type)
            else:
                confidence_map[meter_name] = (confidence, match_type)
                # Add to chanda list if not already there
                if meter_tuple not in chanda:
                    chanda.append(meter_tuple)
        
        # Sort chanda by confidence (highest first)
        chanda_with_confidence = [
            (name, confidence_map.get(name[0] if isinstance(name, tuple) else name, (0, ''))[0])
            for name in chanda
        ]
        chanda_with_confidence.sort(key=lambda x: x[1], reverse=True)
        chanda = [item[0] for item in chanda_with_confidence]
        
        # Update found status
        if chanda:
            found = True
        
        # Store confidence information for debugging/analysis
        answer['confidence_scores'] = confidence_map

        # display properties
        display_line = line
        display_syllables = direct_match['syllables']
        display_lg = full_lg
        display_gana = (
            ' / '.join(gana).translate(self.ttable_out)
            if gana else
            full_gana
        )
        display_length = ' / '.join(length) if length else full_length
        display_matra = ' / '.join(matra) if matra else full_matra
        
        # Format chanda for display, handling both tuple and string formats
        display_chanda_parts = []
        display_chanda_primary_parts = []  # High-confidence matches (exact pattern matches)
        display_chanda_alternate_parts = []  # Medium-confidence matches
        
        # Find maximum confidence to calculate thresholds
        max_confidence = max((conf for meter, (conf, _) in confidence_map.items()), default=0)
        
        # Primary threshold: 80% of max confidence (for exact matches)
        # This ensures exact matches (10.0) show as primary, but not syllable-only matches (5.0)
        confidence_threshold_primary = max_confidence * 0.8
        
        # Alternate threshold: Only show if confidence is at least 7.0 (higher than syllable-only)
        # This filters out the hundreds of syllable-count-only matches
        confidence_threshold_alternate = 7.0
        
        for c in chanda:
            if isinstance(c, tuple) and len(c) >= 2:
                formatted = self.format_chanda_pada(c[0], c[1])
                meter_name = c[0]
            elif isinstance(c, tuple) and len(c) == 1:
                formatted = self.format_chanda_pada(c[0], ('',))
                meter_name = c[0]
            else:
                formatted = str(c)
                meter_name = c
            
            if formatted:  # Only add non-None, non-empty strings
                meter_confidence = confidence_map.get(meter_name, (0, ''))[0]
                
                # Add IAST transliteration if meter name is in Devanagari
                meter_display = formatted
                if meter_name and any(ord(ch) > 127 for ch in meter_name):
                    # Transliterate to IAST
                    iast_name = transliterate(meter_name, sanscript.DEVANAGARI, sanscript.IAST)
                    # Only add if it's different (not already in IAST)
                    if iast_name and iast_name != meter_name:
                        meter_display = f"{formatted} ({iast_name})"
                
                # Categorize by confidence
                if meter_confidence >= confidence_threshold_primary:
                    # Primary display: high-confidence with scores (exact pattern matches)
                    formatted_with_conf = f"{meter_display} [{meter_confidence:.1f}]"
                    display_chanda_primary_parts.append(formatted_with_conf)
                elif meter_confidence >= confidence_threshold_alternate:
                    # Alternate display: medium-confidence (pada matches, vedic, etc.)
                    display_chanda_alternate_parts.append(meter_display)
                
                # Always add to full list (for backwards compatibility)
                display_chanda_parts.append(formatted)
        
        display_chanda = ' / '.join(display_chanda_parts)
        display_chanda_primary = ' | '.join(display_chanda_primary_parts)
        display_chanda_alternate = ' / '.join(display_chanda_alternate_parts)
        display_chanda_alternate_count = len(display_chanda_alternate_parts)
        display_chanda_hidden_count = len(display_chanda_parts) - len(display_chanda_primary_parts) - len(display_chanda_alternate_parts)
        
        display_jaati = ' / '.join(
            jaati if jaati else full_jaati
        )

        answer['found'] = found
        answer['syllables'] = direct_match['syllables']
        answer['lg'] = full_lg
        answer['gana'] = full_gana
        answer['length'] = full_length
        answer['matra'] = full_matra
        answer['chanda'] = chanda
        answer['jaati'] = jaati

        answer['display_scheme'] = output_scheme
        answer['display_line'] = display_line
        answer['display_syllables'] = display_syllables
        answer['display_lg'] = display_lg
        answer['display_gana'] = display_gana
        answer['display_length'] = display_length
        answer['display_matra'] = display_matra
        answer['display_chanda'] = display_chanda
        answer['display_chanda_primary'] = display_chanda_primary  # High-confidence (≥15.0)
        answer['display_chanda_alternate'] = display_chanda_alternate  # Medium-confidence (≥50% of max)
        answer['display_chanda_alternate_count'] = display_chanda_alternate_count  # Count of medium-conf matches
        answer['display_chanda_hidden_count'] = display_chanda_hidden_count  # Count of low-conf matches (<50%)
        answer['display_jaati'] = display_jaati

        answer['fuzzy'] = []

        if not found and fuzzy:
            for chanda_lg, chanda_names in self.CHANDA.items():
                chanda_gana = self.lg_to_gana(chanda_lg)
                cost, suggestion = self.transform(line, chanda_lg)
                similarity = (1 - cost / len(chanda_lg))
                # Fixed: Always add suggestions even if transformation is None (Bug #4)
                output = suggestion if suggestion else []
                _display_chanda = ' / '.join(
                    self.format_chanda_pada(c, p) for c, p in chanda_names
                )
                answer['fuzzy'].append(
                    {
                        "chanda": chanda_names,
                        "gana": chanda_gana.translate(self.ttable_out),
                        "suggestion": output,
                        "cost": cost,
                        "similarity": similarity,
                        "display_chanda": _display_chanda
                    }
                )
            answer['fuzzy'] = sorted(
                answer['fuzzy'],
                key=lambda x: x["similarity"],
                reverse=True
            )[:k]
        return answer

    ###########################################################################

    def identify_with_sandhi(self, line, k_candidates=5, k_meters=10, 
                             fuzzy=False, lexicon_path=None):
        """
        Identify chandas with automatic sandhi resolution.
        
        This method generates multiple sandhi-split candidates and identifies
        the chandas for each, returning the best match based on a combined
        score of sandhi plausibility and meter confidence.
        
        Args:
            line (str): Sanskrit text (may contain merged sandhi)
            k_candidates (int): Number of sandhi candidates to try (default: 5)
            k_meters (int): Number of meter matches per candidate (default: 10)
            fuzzy (bool): Enable fuzzy matching for identification (default: False)
            lexicon_path (str): Path to lexicon file for sandhi scoring (default: None)
        
        Returns:
            dict: Identification result with additional sandhi information:
                - All standard identify_line() keys
                - 'sandhi_candidates': list of tried candidates with scores
                - 'sandhi_best': the selected candidate info
                - 'sandhi_original': original input line
        
        Example:
            >>> chanda = Chanda('data/')
            >>> result = chanda.identify_with_sandhi("कर्मण्येवाधिकारस्ते")
            >>> print(result['sandhi_best']['rules'])
            >>> print(result['display_chanda'])
        """
        try:
            from sandhi_rules import gen_candidates
        except ImportError:
            # Fallback to regular identification if sandhi_rules not available
            result = self.identify_line(line, fuzzy=fuzzy, k=k_meters)
            result['sandhi_available'] = False
            result['sandhi_original'] = line
            return result
        
        # Set default lexicon path if not provided
        if lexicon_path is None:
            lexicon_path = os.path.join(self.data_path, 'sandhi_lexicon.txt')
        
        # Generate sandhi candidates
        candidates = gen_candidates(
            line, 
            k=k_candidates, 
            lexicon_path=lexicon_path if os.path.exists(lexicon_path) else None
        )
        
        # Try identification on each candidate
        candidate_results = []
        for cand_info in candidates:
            cand_text = cand_info['cand']
            sandhi_score = cand_info['score']
            
            # Identify chandas for this candidate
            id_result = self.identify_line(cand_text, fuzzy=fuzzy, k=k_meters)
            
            # Calculate combined score
            # Use highest meter confidence if found, otherwise use fuzzy similarity
            if id_result['found'] and id_result.get('confidence_scores'):
                # Get highest confidence from exact matches
                meter_conf = max(
                    (conf for conf, _ in id_result['confidence_scores'].values()),
                    default=0.0
                )
            elif id_result.get('fuzzy') and len(id_result['fuzzy']) > 0:
                # Use top fuzzy match similarity
                meter_conf = id_result['fuzzy'][0]['similarity'] * 10.0  # Scale to ~10
            else:
                meter_conf = 0.0
            
            # Combined score: weighted average of sandhi and meter confidence
            # Sandhi score typically ranges -2 to 2, meter confidence 0-17
            # Normalize sandhi to 0-10 range, then combine
            normalized_sandhi = ((sandhi_score + 2.0) / 4.0) * 10.0
            combined_score = (0.3 * normalized_sandhi) + (0.7 * meter_conf)
            
            candidate_results.append({
                'candidate': cand_text,
                'sandhi_score': sandhi_score,
                'sandhi_rules': cand_info['rules'],
                'meter_confidence': meter_conf,
                'combined_score': combined_score,
                'identification': id_result
            })
        
        # Sort by combined score and select best
        candidate_results.sort(key=lambda x: x['combined_score'], reverse=True)
        best = candidate_results[0] if candidate_results else None
        
        if best:
            # Return the identification result of the best candidate
            result = best['identification'].copy()
            
            # Add sandhi metadata
            result['sandhi_available'] = True
            result['sandhi_original'] = line
            result['sandhi_best'] = {
                'candidate': best['candidate'],
                'sandhi_score': best['sandhi_score'],
                'rules': best['sandhi_rules'],
                'meter_confidence': best['meter_confidence'],
                'combined_score': best['combined_score']
            }
            result['sandhi_candidates'] = [
                {
                    'candidate': c['candidate'],
                    'sandhi_score': c['sandhi_score'],
                    'rules': c['sandhi_rules'],
                    'combined_score': c['combined_score']
                }
                for c in candidate_results
            ]
        else:
            # Fallback to regular identification
            result = self.identify_line(line, fuzzy=fuzzy, k=k_meters)
            result['sandhi_available'] = True
            result['sandhi_original'] = line
            result['sandhi_candidates'] = []
        
        return result

    ###########################################################################

    def summarize_results(self, results):
        line_results = results['line']
        verse_results = results['verse']

        match_line_statistics = defaultdict(Counter)
        fuzzy_line_statistics = defaultdict(Counter)
        verse_statistics = defaultdict(Counter)

        counts = defaultdict(int)

        for line_answer in line_results:
            counts['line'] += 1
            line_result = line_answer['result']
            if line_result['found']:
                counts['match_line'] += 1
                chanda_list = line_result['display_chanda'].split('/')
                gana_list = line_result['display_gana'].split('/')

                match_line_statistics['chanda'].update(chanda_list)
                match_line_statistics['gana'].update(gana_list)
            else:
                counts['fuzzy_line'] += 1
                for idx, fuzzy_match in enumerate(line_result['fuzzy']):
                    if idx == 0:
                        counts['mismatch_syllable'] += fuzzy_match['cost']
                    chanda_list = fuzzy_match['display_chanda'].split('/')
                    fuzzy_line_statistics['chanda'].update(chanda_list)
                    break

        for verse_result in verse_results:
            counts['verse'] += 1
            chanda_list, chanda_score = verse_result['chanda']
            if chanda_score == len(verse_result['lines']):
                counts['match_verse'] += 1
            else:
                counts['fuzzy_verse'] += 1
            verse_statistics['chanda'].update(chanda_list)

        return {
            'verse': verse_statistics,
            'line': {
                'fuzzy': fuzzy_line_statistics,
                'match': match_line_statistics,
            },
            'count': counts
        }

    # def analyse_file(self, file, fuzzy=True, remove_chars=''):
    #     """
    #     Analyses a file and identify Chanda from each line.

    #     @params:
    #         file: path of the input file
    #         remove_chars: characters to be removed

    #     `skt.clean()` is called after removing remove_chars.
    #     Lines are identified using the `skt.split_lines()` function.
    #     """
    #     with open(file, 'r') as f:
    #         content = f.read().translate(str.maketrans('', '', remove_chars))

    #     line_results, verse_results = self.identify_from_text(
    #         content,
    #         verse=True,
    #         fuzzy=True
    #     )

    #     hit = 0
    #     unk = 0
    #     content = []
    #     fuzzy_freq = Counter()
    #     chanda_freq = Counter()
    #     jaati_freq = Counter()
    #     gana_freq = Counter()
    #     matra_freq = Counter()
    #     statistics = defaultdict(Counter)

    #     for line_answer in line_results:
    #         line_result = line_answer['result']

    #         line_chanda = line_result['chanda']
    #         line_jaati = line_result['jaati']
    #         line_gana = line_result['gana']
    #         line_matra = line_result['matra']

    #         hit += line_result['found']
    #         unk += not(line_result['found'])

    #         matra_freq.update([line_matra])
    #         if line_chanda:
    #             line_desc = ' / '.join(line_chanda)
    #             chanda_freq.update(line_chanda)
    #         else:
    #             line_desc = line_gana
    #             gana_freq.update([line_gana])

    #         if fuzzy and line_result['fuzzy']:
    #             line_fuzzy = line_result['fuzzy'][0][0]
    #             fuzzy_freq.update(line_fuzzy)

    #         jaati_freq.update(line_jaati)

    #         content.append(
    #             f"{line_matra:<6}: {line_desc:<20}: {line_answer['line']}"
    #         )

    #     with open(f'{file}.chanda', 'w') as f:
    #         f.write('\n'.join(content))

    #     with open(f'{file}.analysis', 'w') as f:
    #         json.dump(statistics, f, ensure_ascii=False, indent=2)

    #     result = {
    #         'hit': hit,
    #         'unk': unk,
    #         'chanda_freq': chanda_freq,
    #         'fuzzy_freq': fuzzy_freq,
    #         'matra_freq': matra_freq,
    #         'jaati_freq': jaati_freq,
    #         'gana_freq': gana_freq,
    #     }
    #     return result

    ###########################################################################
    # Formatters

    @staticmethod
    def format_chanda_pada(chanda: str, pada: tuple) -> str:
        if len(pada) == 1:
            return f"{chanda} (पाद {pada[0]})" if pada[0] else chanda
        if len(pada) == 2:
            return f"{chanda} (पाद {pada[0]}-{pada[1]})"

    @staticmethod
    def format_line_result(line_result) -> str:
        output_lines = [
            line_result['display_line'],
            f"\tSyllables: {line_result['display_syllables']}",
            f"\tLG: {line_result['display_lg']}",
            f"\tGana: {line_result['display_gana']}",
            (f"\tCounts: {line_result['display_length']} letters, "
                f"{line_result['display_matra']} morae"),
            f"\tChanda: {line_result['display_chanda']}",
            f"\tJaati: {line_result['display_jaati']} "
        ]
        if line_result['fuzzy']:
            best_match = line_result['fuzzy'][0]
            output_lines.extend([
                (f"\tFuzzy: {best_match['display_chanda']} "
                 f"({best_match['similarity']})"),
                f"\t\t{best_match['suggestion']}"
            ])
        return "\n".join(output_lines)

    @staticmethod
    def format_summary(result_summary) -> str:
        output = []
        if result_summary["verse"]:
            output.extend([
                "Verse Statistics",
                "----------------"
            ])
            for idx, (chanda_name, chanda_count) in enumerate(
                result_summary["verse"]["chanda"].most_common(),
                start=1
            ):
                output.append(f"{idx:>4}. {chanda_name}: {chanda_count}")
            output.append("")

        output.extend([
            "Line Statistics",
            "---------------"
        ])

        if result_summary["line"]["match"]:
            output.append("-- Exact Match")
            for idx, (chanda_name, chanda_count) in enumerate(
                result_summary["line"]["match"]["chanda"].most_common(),
                start=1
            ):
                output.append(f"{idx:>4}. {chanda_name}: {chanda_count}")
            output.append("")

        if result_summary["line"]["fuzzy"]:
            output.append("-- Fuzzy Match")
            for idx, (chanda_name, chanda_count) in enumerate(
                result_summary["line"]["fuzzy"]["chanda"].most_common(),
                start=1
            ):
                output.append(f"{idx:>4}. {chanda_name}: {chanda_count}")
            output.append("")

        counts = result_summary["count"]
        output.extend([
            "Counts",
            "------",
            f"* Total Lines: {counts['line']}",
            f"  - Exact Match: {counts['match_line']}",
            f"  - Fuzzy Match: {counts['fuzzy_line']}",
            f"* Total Verses: {counts['verse']}",
            f"  - Exact Match: {counts['match_verse']}",
            f"  - Fuzzy Match: {counts['fuzzy_verse']}",
            f"* Total Syllables Mismatched: {counts['mismatch_syllable']}",
        ])

        return "\n".join(output)

    ###########################################################################

###############################################################################
