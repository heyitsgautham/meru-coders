"""Input screening (is this Sanskrit verse?) and Vedic text normalization.

Mixed into backend.core.chanda.Chanda; methods rely on its other mixins through self.
"""

import re

from .chanda_input_words import COMMON_ENGLISH_WORDS


class InputCheckMixin:
    # ----------------------------------------------------------------------- #
    # Preprocessing and Normalization Functions
    # ----------------------------------------------------------------------- #

    def is_valid_sanskrit_input(self, text):
        """
        Check if the input text contains valid Sanskrit/Indic script characters.

        This method validates that the input is actually Sanskrit text (in any
        supported script like Devanagari, IAST, SLP1, etc.) and not random
        ASCII characters, English text, or gibberish.

        Args:
            text: Input text string

        Returns:
            tuple: (is_valid: bool, reason: str)
        """
        if not text or not text.strip():
            return False, "खाली पाठ (Empty input)"

        text = text.strip()

        # Minimum length check - single characters or very short strings are not valid verses
        # A valid Sanskrit word/phrase should have at least 2-3 characters
        MIN_LENGTH_ASCII = 3  # Minimum for romanized: "om", "aum", etc.
        MIN_LENGTH_DEVANAGARI = 2  # Minimum for Devanagari: "ॐ" is special case

        # Check for Devanagari characters (U+0900 to U+097F)
        devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097f')

        # Check for other Indic scripts (Bengali, Telugu, Tamil, etc.)
        other_indic_chars = sum(
            1
            for c in text
            if (
                '\u0980' <= c <= '\u09ff'  # Bengali
                or '\u0a00' <= c <= '\u0a7f'  # Gurmukhi
                or '\u0a80' <= c <= '\u0aff'  # Gujarati
                or '\u0b00' <= c <= '\u0b7f'  # Oriya
                or '\u0b80' <= c <= '\u0bff'  # Tamil
                or '\u0c00' <= c <= '\u0c7f'  # Telugu
                or '\u0c80' <= c <= '\u0cff'  # Kannada
                or '\u0d00' <= c <= '\u0d7f'  # Malayalam
            )
        )

        # Check for IAST/romanized Sanskrit characters
        # IAST uses Latin letters with diacritics: ā ī ū ṛ ṝ ḷ ḹ ṃ ḥ ñ ṅ ṭ ḍ ṇ ś ṣ
        iast_diacritics = set('āīūṛṝḷḹṃḥñṅṭḍṇśṣĀĪŪṚṜḶḸṂḤÑṄṬḌṆŚṢ')
        iast_chars = sum(1 for c in text if c in iast_diacritics)

        # Check for basic Latin vowels that are common in Sanskrit transliteration
        latin_vowels = set('aeiouAEIOU')
        latin_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        latin_vowel_count = sum(1 for c in text if c in latin_vowels)

        # Total meaningful characters (excluding spaces, punctuation, numbers)
        total_alpha = sum(1 for c in text if c.isalpha() or '\u0900' <= c <= '\u0d7f')

        if total_alpha == 0:
            return False, "कोई वर्ण नहीं मिला (No alphabetic characters found)"

        # Special case: ॐ (Om) is valid even though it's a single character
        if text == 'ॐ' or text.lower() in ['om', 'aum']:
            return True, "ॐ (Om mantra)"

        # Minimum length validation
        if devanagari_chars > 0 or other_indic_chars > 0:
            # Indic script
            if len(text) < MIN_LENGTH_DEVANAGARI:
                return (
                    False,
                    f"पाठ बहुत छोटा है (Text too short - minimum {MIN_LENGTH_DEVANAGARI} characters for Indic script)",
                )
        else:
            # ASCII/romanized
            if len(text) < MIN_LENGTH_ASCII:
                return False, f"पाठ बहुत छोटा है (Text too short - minimum {MIN_LENGTH_ASCII} characters)"

        # *** ENGLISH TEXT DETECTION ***
        # Check if input contains common English words
        # CRITICAL: Reject English text that is NOT IAST transliteration
        # IAST has diacritics (ā, ī, ū, ṛ, ṝ, ḷ, ḹ, ṃ, ḥ, ñ, ṅ, ṭ, ḍ, ṇ, ś, ṣ)
        # Plain English has NO diacritics - this is the key distinction
        if devanagari_chars == 0 and other_indic_chars == 0:
            # Pure ASCII/Latin input - check if it's English vs IAST
            text_lower = text.lower()
            words = re.findall(r'[a-z]+', text_lower)

            # If NO IAST diacritics present, this is likely English, not Sanskrit
            if iast_chars == 0 and words:
                english_word_count = sum(1 for word in words if word in COMMON_ENGLISH_WORDS)
                total_words = len(words)

                # Stricter thresholds when NO diacritics present
                # If even ONE common English word exists, reject (since no diacritics = not IAST)
                if english_word_count >= 1:
                    return (
                        False,
                        "अंग्रेजी पाठ प्रतीत होता है - संस्कृत के लिए IAST लिप्यन्तरण में diakritik चिह्न आवश्यक हैं (Appears to be English text - Sanskrit IAST requires diacritical marks)",
                    )

                # If more than 20% of words are common English words, reject
                if total_words > 0 and english_word_count / total_words > 0.2:
                    return False, "अंग्रेजी पाठ प्रतीत होता है (Appears to be English text, not Sanskrit)"

                # Check for repeated words (like "hello hello hello")
                word_counts = {}
                for word in words:
                    word_counts[word] = word_counts.get(word, 0) + 1

                # If any word repeats 2+ times and it's an English word, reject
                for word, count in word_counts.items():
                    if count >= 2 and word in COMMON_ENGLISH_WORDS:
                        return False, "अंग्रेजी पाठ प्रतीत होता है (Appears to be English text with repeated words)"

            # If IAST diacritics ARE present, be more lenient
            # Some Sanskrit words transliterated might coincidentally match English words
            elif iast_chars > 0 and words:
                english_word_count = sum(1 for word in words if word in COMMON_ENGLISH_WORDS)
                total_words = len(words)

                # With diacritics present, only reject if majority are English words
                if total_words > 0 and english_word_count / total_words > 0.6:
                    return False, "अंग्रेजी पाठ प्रतीत होता है (Appears to be English text, not Sanskrit)"

        # Calculate ratios
        devanagari_ratio = devanagari_chars / len(text)
        indic_ratio = (devanagari_chars + other_indic_chars) / len(text)
        iast_ratio = (iast_chars + latin_chars) / len(text) if iast_chars > 0 else 0

        # Case 1: Has Devanagari - definitely valid
        if devanagari_ratio > 0.3:
            return True, "देवनागरी लिपि (Devanagari script detected)"

        # Case 2: Has other Indic script - valid
        if indic_ratio > 0.3:
            return True, "भारतीय लिपि (Indic script detected)"

        # Case 3: Has IAST diacritics - valid romanized Sanskrit
        if iast_chars > 0 and iast_ratio > 0.1:
            return True, "IAST लिप्यन्तरण (IAST transliteration detected)"

        # Case 4: Pure ASCII without IAST diacritics
        # This is tricky - could be SLP1 or Harvard-Kyoto, or could be gibberish
        # Check for vowel ratio (Sanskrit has high vowel density)
        if latin_chars > 0 and latin_vowel_count > 0:
            vowel_ratio = latin_vowel_count / latin_chars

            # Sanskrit typically has vowel ratio of 0.3-0.5
            # Gibberish like "djajjkvdskldsjlsdfjkl" has very low vowel ratio
            if vowel_ratio < 0.15:
                return False, "अमान्य पाठ - स्वर अनुपात न्यून (Invalid text - vowel ratio too low for Sanskrit)"

            # Check for common Sanskrit consonant clusters
            # Valid SLP1/HK: "dharma", "karma", "yoga" etc.
            # Invalid: "djajjkvdskl" (impossible consonant clusters)
            text_lower = text.lower()
            impossible_clusters = ['dj', 'kv', 'jj', 'fj', 'vd', 'ld', 'jl', 'fk', 'dk']
            cluster_count = sum(1 for cluster in impossible_clusters if cluster in text_lower)

            if cluster_count >= 2:
                return False, "अमान्य पाठ - असंभव व्यञ्जन संयोग (Invalid text - impossible consonant clusters)"

            # If vowel ratio is reasonable, assume it might be valid transliteration
            if vowel_ratio >= 0.25:
                return True, "संभावित लिप्यन्तरण (Possible transliteration)"
            else:
                return False, "अनिश्चित पाठ - कृपया देवनागरी में प्रविष्ट करें (Uncertain text - please enter in Devanagari)"

        return False, "अमान्य पाठ (Invalid text format)"

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
        text = text.replace('\u1cf2', 'ः')

        # U+1CF3: VEDIC SIGN ROTATED ARDHAVISARGA - normalize to ः
        text = text.replace('\u1cf3', 'ः')

        # U+1CF4: VEDIC TONE CANDRA ABOVE - tone marker, can be removed
        text = text.replace('\u1cf4', '')

        # Vedic signs for jihvāmūlīya (क् before) and upadhmanīya (प् before)
        # These are allophonic variants of visarga before k/p
        # U+1CF5: VEDIC SIGN JIHVAMULIYA (visarga before क, ख, etc.)
        text = text.replace('\u1cf5', 'ः')

        # U+1CF6: VEDIC SIGN UPADHMANIYA (visarga before प, फ, etc.)
        text = text.replace('\u1cf6', 'ः')

        # U+1CFA: VEDIC SIGN DOUBLE ANUSVARA ANTARGOMUKHA - normalize to ं
        text = text.replace('\u1cfa', 'ं')

        # Vedic anusvara variants
        # U+1CE1: VEDIC TONE ATHARVAVEDIC INDEPENDENT SVARITA - remove tone
        text = text.replace('\u1ce1', '')

        # Vedic accent/tone marks that don't affect syllable weight
        # U+1CD0-U+1CD2: Various tone marks
        text = text.replace('\u1cd0', '')  # VEDIC TONE KARSHANA
        text = text.replace('\u1cd1', '')  # VEDIC TONE SHARA
        text = text.replace('\u1cd2', '')  # VEDIC TONE PRENKHA

        # U+1CD3: VEDIC SIGN NIHSHVASA (breath mark) - remove
        text = text.replace('\u1cd3', '')

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
