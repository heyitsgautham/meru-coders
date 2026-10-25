"""Syllable counting and positions for PadaSplitter, for Devanagari, IAST and SLP1 input.

Mixed into backend.utils.pada_splitter.PadaSplitter."""

import re
from typing import List, Tuple

from indic_transliteration import sanscript
from indic_transliteration.detect import detect
from indic_transliteration.sanscript import transliterate


class PadaSyllables:
    # Sanskrit/Devanagari vowels for syllable counting
    # Independent vowels
    DEVANAGARI_VOWELS = 'अआइईउऊऋॠऌॡएऐओऔ'

    # Dependent vowels (mātrās)
    DEVANAGARI_MATRAS = 'ािीुूृॄॢॣेैोौ'

    # IAST/transliteration vowels (including long vowels with macrons)
    IAST_VOWELS = 'aāiīuūṛṝḷḹeaioau'

    IAST_VOWELS_PATTERN = r'[aāiīuūṛṝḷḹeo]|ai|au'

    # SLP1 vowels
    SLP1_VOWELS = 'aAiIuUfFxXeEoO'

    def _detect_script(self, text: str) -> str:
        """Detect the script of the input text"""
        try:
            detected = detect(text)
            if detected:
                return detected
        except Exception:
            pass

        # Fallback detection
        if any(c in text for c in self.DEVANAGARI_VOWELS + self.DEVANAGARI_MATRAS):
            return sanscript.DEVANAGARI
        elif any(c in text for c in 'āīūṛṝḷḹṃḥṅñṭḍṇśṣ'):
            return sanscript.IAST
        elif any(c in text for c in 'AIUFXEO'):  # SLP1 specific
            return sanscript.SLP1
        else:
            return sanscript.IAST  # Default to IAST for romanized

    def _to_devanagari(self, text: str) -> str:
        """Convert text to Devanagari if not already"""
        script = self._detect_script(text)
        if script == sanscript.DEVANAGARI:
            return text
        try:
            return transliterate(text, script, sanscript.DEVANAGARI)
        except Exception:
            return text

    def count_syllables(self, text: str) -> int:
        """
        Count syllables in Sanskrit text by counting vowels.

        In Sanskrit, each syllable (akṣara) contains exactly one vowel sound.
        A syllable can be:
        - An independent vowel (अ, आ, इ, etc.)
        - A consonant + dependent vowel (मा, कि, etc.)
        - A consonant cluster + vowel (स्त्र + vowel)

        Args:
            text: Sanskrit text (Devanagari or transliteration)

        Returns:
            Number of syllables
        """
        script = self._detect_script(text)

        if script == sanscript.DEVANAGARI:
            return self._count_syllables_devanagari(text)
        else:
            # Convert to Devanagari for consistent counting
            devanagari = self._to_devanagari(text)
            return self._count_syllables_devanagari(devanagari)

    def _count_syllables_devanagari(self, text: str) -> int:
        """
        Count syllables in Devanagari text.

        Rules:
        1. Each independent vowel = 1 syllable
        2. Each consonant with inherent 'a' or explicit mātrā = 1 syllable
        3. Consonant with halant (्) = 0 syllables (combines with next)
        4. Anusvara (ं) and visarga (ः) don't add syllables
        5. Special symbols like ॐ (Om) = 1 syllable
        """
        # Remove spaces and punctuation
        text = re.sub(r'[\s।॥,\.!?\d]+', '', text)

        # Handle special symbols first
        # Om (ॐ) is a single syllable
        om_count = text.count('ॐ')
        text = text.replace('ॐ', '')  # Remove Om for further processing

        # Count independent vowels
        independent_vowels = sum(1 for c in text if c in self.DEVANAGARI_VOWELS)

        # Count dependent vowels (mātrās)
        dependent_vowels = sum(1 for c in text if c in self.DEVANAGARI_MATRAS)

        # Count consonants with inherent 'a' (no halant, no mātrā following)
        # A consonant has inherent 'a' if:
        # - It's not followed by halant (्)
        # - It's not followed by a mātrā
        consonant_pattern = r'[क-ह](?![्' + self.DEVANAGARI_MATRAS + '])'
        inherent_a_consonants = len(re.findall(consonant_pattern, text))

        # Handle special cases
        # Avagraha (ऽ) represents elided 'a' - counts as syllable
        avagraha_count = text.count('ऽ')

        total = independent_vowels + dependent_vowels + inherent_a_consonants + avagraha_count + om_count

        return total

    def get_syllables_with_positions(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Get syllables with their character positions in the original text.

        Returns:
            List of (syllable_text, start_pos, end_pos) tuples
        """
        # Convert to Devanagari for processing
        devanagari = self._to_devanagari(text)

        syllables = []
        current_syllable = ""
        start_pos = 0

        i = 0
        while i < len(devanagari):
            char = devanagari[i]

            # Skip whitespace and punctuation
            if char in ' \t\n।॥,।':
                if current_syllable:
                    syllables.append((current_syllable, start_pos, i))
                    current_syllable = ""
                i += 1
                continue

            # Independent vowel starts a new syllable
            if char in self.DEVANAGARI_VOWELS:
                if current_syllable:
                    syllables.append((current_syllable, start_pos, i))
                start_pos = i
                current_syllable = char
                i += 1
                # Include any following nasalization or visarga
                while i < len(devanagari) and devanagari[i] in 'ंःँ':
                    current_syllable += devanagari[i]
                    i += 1
                syllables.append((current_syllable, start_pos, i))
                current_syllable = ""
                continue

            # Consonant
            if '\u0915' <= char <= '\u0939':  # क to ह
                if current_syllable:
                    # Check if previous syllable is complete
                    # (has a vowel or ends without halant)
                    if any(c in self.DEVANAGARI_MATRAS + self.DEVANAGARI_VOWELS for c in current_syllable) or (
                        current_syllable and current_syllable[-1] not in '्'
                    ):
                        syllables.append((current_syllable, start_pos, i))
                        start_pos = i
                        current_syllable = ""

                if not current_syllable:
                    start_pos = i

                current_syllable += char
                i += 1

                # Consume any following halants and consonants (conjuncts)
                while i < len(devanagari):
                    if devanagari[i] == '्':  # Halant
                        current_syllable += devanagari[i]
                        i += 1
                        # Next should be a consonant in a conjunct
                        if i < len(devanagari) and '\u0915' <= devanagari[i] <= '\u0939':
                            current_syllable += devanagari[i]
                            i += 1
                        else:
                            break
                    elif devanagari[i] in self.DEVANAGARI_MATRAS:
                        # Mātrā completes the syllable
                        current_syllable += devanagari[i]
                        i += 1
                        # Include any following anusvara/visarga
                        while i < len(devanagari) and devanagari[i] in 'ंःँ':
                            current_syllable += devanagari[i]
                            i += 1
                        break
                    elif devanagari[i] in 'ंःँ':
                        # Anusvara/visarga on inherent 'a'
                        current_syllable += devanagari[i]
                        i += 1
                    else:
                        break

                continue

            # Other characters (nukta, etc.)
            if current_syllable:
                current_syllable += char
            i += 1

        # Don't forget the last syllable
        if current_syllable:
            syllables.append((current_syllable, start_pos, len(devanagari)))

        return syllables

    def _get_syllable_boundaries(self, word: str) -> List[Tuple[int, int]]:
        """
        Get the character boundaries of each syllable in a word.

        Returns:
            List of (start, end) tuples for each syllable
        """
        boundaries = []
        i = 0
        start = 0

        while i < len(word):
            char = word[i]

            # Independent vowel
            if char in self.DEVANAGARI_VOWELS:
                start = i
                i += 1
                # Include following anusvara/visarga
                while i < len(word) and word[i] in 'ंःँ':
                    i += 1
                boundaries.append((start, i))
                start = i
                continue

            # Consonant
            if '\u0915' <= char <= '\u0939':
                if i == start:
                    start = i

                i += 1

                # Process consonant clusters and mātrās
                while i < len(word):
                    if word[i] == '्':  # Halant
                        i += 1
                        if i < len(word) and '\u0915' <= word[i] <= '\u0939':
                            i += 1
                        else:
                            break
                    elif word[i] in self.DEVANAGARI_MATRAS:
                        i += 1
                        while i < len(word) and word[i] in 'ंःँ':
                            i += 1
                        break
                    elif word[i] in 'ंःँ':
                        i += 1
                    else:
                        break

                boundaries.append((start, i))
                start = i
                continue

            # Other characters
            i += 1

        return boundaries
