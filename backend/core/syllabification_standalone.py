#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Syllabification and Laghu-Guru Algorithm (Standalone Implementation)
=====================================================================

A clean, standalone implementation of Sanskrit syllabification and
Laghu-Guru (prosodic weight) determination based on Pingala's Chandas Shastra.

This module provides:
1. Sanskrit text normalization
2. Akṣara (syllable) tokenization
3. Laghu-Guru decision rules
4. Syllable to binary L-G conversion
5. Pada count and syllables per pada inference

Reference: Pingala's Chandas Shastra (500-200 BCE)

Author: Meru Coders (SIH 2025)
"""

import re
from typing import List, Tuple, Optional


###############################################################################
# STEP 1 — Sanskrit Normalizer
###############################################################################

# Characters to normalize/remove from input
DEVANAGARI_NORMALIZE = [
    ("॥", ""),      # Double danda (verse separator)
    ("।", ""),      # Single danda (line separator)
    ("ॐ", "ओम्"),   # Om symbol -> "Om" in Devanagari
    ("\n", " "),    # Newline -> space
    ("\t", " "),    # Tab -> space
    ("़", ""),      # Nukta (remove)
    ("॰", ""),      # Abbreviation sign
    ("ऽ", ""),      # Avagraha (elision marker) - remove for syllable counting
]

# Additional Vedic character normalization
VEDIC_NORMALIZE = [
    ("\u1CF2", "ः"),  # VEDIC SIGN ARDHAVISARGA -> Visarga
    ("\u1CF3", "ः"),  # VEDIC SIGN ROTATED ARDHAVISARGA -> Visarga
    ("\u1CF4", ""),   # VEDIC TONE CANDRA ABOVE -> remove
    ("\u1CF5", "ः"),  # VEDIC SIGN JIHVAMULIYA -> Visarga
    ("\u1CF6", "ः"),  # VEDIC SIGN UPADHMANIYA -> Visarga
    ("\u1CFA", "ं"),  # VEDIC SIGN DOUBLE ANUSVARA -> Anusvara
    ("\u1CD0", ""),   # VEDIC TONE KARSHANA -> remove
    ("\u1CD1", ""),   # VEDIC TONE SHARA -> remove
    ("\u1CD2", ""),   # VEDIC TONE PRENKHA -> remove
    ("\u1CD3", ""),   # VEDIC SIGN NIHSHVASA -> remove
    ("\u1CE1", ""),   # VEDIC TONE ATHARVAVEDIC INDEPENDENT SVARITA -> remove
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


###############################################################################
# STEP 2 — Akṣara (Syllable) Tokenizer
###############################################################################

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


###############################################################################
# STEP 3 — Laghu-Guru Decision Rules
###############################################################################

# Long vowels (दीर्घ स्वर) - make syllable Guru
LONG_VOWELS = ["आ", "ई", "ऊ", "ॠ", "ॡ", "ए", "ऐ", "ओ", "औ"]

# Long vowel signs (दीर्घ मात्रा)
LONG_MATRA = ["ा", "ी", "ू", "ॄ", "ॣ", "े", "ै", "ो", "ौ"]

# Short vowels (ह्रस्व स्वर) - make syllable Laghu (unless other rules apply)
SHORT_VOWELS = ["अ", "इ", "उ", "ऋ", "ऌ"]

# Short vowel signs (ह्रस्व मात्रा)
SHORT_MATRA = ["ि", "ु", "ृ", "ॢ"]


def is_guru(syllable: str, next_syllable: Optional[str] = None) -> bool:
    """
    Determine if a syllable is Guru (long/heavy).
    
    Pingala's rules for Guru:
    1. Syllable contains a long vowel (ā, ī, ū, ai, au, e, o)
    2. Syllable ends with anusvāra (ं) or visarga (ः)
    3. Syllable ends with halanta (्) - half consonant
    4. Syllable is followed by a conjunct consonant (saṃyoga rule)
    5. Last syllable of a pāda is typically Guru (anta-guru rule)
    
    Args:
        syllable: The syllable to check
        next_syllable: The following syllable (for conjunct check)
    
    Returns:
        True if the syllable is Guru, False otherwise
    """
    if not syllable:
        return False
    
    # Rule 1 — Long vowel (independent)
    for lv in LONG_VOWELS:
        if lv in syllable:
            return True
    
    # Rule 1b — Long vowel sign (dependent mātrā)
    for lm in LONG_MATRA:
        if lm in syllable:
            return True
    
    # Rule 2 — Ends with anusvāra, visarga, or chandrabindu
    if syllable.endswith(ANUSVARA) or syllable.endswith(VISARGA) or syllable.endswith(CHANDRABINDU):
        return True
    
    # Rule 3 — Ends with halanta (संयुक्त व्यञ्जन - conjunct)
    if syllable.endswith(HALANTA):
        return True
    
    # Rule 4 — Followed by conjunct consonant (saṃyoga)
    # If next syllable starts with conjunct (consonant + halanta + consonant),
    # current syllable becomes Guru
    if next_syllable:
        # Check if next syllable starts with consonant cluster
        # A conjunct is indicated by halanta in the beginning part
        if HALANTA in next_syllable[:3]:  # Check first few chars
            return True
    
    return False


def is_laghu(syllable: str, next_syllable: Optional[str] = None) -> bool:
    """
    Determine if a syllable is Laghu (short/light).
    
    A syllable is Laghu if:
    - It has a short vowel AND
    - None of the Guru rules apply
    
    Args:
        syllable: The syllable to check
        next_syllable: The following syllable (for conjunct check)
    
    Returns:
        True if the syllable is Laghu, False otherwise
    """
    return not is_guru(syllable, next_syllable)


###############################################################################
# STEP 4 — Convert Syllables to Binary L-G Sequence
###############################################################################

def syllables_to_lg(syllables: List[str], apply_anta_guru: bool = True) -> List[int]:
    """
    Convert syllables to binary Laghu-Guru sequence.
    
    Args:
        syllables: List of syllable strings
        apply_anta_guru: If True, treat the last syllable as Guru (traditional rule)
    
    Returns:
        List of 0s (Laghu) and 1s (Guru)
    """
    if not syllables:
        return []
    
    binary = []
    
    for i, syl in enumerate(syllables):
        # Get next syllable for conjunct check
        next_syl = syllables[i + 1] if i + 1 < len(syllables) else None
        
        # Check if last syllable (for anta-guru rule)
        is_last = (i == len(syllables) - 1)
        
        if is_guru(syl, next_syl):
            binary.append(1)  # Guru
        elif apply_anta_guru and is_last:
            binary.append(1)  # Anta-guru rule: last syllable is Guru
        else:
            binary.append(0)  # Laghu
    
    return binary


def syllables_to_lg_string(syllables: List[str], apply_anta_guru: bool = True) -> str:
    """
    Convert syllables to L-G string representation.
    
    Args:
        syllables: List of syllable strings
        apply_anta_guru: If True, treat the last syllable as Guru
    
    Returns:
        String of 'L's and 'G's (e.g., "LGLGLGGL")
    """
    binary = syllables_to_lg(syllables, apply_anta_guru)
    return ''.join('G' if b else 'L' for b in binary)


def syllables_to_lg_devanagari(syllables: List[str], apply_anta_guru: bool = True) -> str:
    """
    Convert syllables to Devanagari L-G representation.
    
    Args:
        syllables: List of syllable strings
        apply_anta_guru: If True, treat the last syllable as Guru
    
    Returns:
        String of 'ल's and 'ग's (e.g., "लगलगलगगल")
    """
    binary = syllables_to_lg(syllables, apply_anta_guru)
    return ''.join('ग' if b else 'ल' for b in binary)


###############################################################################
# STEP 5 — Infer Pada Count and Syllables Per Pada
###############################################################################

def guess_padas(text: str, syllables: List[str]) -> Tuple[int, List[int]]:
    """
    Infer the pada (foot) count and syllables per pada from text structure.
    
    Heuristics:
    1. If text has explicit dandas (।/॥), split by them
    2. If newlines present, treat each line as potential pada
    3. Otherwise, assume 4 pādas (most common in śloka meters)
    4. Divide syllables as equally as possible
    
    Args:
        text: Original input text (before normalization)
        syllables: List of syllables from the normalized text
    
    Returns:
        Tuple of (pada_count, list of syllables_per_pada)
    """
    total_syllables = len(syllables)
    
    if total_syllables == 0:
        return 0, []
    
    # Method 1: Check for dandas (verse separators)
    if "।" in text or "॥" in text:
        # Split by any danda
        parts = re.split(r"[।॥]+", text)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) > 1:
            pada_count = len(parts)
            # Estimate syllables per pada
            # We can't directly map parts to syllables perfectly,
            # so we use approximate equal distribution
            base = total_syllables // pada_count
            remainder = total_syllables % pada_count
            
            # Distribute remainder to first padas
            spp = [base + (1 if i < remainder else 0) for i in range(pada_count)]
            return pada_count, spp
    
    # Method 2: Check for newlines (each line might be a pada)
    original_text = text  # Use text before full normalization for line detection
    if "\n" in original_text:
        lines = [l.strip() for l in original_text.split("\n") if l.strip()]
        if len(lines) > 1:
            pada_count = len(lines)
            base = total_syllables // pada_count
            remainder = total_syllables % pada_count
            spp = [base + (1 if i < remainder else 0) for i in range(pada_count)]
            return pada_count, spp
    
    # Method 3: Use syllable count heuristics for common meters
    # Common Vedic/Classical meter structures:
    # - Gayatri: 24 syllables = 3 padas × 8
    # - Anushtubh: 32 syllables = 4 padas × 8
    # - Trishtubh: 44 syllables = 4 padas × 11
    # - Jagati: 48 syllables = 4 padas × 12
    
    meter_structures = {
        24: (3, [8, 8, 8]),           # Gayatri
        28: (4, [7, 7, 7, 7]),        # Ushnik
        32: (4, [8, 8, 8, 8]),        # Anushtubh
        36: (4, [9, 9, 9, 9]),        # Brihati
        40: (5, [8, 8, 8, 8, 8]),     # Pankti
        44: (4, [11, 11, 11, 11]),    # Trishtubh
        48: (4, [12, 12, 12, 12]),    # Jagati
    }
    
    # Check for exact match first
    if total_syllables in meter_structures:
        return meter_structures[total_syllables]
    
    # Check for close match (±2 syllables)
    for count, (padas, spp) in meter_structures.items():
        if abs(total_syllables - count) <= 2:
            # Adjust distribution
            diff = total_syllables - count
            adjusted_spp = spp.copy()
            for i in range(abs(diff)):
                idx = i % len(adjusted_spp)
                adjusted_spp[idx] += 1 if diff > 0 else -1
            return padas, adjusted_spp
    
    # Method 4: Default to 4 padas (most common structure)
    pada_count = 4
    base = total_syllables // pada_count
    remainder = total_syllables % pada_count
    spp = [base + (1 if i < remainder else 0) for i in range(pada_count)]
    
    return pada_count, spp


###############################################################################
# COMPLETE ANALYSIS FUNCTION
###############################################################################

def analyze_verse(text: str, apply_anta_guru: bool = True) -> dict:
    """
    Complete analysis of a Sanskrit verse.
    
    Performs:
    1. Text normalization
    2. Syllable tokenization
    3. L-G determination
    4. Pada structure inference
    5. Matra (weight) counting
    
    Args:
        text: Input Sanskrit verse in Devanagari
        apply_anta_guru: If True, apply anta-guru rule for last syllable
    
    Returns:
        Dictionary with complete analysis results
    """
    # Store original for pada detection
    original_text = text
    
    # Step 1: Normalize
    normalized = normalize_sanskrit(text)
    
    # Step 2: Syllabify
    syllables = split_syllables(normalized)
    
    # Step 3: Get L-G pattern
    lg_binary = syllables_to_lg(syllables, apply_anta_guru)
    lg_string = syllables_to_lg_string(syllables, apply_anta_guru)
    lg_devanagari = syllables_to_lg_devanagari(syllables, apply_anta_guru)
    
    # Step 4: Infer pada structure
    pada_count, syllables_per_pada = guess_padas(original_text, syllables)
    
    # Step 5: Count matras (Laghu = 1, Guru = 2)
    matra_count = sum(2 if b else 1 for b in lg_binary)
    
    # Calculate gana pattern (groups of 3)
    gana_map = {
        'LGG': 'य', 'GLG': 'र', 'GGL': 'त', 'LLL': 'न',
        'GLL': 'भ', 'LGL': 'ज', 'LLG': 'स', 'GGG': 'म'
    }
    gana_pattern = ""
    for i in range(0, len(lg_string), 3):
        group = lg_string[i:i+3]
        if len(group) == 3:
            gana_pattern += gana_map.get(group, '?')
        else:
            gana_pattern += group  # Remainder
    
    return {
        "original": text,
        "normalized": normalized,
        "syllables": syllables,
        "syllable_count": len(syllables),
        "lg_binary": lg_binary,
        "lg_string": lg_string,
        "lg_devanagari": lg_devanagari,
        "gana_pattern": gana_pattern,
        "matra_count": matra_count,
        "pada_count": pada_count,
        "syllables_per_pada": syllables_per_pada,
    }


###############################################################################
# UTILITY FUNCTIONS
###############################################################################

def compare_patterns(pattern1: str, pattern2: str) -> float:
    """
    Compare two L-G patterns and return similarity score (0.0 to 1.0).
    
    Args:
        pattern1: First L-G pattern string
        pattern2: Second L-G pattern string
    
    Returns:
        Similarity score (1.0 = identical)
    """
    if not pattern1 or not pattern2:
        return 0.0
    
    if len(pattern1) != len(pattern2):
        # Different lengths - use normalized comparison
        min_len = min(len(pattern1), len(pattern2))
        max_len = max(len(pattern1), len(pattern2))
        matches = sum(1 for a, b in zip(pattern1[:min_len], pattern2[:min_len]) if a == b)
        return matches / max_len
    
    # Same length - direct comparison
    matches = sum(1 for a, b in zip(pattern1, pattern2) if a == b)
    return matches / len(pattern1)


def split_into_padas(lg_pattern: str, syllables_per_pada: List[int]) -> List[str]:
    """
    Split an L-G pattern into pada-wise patterns.
    
    Args:
        lg_pattern: Full L-G pattern string
        syllables_per_pada: List of syllable counts per pada
    
    Returns:
        List of L-G patterns for each pada
    """
    padas = []
    start = 0
    
    for count in syllables_per_pada:
        pada = lg_pattern[start:start + count]
        padas.append(pada)
        start += count
    
    return padas


###############################################################################
# MAIN - Example Usage
###############################################################################

if __name__ == "__main__":
    # Test with famous shlokas
    test_verses = [
        # Bhagavad Gita 1.1 - Anushtubh (4×8 = 32 syllables)
        "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
        
        # Gayatri Mantra (3×8 = 24 syllables)
        "तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि",
        
        # Another line from BG
        "वसुदेवसुतं देवं कंसचाणूरमर्दनम्",
        
        # Full shloka with danda
        "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः। मामकाः पाण्डवाश्चैव किमकुर्वत संजय॥",
    ]
    
    print("=" * 70)
    print("SANSKRIT SYLLABIFICATION AND L-G ANALYSIS")
    print("Standalone Implementation for SIH 2025")
    print("=" * 70)
    
    for verse in test_verses:
        print(f"\n{'─' * 70}")
        print(f"INPUT: {verse}")
        print(f"{'─' * 70}")
        
        result = analyze_verse(verse)
        
        print(f"Syllables ({result['syllable_count']}): {' | '.join(result['syllables'])}")
        print(f"L-G Pattern: {result['lg_string']}")
        print(f"L-G (देवनागरी): {result['lg_devanagari']}")
        print(f"Gaṇa Pattern: {result['gana_pattern']}")
        print(f"Mātrā Count: {result['matra_count']}")
        print(f"Pada Count: {result['pada_count']}")
        print(f"Syllables/Pada: {result['syllables_per_pada']}")
    
    print(f"\n{'=' * 70}")
    print("ANALYSIS COMPLETE")
    print("=" * 70)
