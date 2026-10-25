#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hybrid Implementation
Combines ICU-based syllabization with our existing pattern matching logic
"""

import functools

import regex
from indic_transliteration import sanscript

from backend.core.chanda import Chanda

MAX_CACHE = 1024


class ChandaHybrid(Chanda):
    """
    Hybrid Chanda Identifier
    Uses ICU-based syllabization + our existing pattern matching and data
    """

    def __init__(self, data_path, symbols='यरतनभजसमलग'):
        # Initialize parent class
        super().__init__(data_path, symbols)
        self.syllabization_method = 'icu'  # Track which method is being used

    # Override syllabization with ICU-based method
    def get_syllables_icu(self, in_string):
        """Split devanagari string into syllables using ICU logic"""
        dev_scheme = sanscript.SCHEMES[sanscript.DEVANAGARI]
        cleaned_phrase = in_string

        # Preprocess OM
        cleaned_phrase = regex.sub("[%s]" % dev_scheme.PATTERN_OM, "ओम्", cleaned_phrase)

        # Remove non-letter characters
        cleaned_phrase = regex.sub(
            r"([^%s%s%s%s%s%s])"
            % (
                dev_scheme.PATTERN_INDEPENDENT_VOWEL,
                dev_scheme.PATTERN_VYANJANA,
                dev_scheme.PATTERN_DEPENDENT_VOWEL,
                dev_scheme.PATTERN_YOGAVAAHA,
                dev_scheme.PATTERN_ACCENT,
                dev_scheme.PATTERN_CONSONANT_MODIFIER,
            ),
            "",
            cleaned_phrase,
            flags=regex.UNICODE,
        )

        cleaned_phrase = cleaned_phrase.replace(" ", "")

        # Join vyanjana + independent vowel
        cleaned_phrase = regex.sub(
            r"(%s)([%s])" % (dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL, dev_scheme.PATTERN_INDEPENDENT_VOWEL),
            lambda x: sanscript.SCHEMES[sanscript.DEVANAGARI].do_vyanjana_svara_join(x.group(1), x.group(2)),
            cleaned_phrase,
        )

        syllables = []
        while len(cleaned_phrase) > 0:
            match = regex.match(
                (
                    r"(%s)*[%s%s]़?[%s]*[%s]*[%s]*(%sँ?)*"
                    % (
                        dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL,
                        dev_scheme.PATTERN_INDEPENDENT_VOWEL,
                        dev_scheme.PATTERN_VYANJANA,
                        dev_scheme.PATTERN_DEPENDENT_VOWEL,
                        dev_scheme.PATTERN_YOGAVAAHA,
                        dev_scheme.PATTERN_ACCENT,
                        dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL,
                    )
                ),
                cleaned_phrase,
            )
            if match is None:
                break
            current_syllable = match.group(0)
            cleaned_phrase = cleaned_phrase.replace(match.group(0), "", 1)
            if len(current_syllable) > 0:
                syllables.append(current_syllable)

        return syllables

    def get_syllable_weight_icu(self, syllable):
        """Get weight (L/G) of a syllable using ICU logic"""
        dev_scheme = sanscript.SCHEMES[sanscript.DEVANAGARI]

        # Check for guru vowels
        if regex.findall(
            r"[%s%s%s]"
            % (
                dev_scheme.PATTERN_GURU_INDEPENDENT_VOWEL,
                dev_scheme.PATTERN_GURU_DEPENDENT_VOWEL,
                dev_scheme.PATTERN_GURU_YOGAVAAHA,
            ),
            syllable,
        ):
            return self.G

        # Check for conjunct consonants (makes it guru)
        elif regex.findall(
            r"[%s%s]़?[%s]*[%s]*[%s]*(%s)+"
            % (
                dev_scheme.PATTERN_INDEPENDENT_VOWEL,
                dev_scheme.PATTERN_VYANJANA,
                dev_scheme.PATTERN_DEPENDENT_VOWEL,
                dev_scheme.PATTERN_YOGAVAAHA,
                dev_scheme.PATTERN_ACCENT,
                dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL,
            ),
            syllable,
        ):
            return self.G
        else:
            return self.L

    @functools.lru_cache(maxsize=MAX_CACHE)  # noqa: B019 - one long-lived engine per process
    def mark_lg(self, text):
        """
        Mark Laghu-Guru using ICU syllabization
        Overrides parent method to use ICU-based approach
        """
        # Preprocess text for Vedic markers (keep this from parent)
        if self.detect_vedic_markers(text):
            text = self.preprocess_vedic_text(text)

        # Use ICU syllabization
        syllables_flat = self.get_syllables_icu(text)
        lg_marks = [self.get_syllable_weight_icu(syl) for syl in syllables_flat]

        # Wrap in nested list structure to match parent's return format
        # Parent returns: [[['syl1', 'syl2'], ['syl3']]], [L, G, L]
        # We return: [[syllables_flat]], lg_marks
        syllables = [[syllables_flat]]

        return syllables, lg_marks

    def get_method_info(self):
        """Return information about which syllabization method is being used"""
        return {
            'syllabization': 'ICU-based',
            'pattern_matching': 'Original (from chanda.py)',
            'data': 'Merged dataset (1,850 meters)',
        }
