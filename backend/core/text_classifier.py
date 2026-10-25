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

from . import text_classifier_vocab as vocab


class TextClassifier:
    """
    Classifies Sanskrit text as Vedic or Classical based on linguistic features.

    Usage:
        classifier = TextClassifier()
        text_type, confidence, features = classifier.classify("अग्निमीळे पुरोहितं...")
        # Returns: ('vedic', 0.85, {'syllable_count': 24, 'vedic_vocab_hits': 3, ...})
    """

    # Vocabulary and pattern tables live in text_classifier_vocab.py.
    VEDIC_VOCABULARY = vocab.VEDIC_VOCABULARY
    VEDIC_SUFFIXES = vocab.VEDIC_SUFFIXES
    VEDIC_PATTERNS = vocab.VEDIC_PATTERNS
    VEDIC_UNICODE_RANGES = vocab.VEDIC_UNICODE_RANGES
    VEDIC_SPECIAL_CHARS = vocab.VEDIC_SPECIAL_CHARS
    VEDIC_SYLLABLE_COUNTS = vocab.VEDIC_SYLLABLE_COUNTS
    CLASSICAL_VOCABULARY = vocab.CLASSICAL_VOCABULARY
    CLASSICAL_STRUCTURAL_PATTERNS = vocab.CLASSICAL_STRUCTURAL_PATTERNS
    CLASSICAL_METERS_SYLLABLES = vocab.CLASSICAL_METERS_SYLLABLES

    # =========================================================================
    # CLASSIFICATION METHODS
    # =========================================================================

    def __init__(self):
        """Initialize the classifier with compiled patterns"""
        self.classical_patterns = [re.compile(p, re.UNICODE) for p in self.CLASSICAL_STRUCTURAL_PATTERNS]

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
        vedic_words = [word for word in self.VEDIC_VOCABULARY if word in text]
        classical_words = [word for word in self.CLASSICAL_VOCABULARY if word in text]
        return len(vedic_words), len(classical_words), vedic_words, classical_words

    def check_structural_markers(self, text: str) -> Tuple[int, List[str]]:
        """
        Check for Classical structural markers (dandas, verse numbers, etc.)
        """
        matches = [match for pattern in self.classical_patterns for match in pattern.findall(text)]
        return len(matches), matches

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
        if meter and meter in ['गायत्री', 'उष्णिक्', 'अनुष्टुभ्', 'बृहती', 'पङ्क्ति', 'त्रिष्टुभ्', 'जगती']:
            if double_danda == 0 and single_danda <= 1:
                vedic_score += meter_conf * 0.35  # Only if no dandas
            else:
                vedic_score += meter_conf * 0.1  # Reduced if dandas present
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
        classical_score += self._line_regularity_score(text)

        # 8. Check for specific markers
        # "॥" at end strongly suggests classical
        if text.strip().endswith('॥') or text.strip().endswith('।।'):
            classical_score += 0.2

        # 9. Compound word density (Classical has more elaborate compounds)
        classical_score += self._compound_density_score(text)

        # 10. Final structural override
        # If absolutely no punctuation and syllables in Vedic range, boost Vedic
        if single_danda == 0 and double_danda == 0 and 20 <= syllables <= 50:
            vedic_score += 0.15

        vedic_score, classical_score = self._normalize_scores(vedic_score, classical_score, single_danda, double_danda)
        if vedic_score > classical_score:
            classification, confidence = 'vedic', vedic_score
        else:
            classification, confidence = 'classical', classical_score

        features['vedic_score'] = vedic_score
        features['classical_score'] = classical_score

        return classification, confidence, features

    def _line_regularity_score(self, text: str) -> float:
        """0.2 when a multi-line text keeps a near-constant 10 to 21 syllables per line, as classical verse does."""
        lines = re.split(r'[।॥\n]', text)
        lines = [ln.strip() for ln in lines if ln.strip() and len(ln.strip()) > 5]
        if len(lines) < 2:
            return 0.0
        per_line_syllables = [self.count_syllables_fast(ln) for ln in lines]
        avg = sum(per_line_syllables) / len(per_line_syllables)
        if not 10 <= avg <= 21:
            return 0.0
        variance = sum((s - avg) ** 2 for s in per_line_syllables) / len(per_line_syllables)
        return 0.2 if variance < 4 else 0.0

    @staticmethod
    def _compound_density_score(text: str) -> float:
        """0.1 when the average word is longer than 12 characters, a sign of classical compounds."""
        words = text.split()
        if words and sum(len(w) for w in words) / len(words) > 12:
            return 0.1
        return 0.0

    @staticmethod
    def _normalize_scores(vedic: float, classical: float, single_danda: int, double_danda: int) -> Tuple[float, float]:
        """Scale both scores to sum to 1; with no evidence at all, lean on the danda count."""
        total = vedic + classical
        if total > 0:
            return vedic / total, classical / total
        if double_danda > 0 or single_danda >= 2:
            return 0.3, 0.7
        return 0.7, 0.3

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
