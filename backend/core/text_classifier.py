#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vedic vs Classical Sanskrit Text Classifier

This module provides robust classification of Sanskrit texts to determine
whether they are Vedic (Rigveda, Yajurveda, etc.) or Classical (Kavya, 
Shloka poetry like Meghadutam, Bhagavad Gita shlokas, etc.)

Key distinguishing features:
1. Syllable structure - Vedic: typically 22-48 syllables in specific counts
                       Classical: variable, often longer verses
2. Vocabulary markers - Vedic has archaic forms, Classical has evolved forms
3. Structural patterns - Vedic: often 3-4 padas, Classical: 2-4 padas with danda
4. Character usage - Vedic uses certain archaic Unicode chars (U+1CF0-U+1CFF)
5. Deity invocations - Vedic style vs Classical style
6. Compound patterns - Vedic simpler, Classical elaborate samasa

Author: Meru Coders Team (SIH 2025)
"""

import re
from typing import Dict, List, Tuple


class TextClassifier:
    """
    Classifies Sanskrit text as Vedic or Classical based on linguistic features.
    
    Usage:
        classifier = TextClassifier()
        text_type, confidence, features = classifier.classify("अग्निमीळे पुरोहितं...")
        # Returns: ('vedic', 0.85, {'syllable_count': 24, 'vedic_vocab_hits': 3, ...})
    """

    # =========================================================================
    # VEDIC MARKERS
    # =========================================================================

    # Vedic-specific vocabulary (archaic forms, Vedic deities, ritual terms)
    VEDIC_VOCABULARY = {
        # Deities (Vedic style invocation)
        'अग्नि', 'इन्द्र', 'वरुण', 'मित्र', 'सोम', 'अश्विन', 'मरुत', 'रुद्र',
        'विष्णु', 'सविता', 'पूषन', 'भग', 'अर्यमन', 'दक्ष', 'अंश', 'त्वष्टृ',
        'विवस्वत', 'आदित्य', 'वायु', 'पर्जन्य', 'द्यौस', 'पृथिवी', 'उषस',
        'अहि', 'वृत्र', 'असुर', 'आपः', 'जातवेदस',
        # Vedic ritual terms
        'यज्ञ', 'होत', 'होतृ', 'होतार', 'ऋत्विज', 'अध्वर', 'सोमपीत', 'हव्य',
        'पुरोहित', 'बर्हिस', 'स्रुच', 'स्रुव', 'जुहू', 'उपभृत', 'ध्रुवा',
        'इध्म', 'समिध', 'आज्य', 'घृत', 'दधि', 'मधु', 'भेषज', 'वरूथ',
        # Vedic archaic forms
        'ईळ', 'ईड', 'स्तु', 'गृणा', 'अर्च', 'नम', 'वन्द', 'शंस', 'ब्रू',
        'ऋषि', 'कवि', 'विप्र', 'वेधस', 'मेधस', 'शूर', 'महि',
        # Ritual actions
        'यज', 'जुहु', 'दा', 'भज', 'गम', 'इ', 'कृ',
        # Vedic compounds
        'रत्नधातम', 'वीरवत्तम', 'सत्यश्चित्र', 'कविक्रतु', 'घृताची',
        # Vedic verb forms (archaic endings)
        'वक्षति', 'गच्छति', 'करिष्यसि', 'एमसि', 'भरन्त',
        # Common Vedic starters and vocatives
        'अग्निमीळे', 'इन्द्रं', 'वायवा', 'मित्रं', 'सोमं',
        # Vocatives (O Vayu, O Indra, etc.) - common in Rigveda
        'वायो', 'इन्द्रा', 'अग्ने', 'देव', 'देवा',
        # Vedic imperatives and verb forms
        'याहि', 'पृणीत', 'श्रुधी', 'पाहि', 'गहि', 'एहि',
        'जुषस्व', 'शृणु', 'वेधि', 'विद्धि',
        # Vedic particles and common words
        'दृशे', 'भुजे', 'सुशिप्र', 'शतक्रतु', 'वाजिन',
        'स्तोम', 'उक्थ', 'ब्रह्म', 'गिर', 'मन्त्र', 'ऋच',
        # Vedic adjectives and epithets
        'सुमन', 'विश्वचर्षणि', 'पुरुष्टुत', 'वृषभ', 'वृषन',
        'सुदक्ष', 'सुक्रतु', 'सुशंस', 'सुमति',
        # Vedic nouns
        'रयि', 'क्षत्र', 'वाज', 'सहस', 'ओजस', 'तेजस',
        'केतु', 'अर्क', 'अर्चि', 'द्युम्न', 'श्रवस',
        # Common Rigvedic words from misclassified verses
        'अस्माकं', 'विश्वा', 'सुमनस', 'देवयंत',
    }

    # Vedic-specific suffixes and endings
    VEDIC_SUFFIXES = [
        'वत्तम', 'तम', 'वान्', 'मान्', 'आन', 'उस्',
        'षि', 'न्वत्', 'धातम', 'कृतु', 'श्रवस्',
    ]

    # Vedic word patterns (regex) - archaic forms
    VEDIC_PATTERNS = [
        r'स्व\S+',      # Words starting with स्व (sva-)
        r'\S+भिः',      # Instrumental plural ending -bhiḥ
        r'\S+षु',       # Locative plural ending -ṣu
        r'\S+ेभ्यः',    # Dative plural ending
        r'\S+ाय',       # Dative singular ending
    ]

    # Vedic Unicode range (Vedic Extensions)
    # U+1CD0-U+1CFF: Vedic Extensions including tone marks
    VEDIC_UNICODE_RANGES = [
        (0x1CD0, 0x1CFF),  # Vedic Extensions
        (0x0951, 0x0954),  # Vedic tone marks in Devanagari
    ]

    # Vedic special characters
    VEDIC_SPECIAL_CHARS = {
        '\u0951',  # Udatta (svarita)
        '\u0952',  # Anudatta
        '\u1CD0',  # Vedic tone Karshana
        '\u1CD1',  # Vedic tone Shara
        '\u1CD2',  # Vedic tone Prenkha
        '\u1CF2',  # Vedic sign Ardhavisarga
        '\u1CF3',  # Vedic sign Rotated Ardhavisarga
        '\u1CF4',  # Vedic tone Candra Above
        '\u1CF5',  # Vedic sign Jihvamuliya
        '\u1CF6',  # Vedic sign Upadhmaniya
        'ळ',       # Used in Vedic texts
    }

    # Vedic syllable counts for major meters
    # Maps syllable count -> (meter_name, is_exact)
    VEDIC_SYLLABLE_COUNTS = {
        24: ('गायत्री', True),     # 3×8 padas
        28: ('उष्णिक्', True),      # 4×7 or 8+8+12
        32: ('अनुष्टुभ्', True),    # 4×8 padas
        36: ('बृहती', True),       # 8+8+12+8 or variations
        40: ('पङ्क्ति', True),      # 5×8 or 4×10
        44: ('त्रिष्टुभ्', True),   # 4×11 padas
        48: ('जगती', True),        # 4×12 padas
        # Variations with ±2 tolerance
        22: ('गायत्री', False),
        23: ('गायत्री', False),
        25: ('गायत्री', False),
        26: ('उष्णिक्', False),
        27: ('उष्णिक्', False),
        29: ('उष्णिक्', False),
        30: ('अनुष्टुभ्', False),
        31: ('अनुष्टुभ्', False),
        33: ('अनुष्टुभ्', False),
        34: ('बृहती', False),
        35: ('बृहती', False),
        37: ('बृहती', False),
        38: ('पङ्क्ति', False),
        39: ('पङ्क्ति', False),
        41: ('पङ्क्ति', False),
        42: ('त्रिष्टुभ्', False),
        43: ('त्रिष्टुभ्', False),
        45: ('त्रिष्टुभ्', False),
        46: ('जगती', False),
        47: ('जगती', False),
        49: ('जगती', False),
        50: ('जगती', False),
    }

    # =========================================================================
    # CLASSICAL MARKERS
    # =========================================================================

    # Classical-specific vocabulary (later Sanskrit, Kavya terms)
    CLASSICAL_VOCABULARY = {
        # Common Shloka/Kavya terms
        'श्लोक', 'काव्य', 'पद्य', 'गद्य', 'अलंकार', 'रस',
        # Classical deities (with epithets)
        'राम', 'कृष्ण', 'शिव', 'पार्वती', 'गणेश', 'हनुमान', 'सीता',
        'राधा', 'गोविन्द', 'मुरारि', 'माधव', 'केशव', 'नारायण',
        # Classical themes
        'प्रेम', 'विरह', 'शृंगार', 'करुण', 'वीर', 'भक्ति', 'ज्ञान',
        'मोक्ष', 'धर्म', 'अर्थ', 'काम',
        # Nature imagery (Classical kavya)
        'मेघ', 'वर्षा', 'चन्द्र', 'सूर्य', 'तारा', 'नक्षत्र',
        'पुष्प', 'लता', 'वन', 'सरोवर', 'नदी', 'पर्वत', 'समुद्र',
        # Human elements (Classical themes)
        'राजा', 'रानी', 'नायक', 'नायिका', 'सखी', 'दूत', 'प्रिय', 'प्रिया',
        # Classical compounds and descriptions
        'चन्द्रमुख', 'कमलनयन', 'मृगनयन', 'पद्मपत्र', 'रत्नभूषण',
        # Meghaduta-style
        'यक्ष', 'विरहिन', 'प्रियतम', 'अलक', 'उज्जयिनी',
        # Bhagavad Gita markers
        'अर्जुन', 'पार्थ', 'भारत', 'कुरुक्षेत्र', 'धर्मक्षेत्र',
        'संजय', 'धृतराष्ट्र', 'पाण्डव', 'कौरव',
        # Classical philosophy
        'योग', 'सांख्य', 'वेदान्त', 'न्याय', 'तत्त्व',
        'आत्मा', 'ब्रह्म', 'माया', 'प्रकृति', 'पुरुष',
        # Markers from danda usage in classical
        'इति', 'एवं', 'तथा', 'यथा', 'अपि', 'तु', 'हि', 'च', 'वा',
    }

    # Classical structural markers
    CLASSICAL_STRUCTURAL_PATTERNS = [
        r'॥\s*\d+\s*॥',           # Verse numbering: ॥ 1 ॥
        r'\|\|',                   # Double danda
        r'।\s*$',                  # Line ending with danda
        r'॥\s*$',                  # Line ending with double danda
        r'इति\s+.*॥',             # "iti" marking end
        r'\d+\s*-\s*\d+',          # Verse references (1-5)
    ]

    # Classical meters with their typical syllable counts (often longer)
    CLASSICAL_METERS_SYLLABLES = {
        # Per line counts for classical meters
        14: ['वसन्ततिलका'],          # 14 syllables per line
        17: ['शार्दूलविक्रीडित', 'पृथ्वी'],  # 17 syllables
        19: ['स्रग्धरा'],             # 19 syllables per line
        21: ['मन्दाक्रान्ता'],         # 21 syllables per quarter (long verse)
        11: ['इन्द्रवज्रा', 'उपेन्द्रवज्रा', 'उपजाति'],  # 11 per quarter
        12: ['द्रुतविलम्बित', 'वंशस्थ'],  # 12 per quarter
    }

    # =========================================================================
    # CLASSIFICATION METHODS
    # =========================================================================

    def __init__(self):
        """Initialize the classifier with compiled patterns"""
        self.classical_patterns = [
            re.compile(p, re.UNICODE) for p in self.CLASSICAL_STRUCTURAL_PATTERNS
        ]

    def count_syllables(self, text: str) -> int:
        """
        Count syllables in Sanskrit text (approximate).
        Sanskrit syllable = vowel nucleus (can be with consonant clusters)
        """
        # Remove whitespace and punctuation
        text = re.sub(r'[\s।॥|,;:\.\-\d]+', '', text)

        # Devanagari vowels (independent and matra forms)
        vowels_independent = 'अआइईउऊऋॠऌॡएऐओऔ'
        vowels_matra = 'ािीुूृॄॢॣेैोौं'

        # Count independent vowels (stand-alone syllable nuclei)
        count = sum(1 for c in text if c in vowels_independent)

        # Count matra forms (attached to consonants)
        count += sum(1 for c in text if c in vowels_matra)

        # Count consonants without vowel signs (inherent 'a')
        # A consonant without virama or matra has inherent 'a'
        consonants = 'कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह'
        virama = '्'

        for i, c in enumerate(text):
            if c in consonants:
                # Check if followed by virama or matra
                next_idx = i + 1
                has_vowel_sign = False
                while next_idx < len(text):
                    next_c = text[next_idx]
                    if next_c == virama:
                        has_vowel_sign = True  # Actually no vowel
                        break
                    elif next_c in vowels_matra:
                        has_vowel_sign = True
                        break
                    elif next_c in consonants or next_c in vowels_independent:
                        break
                    next_idx += 1

                if not has_vowel_sign:
                    # Consonant with inherent 'a'
                    count += 1

        return count

    def count_syllables_fast(self, text: str) -> int:
        """
        Fast syllable count using vowel counting heuristic.
        Less accurate but faster for classification purposes.
        """
        text = re.sub(r'[\s।॥|,;:\.\-\d]+', '', text)

        # All vowel indicators (independent + matra)
        vowels = set('अआइईउऊऋॠऌॡएऐओऔािीुूृॄॢॣेैोौ')

        count = sum(1 for c in text if c in vowels)

        # Add inherent 'a' for consonants followed by consonants or end
        consonants = set('कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळक्षज्ञ')
        virama = '्'

        for i, c in enumerate(text):
            if c in consonants:
                # Check if next char is virama or matra
                if i + 1 >= len(text):
                    count += 1  # End of text, inherent 'a'
                elif text[i + 1] not in vowels and text[i + 1] != virama:
                    if text[i + 1] in consonants:
                        count += 1  # Inherent 'a' before consonant cluster

        return max(count, 1)

    def check_vedic_unicode(self, text: str) -> Tuple[int, List[str]]:
        """Check for Vedic-specific Unicode characters"""
        vedic_chars_found = []
        count = 0

        for char in text:
            cp = ord(char)
            # Check Vedic Unicode ranges
            for start, end in self.VEDIC_UNICODE_RANGES:
                if start <= cp <= end:
                    vedic_chars_found.append(char)
                    count += 1
                    break
            # Check specific Vedic chars
            if char in self.VEDIC_SPECIAL_CHARS:
                if char not in vedic_chars_found:
                    vedic_chars_found.append(char)
                    count += 1

        return count, vedic_chars_found

    def check_vocabulary(self, text: str) -> Tuple[int, int, List[str], List[str]]:
        """
        Check text for Vedic and Classical vocabulary markers.
        Returns: (vedic_hits, classical_hits, vedic_words, classical_words)
        """
        vedic_hits = 0
        classical_hits = 0
        vedic_words = []
        classical_words = []

        # Normalize text for matching

        for word in self.VEDIC_VOCABULARY:
            if word in text:
                vedic_hits += 1
                vedic_words.append(word)

        for word in self.CLASSICAL_VOCABULARY:
            if word in text:
                classical_hits += 1
                classical_words.append(word)

        return vedic_hits, classical_hits, vedic_words, classical_words

    def check_structural_markers(self, text: str) -> Tuple[int, List[str]]:
        """
        Check for Classical structural markers (dandas, verse numbers, etc.)
        """
        matches = []
        count = 0

        for pattern in self.classical_patterns:
            found = pattern.findall(text)
            if found:
                count += len(found)
                matches.extend(found)

        return count, matches

    def check_syllable_pattern(self, text: str) -> Tuple[str, float]:
        """
        Check if syllable count matches Vedic meter patterns.
        Returns: (likely_meter, confidence)
        """
        syllables = self.count_syllables_fast(text)

        if syllables in self.VEDIC_SYLLABLE_COUNTS:
            meter, is_exact = self.VEDIC_SYLLABLE_COUNTS[syllables]
            confidence = 0.9 if is_exact else 0.7
            return meter, confidence

        # Check for classical per-line patterns
        # Split by danda and check per-line syllables
        lines = re.split(r'[।॥|\n]', text)
        lines = [ln.strip() for ln in lines if ln.strip()]

        if lines:
            per_line_syllables = [self.count_syllables_fast(ln) for ln in lines]
            avg_syllables = sum(per_line_syllables) / len(per_line_syllables)

            # Classical meters typically have 11-21 syllables per quarter
            for count, meters in self.CLASSICAL_METERS_SYLLABLES.items():
                if abs(avg_syllables - count) <= 1:
                    return meters[0], 0.6  # Classical meter match

        return None, 0.0

    def check_line_structure(self, text: str) -> Tuple[str, Dict]:
        """
        Analyze the line/pada structure of the text.
        Vedic: typically space-separated padas or single continuous text
        Classical: danda-separated lines with specific structure
        """
        # Count dandas
        single_danda = text.count('।')
        double_danda = text.count('॥')
        newlines = text.count('\n')

        # Check for space-separated structure (Vedic style)
        words = text.split()

        structure = {
            'single_danda': single_danda,
            'double_danda': double_danda,
            'newlines': newlines,
            'word_count': len(words),
        }

        # Classical typically has dandas separating lines
        if double_danda > 0 or (single_danda >= 2 and newlines > 0):
            return 'classical', structure

        # Vedic often has continuous text or space-separated padas
        if single_danda <= 1 and double_danda == 0 and newlines == 0:
            return 'vedic', structure

        return 'uncertain', structure

    def classify(self, text: str) -> Tuple[str, float, Dict]:
        """
        Main classification method.
        
        Args:
            text: Sanskrit text to classify
            
        Returns:
            Tuple of (classification, confidence, features)
            classification: 'vedic' or 'classical'
            confidence: 0.0 to 1.0
            features: dict of detected features
        """
        features = {}
        vedic_score = 0.0
        classical_score = 0.0

        # 0. Quick check: if text has multiple lines with dandas, likely classical
        single_danda = text.count('।')
        double_danda = text.count('॥')
        newlines = text.count('\n')

        # Strong classical indicators (multi-line with dandas)
        if double_danda >= 1 or (single_danda >= 2 and newlines >= 1):
            classical_score += 0.4  # Strong structural indicator

        # 1. Check syllable count
        syllables = self.count_syllables_fast(text)
        features['syllable_count'] = syllables

        # Vedic verses have specific total syllable counts
        # Check if it's in the exact Vedic meter range
        meter, meter_conf = self.check_syllable_pattern(text)
        features['likely_meter'] = meter
        features['meter_confidence'] = meter_conf

        # Only boost Vedic score for exact Vedic counts if NO structural classical markers
        if meter and meter in ['गायत्री', 'उष्णिक्', 'अनुष्टुभ्', 'बृहती',
                               'पङ्क्ति', 'त्रिष्टुभ्', 'जगती']:
            if double_danda == 0 and single_danda <= 1:
                vedic_score += meter_conf * 0.35  # Only if no dandas
            else:
                vedic_score += meter_conf * 0.1   # Reduced if dandas present
        elif meter:
            classical_score += meter_conf * 0.2

        # 2. Check Vedic Unicode characters (very strong indicator)
        vedic_unicode_count, vedic_chars = self.check_vedic_unicode(text)
        features['vedic_unicode_count'] = vedic_unicode_count
        features['vedic_chars'] = vedic_chars

        if vedic_unicode_count > 0:
            vedic_score += 0.5  # Strong Vedic indicator (increased)

        # 3. Check vocabulary
        vedic_vocab, classical_vocab, v_words, c_words = self.check_vocabulary(text)
        features['vedic_vocab_hits'] = vedic_vocab
        features['classical_vocab_hits'] = classical_vocab
        features['vedic_words'] = v_words
        features['classical_words'] = c_words

        # Vocabulary scoring (important differentiator)
        vocab_diff = vedic_vocab - classical_vocab
        if vocab_diff > 0:
            # More Vedic vocabulary - stronger weight
            vedic_score += min(vocab_diff * 0.15, 0.4)
        elif vocab_diff < 0:
            # More Classical vocabulary
            classical_score += min(abs(vocab_diff) * 0.1, 0.3)

        # Even a single Vedic vocabulary hit without dandas is strong signal
        if vedic_vocab > 0 and double_danda == 0 and single_danda <= 1:
            vedic_score += 0.15

        # 4. Check structural markers (verse numbers, specific patterns)
        struct_count, struct_matches = self.check_structural_markers(text)
        features['structural_markers'] = struct_count
        features['structural_matches'] = struct_matches

        if struct_count > 0:
            classical_score += 0.25  # Classical structural pattern

        # 5. Check line structure
        line_type, line_struct = self.check_line_structure(text)
        features['line_structure'] = line_struct
        features['line_type'] = line_type

        if line_type == 'vedic':
            vedic_score += 0.2
        elif line_type == 'classical':
            classical_score += 0.2

        # 6. Text length heuristic
        # Vedic mantras tend to be single-line continuous
        # Classical shlokas tend to have multiple lines
        if newlines >= 2:
            classical_score += 0.15
        elif newlines == 0 and len(text) < 150:
            vedic_score += 0.15  # Increased weight

        # 6b. No dandas at all is a strong Vedic indicator
        if single_danda == 0 and double_danda == 0:
            vedic_score += 0.2

        # 7. Per-line syllable count (Classical has consistent per-line counts)
        lines = re.split(r'[।॥\n]', text)
        lines = [ln.strip() for ln in lines if ln.strip() and len(ln.strip()) > 5]
        if len(lines) >= 2:
            per_line_syllables = [self.count_syllables_fast(ln) for ln in lines]
            avg = sum(per_line_syllables) / len(per_line_syllables)

            # Classical meters have specific per-line counts
            if 10 <= avg <= 21 and len(lines) >= 2:
                # Check variance - classical is very regular
                variance = sum((s - avg) ** 2 for s in per_line_syllables) / len(per_line_syllables)
                if variance < 4:  # Very consistent
                    classical_score += 0.2

        # 8. Check for specific markers
        # "॥" at end strongly suggests classical
        if text.strip().endswith('॥') or text.strip().endswith('।।'):
            classical_score += 0.2

        # 9. Compound word density (Classical has more elaborate compounds)
        # Approximated by average word length
        words = text.split()
        if words:
            avg_word_len = sum(len(w) for w in words) / len(words)
            if avg_word_len > 12:  # Long compound words
                classical_score += 0.1

        # 10. Final structural override
        # If absolutely no punctuation and syllables in Vedic range, boost Vedic
        if single_danda == 0 and double_danda == 0 and 20 <= syllables <= 50:
            vedic_score += 0.15

        # Normalize scores
        total_score = vedic_score + classical_score
        if total_score > 0:
            vedic_score /= total_score
            classical_score /= total_score
        else:
            # Default: use structural heuristic
            if double_danda > 0 or single_danda >= 2:
                vedic_score = 0.3
                classical_score = 0.7
            else:
                vedic_score = 0.7  # Increased default Vedic score
                classical_score = 0.3

        # Determine classification
        if vedic_score > classical_score:
            classification = 'vedic'
            confidence = vedic_score
        else:
            classification = 'classical'
            confidence = classical_score

        features['vedic_score'] = vedic_score
        features['classical_score'] = classical_score

        return classification, confidence, features

    def classify_batch(self, texts: List[str]) -> List[Tuple[str, float, Dict]]:
        """Classify multiple texts"""
        return [self.classify(text) for text in texts]

    def get_recommended_mode(self, text: str) -> str:
        """
        Get the recommended mode for Chanda identification.
        
        Returns:
            'vedic' or 'classical' - the recommended mode parameter
        """
        classification, confidence, _ = self.classify(text)
        return classification


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_classifier = None

def get_classifier() -> TextClassifier:
    """Get singleton classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = TextClassifier()
    return _classifier


def classify_text(text: str) -> Tuple[str, float]:
    """
    Quick classification of text.
    
    Args:
        text: Sanskrit text
        
    Returns:
        (classification, confidence) tuple
    """
    classifier = get_classifier()
    classification, confidence, _ = classifier.classify(text)
    return classification, confidence


def get_mode(text: str) -> str:
    """
    Get recommended Chanda identification mode for text.
    
    Args:
        text: Sanskrit text
        
    Returns:
        'vedic' or 'classical'
    """
    classifier = get_classifier()
    return classifier.get_recommended_mode(text)


def is_vedic(text: str, threshold: float = 0.5) -> bool:
    """Check if text is likely Vedic"""
    classification, confidence = classify_text(text)
    return classification == 'vedic' and confidence >= threshold


def is_classical(text: str, threshold: float = 0.5) -> bool:
    """Check if text is likely Classical"""
    classification, confidence = classify_text(text)
    return classification == 'classical' and confidence >= threshold


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    # Test samples
    vedic_samples = [
        "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं",
        "इन्द्रं मित्रं वरुणमग्निमाहुरथो दिव्यः स सुपर्णो गरुत्मान्",
        "वायवा याहि दर्शतेमे सोमा अरंकृताः तेषां पाहि श्रुधी हवं",
    ]

    classical_samples = [
        "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः। मामकाः पाण्डवाश्चैव किमकुर्वत संजय॥",
        "श्यामास्वाङ्गं चकितहरिणीप्रेक्षणे दृष्टिपातं वक्त्रच्छायां शशिनि शिखिनां बर्हभारेषु केशान्",
        "न तातो न माता न बन्धुर्न दाता न पुत्रो न पुत्री न भृत्यो न भर्ता",
    ]

    classifier = TextClassifier()

    print("=" * 60)
    print("VEDIC SAMPLES")
    print("=" * 60)
    for text in vedic_samples:
        cls, conf, features = classifier.classify(text)
        print(f"\nText: {text[:50]}...")
        print(f"  Classification: {cls}")
        print(f"  Confidence: {conf:.2f}")
        print(f"  Syllables: {features['syllable_count']}")
        print(f"  Likely meter: {features.get('likely_meter', 'Unknown')}")

    print("\n" + "=" * 60)
    print("CLASSICAL SAMPLES")
    print("=" * 60)
    for text in classical_samples:
        cls, conf, features = classifier.classify(text)
        print(f"\nText: {text[:50]}...")
        print(f"  Classification: {cls}")
        print(f"  Confidence: {conf:.2f}")
        print(f"  Syllables: {features['syllable_count']}")
        print(f"  Structural markers: {features['structural_markers']}")
