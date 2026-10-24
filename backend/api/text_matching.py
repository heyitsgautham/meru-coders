"""Text normalization and similarity helpers for verse lookup."""

import unicodedata

import Levenshtein

# Vedic accent marks: svarita, anudatta and the Vedic Extensions block
_VEDIC_MARKS = "॒॑॓॔᳐᳑᳒᳓᳔᳕᳖᳗᳘᳙᳜᳝᳞᳟᳚᳛᳠᳡"
_ACCENT_TABLE = str.maketrans("", "", _VEDIC_MARKS)
_PUNCTUATION_TABLE = str.maketrans({"।": " ", "॥": " ", ",": " ", ".": " ", ":": " "})


def normalize_sanskrit_text(text):
    """
    Normalize Sanskrit text for comparison.

    Applies NFC, strips Vedic accent marks, turns danda and common
    punctuation into spaces, collapses whitespace and lowercases the result.
    Returns "" for empty or None input.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_ACCENT_TABLE).translate(_PUNCTUATION_TABLE)
    return " ".join(text.split()).lower()


def calculate_similarity(text1, text2):
    """Return the Levenshtein ratio of two strings, from 0.0 to 1.0 (identical)."""
    return Levenshtein.ratio(text1, text2)
