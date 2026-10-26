"""Steps 1 and 2 of syllabification_standalone.py: normalise Sanskrit text and split it into aksharas."""

import re
from typing import List

# Characters to normalize/remove from input
DEVANAGARI_NORMALIZE = [
    ("॥", ""),  # Double danda (verse separator)
    ("।", ""),  # Single danda (line separator)
    ("ॐ", "ओम्"),  # Om symbol -> "Om" in Devanagari
    ("\n", " "),  # Newline -> space
    ("\t", " "),  # Tab -> space
    ("़", ""),  # Nukta (remove)
    ("॰", ""),  # Abbreviation sign
    ("ऽ", ""),  # Avagraha (elision marker) - remove for syllable counting
]


# Additional Vedic character normalization
VEDIC_NORMALIZE = [
    ("\u1cf2", "ः"),  # VEDIC SIGN ARDHAVISARGA -> Visarga
    ("\u1cf3", "ः"),  # VEDIC SIGN ROTATED ARDHAVISARGA -> Visarga
    ("\u1cf4", ""),  # VEDIC TONE CANDRA ABOVE -> remove
    ("\u1cf5", "ः"),  # VEDIC SIGN JIHVAMULIYA -> Visarga
    ("\u1cf6", "ः"),  # VEDIC SIGN UPADHMANIYA -> Visarga
    ("\u1cfa", "ं"),  # VEDIC SIGN DOUBLE ANUSVARA -> Anusvara
    ("\u1cd0", ""),  # VEDIC TONE KARSHANA -> remove
    ("\u1cd1", ""),  # VEDIC TONE SHARA -> remove
    ("\u1cd2", ""),  # VEDIC TONE PRENKHA -> remove
    ("\u1cd3", ""),  # VEDIC SIGN NIHSHVASA -> remove
    ("\u1ce1", ""),  # VEDIC TONE ATHARVAVEDIC INDEPENDENT SVARITA -> remove
]


def normalize_sanskrit(text: str) -> str:
    """
    Normalize Sanskrit text by removing punctuation, expanding symbols,
    and standardizing whitespace.

    Args:
        text: Input Sanskrit text (Devanagari or IAST)

    Returns:
        Normalized text string
    """
    if not text:
        return ""

    text = text.strip()

    # Apply standard normalizations
    for old, new in DEVANAGARI_NORMALIZE:
        text = text.replace(old, new)

    # Apply Vedic character normalizations
    for old, new in VEDIC_NORMALIZE:
        text = text.replace(old, new)

    # Normalize multiple spaces to single space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# Independent vowels (स्वर)
VOWELS = "अआइईउऊऋॠऌॡएऐओऔ"


# Dependent vowel signs (मात्रा)
MATRA = "ािीुूृॄॢॣेैोौ"


# Anusvara (अनुस्वार)
ANUSVARA = "ं"


# Visarga (विसर्ग)
VISARGA = "ः"


# Halanta/Virama (हलन्त) - indicates no vowel after consonant
HALANTA = "्"


# Chandrabindu (चन्द्रबिन्दु) - nasalization
CHANDRABINDU = "ँ"


# All consonants (व्यञ्जन)
CONSONANTS = "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह"


# Conjunct consonant markers
NUKTA = "़"


def split_syllables(text: str) -> List[str]:
    """
    Split Sanskrit text into syllables (akṣaras).

    We treat a syllable as:
    [consonant cluster] + vowel + (anusvāra/visarga optional)

    A new syllable starts when:
    - A new independent vowel appears
    - A vowel sign (mātrā) appears after a consonant/cluster

    Args:
        text: Normalized Sanskrit text in Devanagari

    Returns:
        List of syllable strings
    """
    syllables = []
    current = ""

    i = 0
    while i < len(text):
        ch = text[i]

        # Skip spaces - they're word boundaries, not syllable boundaries
        if ch == " ":
            if current:
                syllables.append(current)
                current = ""
            i += 1
            continue

        # Check if this character ends a syllable
        if ch in VOWELS:
            # Independent vowel - starts a new syllable
            if current:
                # If current ends with halanta, the vowel joins it
                if current.endswith(HALANTA):
                    current = current[:-1] + ch  # Replace halanta with vowel
                    syllables.append(current)
                    current = ""
                else:
                    # Current syllable is complete, start new one
                    syllables.append(current)
                    current = ch
            else:
                current = ch

            # Check for anusvara/visarga right after
            if i + 1 < len(text) and text[i + 1] in (ANUSVARA + VISARGA + CHANDRABINDU):
                current += text[i + 1]
                syllables.append(current)
                current = ""
                i += 1
            elif current:
                syllables.append(current)
                current = ""

        elif ch in MATRA:
            # Dependent vowel sign - ends current syllable
            current += ch

            # Check for anusvara/visarga right after
            if i + 1 < len(text) and text[i + 1] in (ANUSVARA + VISARGA + CHANDRABINDU):
                current += text[i + 1]
                i += 1

            syllables.append(current)
            current = ""

        elif ch in (ANUSVARA + VISARGA + CHANDRABINDU):
            # If these appear without a vowel/matra before, attach to current
            current += ch
            # This typically ends the syllable
            if current and not current.endswith(HALANTA):
                syllables.append(current)
                current = ""

        elif ch == HALANTA:
            # Halanta - consonant continues to next
            current += ch

        elif ch in CONSONANTS:
            # Consonant - check if starting new syllable
            if current and not current.endswith(HALANTA):
                # Previous syllable is complete (ended with vowel sound)
                # The inherent 'a' makes the previous syllable complete
                syllables.append(current)
                current = ch
            else:
                # Continue building current cluster
                current += ch

        else:
            # Other characters (punctuation, etc.) - skip
            if current:
                syllables.append(current)
                current = ""

        i += 1

    # Handle remaining content
    if current:
        syllables.append(current)

    # Clean up - remove empty or whitespace-only syllables
    syllables = [s for s in syllables if s.strip()]

    return syllables


def split_syllables_simple(text: str) -> List[str]:
    """
    Simplified syllable splitter - original algorithm from specification.

    This is a more straightforward implementation that treats a syllable as:
    [consonant cluster] + vowel + (anusvāra/visarga optional)

    Args:
        text: Normalized Sanskrit text in Devanagari

    Returns:
        List of syllable strings
    """
    syllables = []
    current = ""

    for ch in text:
        if ch == " ":
            if current:
                syllables.append(current)
                current = ""
            continue

        if ch in VOWELS or ch in MATRA:
            current += ch
            syllables.append(current)
            current = ""
        else:
            current += ch

    if current:
        syllables.append(current)

    # Clean empty/garbage
    syllables = [s for s in syllables if s.strip()]
    return syllables
