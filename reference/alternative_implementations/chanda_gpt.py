# chanda_improved.py
"""
Improved chandas (Vedic metre) identifier module.

This file provides a robust, self-contained implementation for:
- Normalizing Sanskrit text (Devanagari focused)
- Tokenizing into syllables (heuristic Devanagari syllabifier)
- Computing Laghu(Guru) (L/G) patterns and matra counts
- Inferring pada structure and matching against VEDIC_METERS
- Exposing a stable API function `identify_from_text(text, variant='strict')`

NOTES:
- This implementation is heuristic: Sanskrit prosody can be subtle and requires
  more advanced linguistic processing for 100% accuracy. Use this as a
  production-grade starting point and iterate using your gold dataset.
- We intentionally do not call external libraries to keep the file portable.

Functions (stable API):
- identify_from_text(text: str, variant: str='strict') -> dict

Return value: a dict with keys:
- text, script, normalized, syllables (list), syllable_count (int), matra_count (int),
  lg_pattern (list of 'L'/'G'), padas (list of lists of syllables),
  inferred_pada_structure (list of ints), identified_meter (str or None),
  confidence (0..1), notes (list)

Keep function name and return type stable for compatibility with existing code.

"""

import re
from typing import List, Tuple, Dict, Any

# -----------------------------
# Canonical VEDIC_METERS mapping
# -----------------------------
VEDIC_METERS = {
    "Gayatri": {"pada_structure": [8, 8, 8], "syllables": 24, "description": "3x8"},
    "Ushnih": {"pada_structure": [8, 8, 12], "syllables": 28, "description": "8+8+12"},
    "Anushtubh": {"pada_structure": [8, 8, 8, 8], "syllables": 32, "description": "4x8"},
    "Brihati": {"pada_structure": [8, 8, 12, 8], "syllables": 36, "description": "8+8+12+8"},
    "Pankti": {"pada_structure": [8, 8, 8, 8, 8], "syllables": 40, "description": "5x8"},
    "Trishtubh": {"pada_structure": [11, 11, 11, 11], "syllables": 44, "description": "4x11"},
    "Jagati": {"pada_structure": [12, 12, 12, 12], "syllables": 48, "description": "4x12"},
    # Variants
    "Nicrt_Gayatri": {"pada_structure": [7, 7, 7], "syllables": 21, "description": "3x7 (nicrt)"},
    "Bhurik_Gayatri": {"pada_structure": [9, 9, 9], "syllables": 27, "description": "3x9 (bhurik)"},
    "Nicrt_Trishtubh": {"pada_structure": [10, 10, 10, 10], "syllables": 40, "description": "4x10 (nicrt)"},
    "Virat_Trishtubh": {"pada_structure": [12, 12, 12, 12], "syllables": 48, "description": "4x12 (virat)"},
    "Nicrt_Jagati": {"pada_structure": [11, 11, 11, 11], "syllables": 44, "description": "4x11 (nicrt jagati)"},
}

# -----------------------------
# Devanagari character classes
# -----------------------------
# Consonants (base), vowels (independent), vowel signs (matras), virama
DEVANAGARI_CONSONANTS = r"कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळक्षज्ञ"
DEVANAGARI_VOWELS = r"अआइईउऊऋॠऌॡएऐओऔ"
DEVANAGARI_MATRA = r"ािीुूृॄॢॣेैोौँः्"  # includes anusvara, visarga, virama
VIRAMA = '्'

# For quick matching
RE_DEVANAGARI = re.compile(r"[\u0900-\u097F]+")
RE_DEVANAGARI_CHAR = re.compile(r"[\u0900-\u097F]")

# Matra classification: short vowels (laghu) vs long (guru)
# In classical matra counting, short vowels: अ(implicit), इ, उ; long: आ, ई, ऊ, ए, ओ, ऐ, औ.
SHORT_VOWELS = set(["अ", "इ", "उ"])  # implicit 'a' handled specially
LONG_VOWELS = set(["आ", "ई", "ऊ", "ए", "ओ", "ऐ", "औ"])
# Also letters like ऋ often count as long in some traditions; treat as long for safety
LONG_EXTRA = set(["ऋ", "ॠ"])

# Vowel signs (matras) mapping to short/long categories (Devanagari signs)
SHORT_MATRAS = set(["", "ि", "ु"])  # '' for inherent vowel where no matra shown
LONG_MATRAS = set(["ा", "ी", "ू", "े", "ै", "ो", "ौ", "ृ"])  # include more

# -----------------------------
# Utilities
# -----------------------------

def detect_script(text: str) -> str:
    """Detect if text is Devanagari, transliteration (IAST), or other.

    Returns: 'devanagari' | 'iast' | 'other'
    """
    if RE_DEVANAGARI.search(text):
        return 'devanagari'
    # simple heuristic: presence of latin letters with diacritics suggests IAST
    if re.search(r"[a-zA-Z]", text):
        return 'iast'
    return 'other'


def normalize_text(text: str) -> str:
    """Normalize input text:
    - strip whitespace
    - remove zero-width joiners and control chars
    - unify punctuation
    - preserve Devanagari letters
    """
    if text is None:
        return ""
    # remove invisible control characters and zero width joiners
    text = re.sub(r"[\u200B-\u200F\uFEFF\u202A-\u202E]", "", text)
    # normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # unify punctuation: replace brackets with spaces
    text = re.sub(r"[\[\]\{\}\(\)<>\|]", " ", text)
    return text


# -----------------------------
# Syllabification (Devanagari-focused heuristic)
# -----------------------------

def devanagari_syllabify(text: str) -> List[str]:
    """
    Heuristic syllabifier for Devanagari text.

    Algorithm (approximate):
    - Iterate over characters; form syllables as (consonant cluster + optional matra/diacritics) or standalone vowels.
    - Treat virama (्) as conjunct marker (attach consonants together).
    - Include anusvara (ं), visarga (ः) as part of the syllable.

    Returns list of syllable strings.
    """
    text = normalize_text(text)
    chars = list(text)
    syllables = []
    buf = ""

    i = 0
    while i < len(chars):
        ch = chars[i]
        if not RE_DEVANAGARI_CHAR.match(ch):
            # flush buffer and treat non-deva as separator
            if buf:
                syllables.append(buf)
                buf = ""
            i += 1
            continue

        buf += ch

        # if ch is virama, then next consonant attaches -> continue
        if ch == VIRAMA:
            # keep conjuncts together: consume next char into buffer if present
            i += 1
            if i < len(chars):
                buf += chars[i]
                i += 1
            continue

        # check if next char is a matra or anusvara/visarga
        nxt = chars[i+1] if i+1 < len(chars) else None
        if nxt and (nxt in DEVANAGARI_MATRA or nxt in ['ं', 'ः']):
            buf += nxt
            i += 2
            syllables.append(buf)
            buf = ""
            continue

        # If ch itself is a vowel sign or independent vowel, close syllable
        if ch in DEVANAGARI_VOWELS or ch in DEVANAGARI_MATRA:
            syllables.append(buf)
            buf = ""
            i += 1
            continue

        # If next char is a consonant but there's no virama, that means implicit vowel completes syllable
        if nxt and RE_DEVANAGARI_CHAR.match(nxt) and nxt not in DEVANAGARI_MATRA and nxt != VIRAMA:
            # implicit vowel ends current syllable
            syllables.append(buf)
            buf = ""
            i += 1
            continue

        # otherwise advance
        i += 1

    if buf:
        syllables.append(buf)
    # filter out empty
    syllables = [s for s in syllables if s.strip()]
    return syllables


def syllable_to_matra(syll: str) -> int:
    """Estimate matra (weight) for a syllable: 1 = laghu, 2 = guru.

    Heuristics:
    - If syll includes a long matra or independent long vowel, count as 2.
    - If syll ends with virama (dead consonant cluster) -> guru (2).
    - If syll ends with anusvara/visarga -> guru (2) in many traditions.
    - Otherwise 1 (laghu).

    This is a heuristic. Some classical rules (e.g., optional cases) are not covered.
    """
    # quick checks
    if not syll or not RE_DEVANAGARI_CHAR.search(syll):
        return 0

    # contains virama -> closed syllable -> guru
    if VIRAMA in syll:
        return 2

    # ends with anusvara or visarga
    if syll.endswith('ं') or syll.endswith('ः'):
        return 2

    # check independent vowel
    for ch in syll:
        if ch in LONG_EXTRA:
            return 2

    # check matra characters
    for m in LONG_MATRAS:
        if m in syll:
            return 2
    # short matra explicitly
    for m in SHORT_MATRAS:
        if m in syll:
            # short matra -> laghu (1)
            return 1

    # if syll contains an independent short vowel like इ उ etc -> laghu
    for ch in syll:
        if ch in SHORT_VOWELS:
            return 1

    # fallback: treat as laghu
    return 1


def compute_lg_pattern(syllables: List[str]) -> Tuple[List[str], int]:
    """Compute Laghu/Guru pattern and total matra count.

    Returns (lg_pattern, matra_total)
    lg_pattern is list of 'L' or 'G' corresponding to syllables.
    """
    pattern = []
    total = 0
    for s in syllables:
        m = syllable_to_matra(s)
        total += m
        pattern.append('G' if m == 2 else 'L')
    return pattern, total


# -----------------------------
# Meter inference utilities
# -----------------------------

def split_into_padas(syllables: List[str], target_pada_counts: List[int] = None) -> List[List[str]]:
    """Split syllables into padas given a target pattern or heuristically.

    If target_pada_counts is provided, split accordingly. Otherwise, attempt
    common splits: 3 padas (Gayatri), 4 padas (Anushtubh/Trishtubh/Jagati),
    5 padas (Pankti), or fallback to equal division.
    """
    n = len(syllables)
    if target_pada_counts:
        # validate sum
        if sum(target_pada_counts) != n:
            return []
        out = []
        idx = 0
        for cnt in target_pada_counts:
            out.append(syllables[idx:idx+cnt])
            idx += cnt
        return out

    # heuristic attempts
    # try exact matches from known meters
    for name, info in VEDIC_METERS.items():
        if info['syllables'] == n:
            return split_into_padas(syllables, info['pada_structure'])

    # fallback: try 4 padas equal-ish, then 3, then 5
    if n % 4 == 0:
        size = n // 4
        return [syllables[i*size:(i+1)*size] for i in range(4)]
    if n % 3 == 0:
        size = n // 3
        return [syllables[i*size:(i+1)*size] for i in range(3)]
    if n % 5 == 0:
        size = n // 5
        return [syllables[i*size:(i+1)*size] for i in range(5)]

    # last resort: split into two halves
    half = n // 2
    return [syllables[:half], syllables[half:]]


def match_meter_by_padas(padas: List[List[str]]) -> Tuple[str, float]:
    """Try to match pada structure to known meters.

    Returns (meter_name_or_None, confidence 0..1)
    Confidence is heuristic based on exactness of the match.
    """
    lengths = [len(p) for p in padas]
    for name, info in VEDIC_METERS.items():
        if info['pada_structure'] == lengths:
            return name, 0.98
    # if total syllable count matches unique meter
    total = sum(lengths)
    candidates = [ (n, info) for n,info in VEDIC_METERS.items() if info['syllables']==total ]
    if len(candidates) == 1:
        return candidates[0][0], 0.85
    if len(candidates) > 1:
        # ambiguous: prefer exact pada-structure if possible
        return candidates[0][0], 0.6
    return None, 0.0


# -----------------------------
# Public API
# -----------------------------

def identify_from_text(text: str, variant: str = 'strict') -> Dict[str, Any]:
    """
    Identify chandas (Vedic metre) from raw input text.

    Parameters:
    - text: input Sanskrit text (Devanagari preferred). Can be multi-line.
    - variant: 'strict'|'lenient'|'experimental'
        * 'strict': conservative checks, reject if suspicious patterns found
        * 'lenient': allow some non-Devanagari heuristics and approximate
        * 'experimental': run extra heuristics and return multiple candidates

    Returns dict with fields described at top of file.
    """
    notes = []
    orig_text = text
    if not text or not text.strip():
        return {
            'text': orig_text,
            'script': None,
            'normalized': '',
            'syllables': [],
            'syllable_count': 0,
            'matra_count': 0,
            'lg_pattern': [],
            'padas': [],
            'inferred_pada_structure': [],
            'identified_meter': None,
            'confidence': 0.0,
            'notes': ['empty input']
        }

    script = detect_script(text)
    normalized = normalize_text(text)

    # If strict and not Devanagari, reject quickly
    if variant == 'strict' and script != 'devanagari':
        notes.append('strict mode: non-Devanagari input')
        # but still attempt to extract Devanagari substrings
        devas = RE_DEVANAGARI.findall(text)
        if devas:
            normalized = ' '.join(devas)
            notes.append('extracted Devanagari substrings')
        else:
            return {
                'text': orig_text,
                'script': script,
                'normalized': normalized,
                'syllables': [],
                'syllable_count': 0,
                'matra_count': 0,
                'lg_pattern': [],
                'padas': [],
                'inferred_pada_structure': [],
                'identified_meter': None,
                'confidence': 0.0,
                'notes': notes
            }

    # Basic injection detection: if input contains braces or 'pretend' patterns, flag
    if re.search(r"\{.*\}|pretend|ignore all|override|respond in json|respond in json", normalized, re.IGNORECASE):
        notes.append('rejected input: contains meta-instructions or injection-like tokens')
        return {
            'text': orig_text,
            'script': script,
            'normalized': normalized,
            'syllables': [],
            'syllable_count': 0,
            'matra_count': 0,
            'lg_pattern': [],
            'padas': [],
            'inferred_pada_structure': [],
            'identified_meter': None,
            'confidence': 0.0,
            'notes': notes
        }

    # Syllabify
    sylls = devanagari_syllabify(normalized)
    lg_pattern, matra_total = compute_lg_pattern(sylls)

    # Split into padas heuristically
    padas = split_into_padas(sylls)
    inferred_pada_len = [len(p) for p in padas]

    # Match to known meters
    meter, conf = match_meter_by_padas(padas)

    # Simple confidence adjustments
    if meter is None and variant == 'lenient':
        # try approximate matching by total syllables
        total = len(sylls)
        candidates = [name for name,info in VEDIC_METERS.items() if info['syllables']==total]
        if candidates:
            meter = candidates[0]
            conf = 0.5
            notes.append('lenient mode: matched by total syllable count')

    # Additional experimental scoring: match LG pattern lengths with expected patterns (optional)
    # For now, keep confidence as-is

    result = {
        'text': orig_text,
        'script': script,
        'normalized': normalized,
        'syllables': sylls,
        'syllable_count': len(sylls),
        'matra_count': matra_total,
        'lg_pattern': lg_pattern,
        'padas': padas,
        'inferred_pada_structure': inferred_pada_len,
        'identified_meter': meter,
        'confidence': float(conf),
        'notes': notes
    }
    return result


# -----------------------------
# Quick test harness (run as script)
# -----------------------------
if __name__ == '__main__':
    examples = [
        "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
        "अग्निमीळे पुरोहितं",
        "कस्तूरीतिलकं ललाटपट्टे",
        "रामो विग्रहवान् स्द्र्मः",
    ]
    for ex in examples:
        print('\nINPUT:', ex)
        out = identify_from_text(ex, variant='lenient')
        for k in ['identified_meter','syllable_count','matra_count','inferred_pada_structure','confidence']:
            print(f"{k}: {out.get(k)}")
        # print L/G pattern truncated
        print('LG (first 40):', ''.join(out.get('lg_pattern')[:40]))
