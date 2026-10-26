"""Rule-based Sanskrit input screening, used when Gemini is not configured or fails.

backend/core/ai_validator.py calls rule_based_validation and returns its verdict
in the same shape as an AI verdict."""

from typing import Any, Dict


def rule_based_validation(text: str) -> Dict[str, Any]:
    """
    Fallback rule-based validation when AI is unavailable.
    Uses the same logic as chanda.py's is_valid_sanskrit_input.

    Args:
        text: Input text to validate

    Returns:
        Validation result dictionary
    """
    import re

    if not text or not text.strip():
        return {
            'is_valid': False,
            'confidence': 1.0,
            'text_type': 'gibberish',
            'reason': 'Empty input',
            'action': 'reject',
            'ai_validated': False,
        }

    text = text.strip()

    # Common English words to reject
    COMMON_ENGLISH_WORDS = {
        'i',
        'me',
        'my',
        'you',
        'your',
        'he',
        'she',
        'it',
        'we',
        'they',
        'them',
        'a',
        'an',
        'the',
        'is',
        'are',
        'was',
        'were',
        'be',
        'been',
        'being',
        'am',
        'have',
        'has',
        'had',
        'do',
        'does',
        'did',
        'will',
        'would',
        'could',
        'should',
        'hello',
        'hi',
        'hey',
        'bye',
        'goodbye',
        'thanks',
        'thank',
        'please',
        'yes',
        'no',
        'ok',
        'okay',
        'sorry',
        'welcome',
        'good',
        'bad',
        'new',
        'old',
        'test',
        'testing',
        'sample',
        'example',
        'demo',
        'input',
        'output',
        'aditya',
        'rahul',
        'priya',
        'kumar',
        'sharma',
        'singh',  # Common names
        'pratap',
        'vijay',
        'ajay',
        'sanjay',
        'amit',
        'sumit',
        'rohit',
        'mohit',  # More names
        'ram',
        'shyam',
        'gopal',
        'krishna',
        'ganesh',
        'shiva',
        'vishnu',  # Religious names (without diacritics = English)
        'name',
        'word',
        'text',
        'data',
        'file',
        'code',
        'type',
        'value',  # Tech words
    }

    # Check for Devanagari characters
    devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097f')

    # Check for IAST diacritics
    iast_diacritics = set('āīūṛṝḷḹṃḥñṅṭḍṇśṣĀĪŪṚṜḶḸṂḤÑṄṬḌṆŚṢ')
    iast_chars = sum(1 for c in text if c in iast_diacritics)

    # If text has Devanagari, it's likely valid
    if devanagari_chars > 0:
        devanagari_ratio = devanagari_chars / len(text)
        if devanagari_ratio > 0.3:
            return {
                'is_valid': True,
                'confidence': 0.8,
                'text_type': 'verse',
                'reason': 'Devanagari script detected',
                'action': 'proceed',
                'ai_validated': False,
            }

    # Pure ASCII without IAST diacritics - likely English
    if iast_chars == 0:
        text_lower = text.lower()
        words = re.findall(r'[a-z]+', text_lower)

        if words:
            english_word_count = sum(1 for word in words if word in COMMON_ENGLISH_WORDS)

            # If ANY common English word is found without diacritics, reject
            if english_word_count >= 1:
                return {
                    'is_valid': False,
                    'confidence': 0.9,
                    'text_type': 'non_sanskrit',
                    'reason': f'English text detected (no IAST diacritics). Found: {", ".join(w for w in words if w in COMMON_ENGLISH_WORDS)[:3]}',
                    'action': 'reject',
                    'ai_validated': False,
                }

            # Check vowel ratio (Sanskrit has ~0.3-0.5)
            latin_chars = sum(1 for c in text if c.isalpha() and c.isascii())
            latin_vowels = sum(1 for c in text if c.lower() in 'aeiou')

            if latin_chars > 0:
                vowel_ratio = latin_vowels / latin_chars
                if vowel_ratio < 0.15:
                    return {
                        'is_valid': False,
                        'confidence': 0.8,
                        'text_type': 'gibberish',
                        'reason': 'Invalid text - vowel ratio too low',
                        'action': 'reject',
                        'ai_validated': False,
                    }

    # Has IAST diacritics - likely valid romanized Sanskrit
    if iast_chars > 0:
        return {
            'is_valid': True,
            'confidence': 0.7,
            'text_type': 'verse',
            'reason': 'IAST transliteration detected',
            'action': 'proceed',
            'ai_validated': False,
        }

    # CRITICAL: If we reach here, text has:
    # - No Devanagari (or very little)
    # - No IAST diacritics
    # - No common English words detected
    # This is likely gibberish or romanized text without proper diacritics
    # Valid Sanskrit MUST have either Devanagari OR IAST diacritics

    # Check if it's pure ASCII letters (no numbers, no special chars)
    ascii_letters = sum(1 for c in text if c.isalpha() and c.isascii())
    total_alpha = sum(1 for c in text if c.isalpha())

    if ascii_letters > 0 and total_alpha > 0:
        # If mostly ASCII letters with no Devanagari/IAST, reject
        if ascii_letters / total_alpha > 0.8:
            return {
                'is_valid': False,
                'confidence': 0.85,
                'text_type': 'non_sanskrit',
                'reason': 'Plain ASCII text without Sanskrit script or IAST diacritics',
                'action': 'reject',
                'ai_validated': False,
            }

    # Default: uncertain, but proceed with warning (shouldn't reach here often)
    return {
        'is_valid': True,
        'confidence': 0.3,
        'text_type': 'unknown',
        'reason': 'Uncertain input - proceeding with caution',
        'action': 'warn',
        'ai_validated': False,
    }
