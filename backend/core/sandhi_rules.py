"""
Enhanced reverse-sandhi candidate generator for Sanskrit text.

Adapted from Chand-Identifier project for integration with Chandojñānam.
This module provides automatic sandhi resolution to handle merged Sanskrit text.

Key Features:
- Reverse vowel sandhi (savarṇa-dīrgha, guṇa, vṛddhi)
- Visarga transformations
- Anusvara expansions (context-aware nasal mapping)
- Consonant cluster splitting
- Lexicon-based candidate scoring

Usage:
    from backend.core.sandhi_rules import gen_candidates

    line = "कर्मण्येवाधिकारस्ते"
    candidates = gen_candidates(line, k=5, lexicon_path="data/sandhi_lexicon.txt")

    for cand in candidates:
        print(f"{cand['score']:.2f}: {cand['cand']}")

Functions:
    gen_candidates(line, k=8, lexicon_path=None, allow_aggressive=False)
        Returns list of dicts: {'cand': text, 'score': float, 'rules': [str]}

Author: Adapted from Chand-Identifier (https://github.com/...)
License: Compatible with Chandojñānam project
Date: November 20, 2025
"""

import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple


def normalize_sandhi_text(text: str) -> str:
    """
    Normalize text for sandhi processing.

    - Unicode NFC normalize
    - Replace dandas (।, ॥) with spaces
    - Keep Devanagari combining marks and special signs
    - Replace other punctuation with space
    - Collapse multiple whitespace to single space
    """
    if text is None:
        return ""

    # Unicode NFC normalization
    text = unicodedata.normalize('NFC', text)

    # Replace danda characters with space (preserve pada boundaries)
    text = re.sub(r'[॥।]+', ' ', text)

    # Ensure OM (ॐ) is spaced
    text = re.sub(r'\u0950', ' \u0950 ', text)

    # Replace common punctuation with space
    punct_re = re.compile(r'[\u2000-\u206F\u2E00-\u2E7F\.,;:"\?\!\(\)\[\]\{\}—\-–/\\\|<>@#\$%\^&\*\+=_`~]')
    text = punct_re.sub(' ', text)

    # Remove ASCII control chars
    text = ''.join(ch for ch in text if ord(ch) >= 32)

    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def load_lexicon(path: str = "data/sandhi_lexicon.txt") -> set:
    """Load lexicon from file (one token per line)."""
    p = Path(path)
    if not p.exists():
        return set()
    with p.open("r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


# Default small lexicon (high-frequency Sanskrit words)
DEFAULT_LEXICON = {
    'राम',
    'रामः',
    'रामो',
    'सीता',
    'सीतायै',
    'सीताम्',
    'कृष्ण',
    'कृष्णः',
    'गुरु',
    'शिष्य',
    'विद्या',
    'धर्म',
    'धर्मः',
    'सत्यम्',
    'अहम्',
    'पाण्डव',
    'हनुमान',
    'लङ्का',
    'अर्जुन',
    'भीम',
    'गद',
    'वेद',
    'ज्ञान',
    'शिव',
    'शिवः',
    'लोका',
    'सुख',
    'बलवान्',
    'अस्ति',
    'गच्छति',
    'व्रज',
    'गगन',
    'सागर',
    'नमः',
    'भगवान्',
    'देव',
    'देवी',
}


# Core reverse-sandhi transformation rules
REVERSE_RULES = [
    # Vowel sandhi patterns
    (r'ा', r' आ ', 'savarṇa-dīrgha (ā split)'),
    (r'े', r' ए ', 'guṇa (e split)'),
    (r'ो', r' ओ ', 'guṇa (o split)'),
    (r'ै', r' ऐ ', 'vṛddhi (ai split)'),
    (r'ौ', r' औ ', 'vṛddhi (au split)'),
    # Visarga and anusvara
    (r'ः', r' ः ', 'visarga-space'),
    (r'ं', r' ं ', 'anusvara-space'),
    # Avagraha (elision marker)
    (r'ऽ', r' ', 'avagraha-split'),
]


def reverse_vowel_sandhi_variants(text: str) -> List[Tuple[str, str]]:
    """Generate plausible reverse-splits for vowel sandhi."""
    variants = []

    # These are conservative splits preserving word boundaries
    if 'ो' in text and 'ः' not in text:  # Avoid visarga cases
        variants.append((text.replace('ो', ' अ उ '), 'o->a+u'))

    if 'े' in text:
        variants.append((text.replace('े', ' अ इ '), 'e->a+i'))

    return variants


def reverse_visarga_variants(text: str) -> List[Tuple[str, str]]:
    """Attempt conservative visarga reversals."""
    variants = []

    if 'ः' in text:
        # Try word boundary around visarga
        variants.append((re.sub(r'ः', ' ः ', text), 'visarga-boundary'))

    return variants


def reverse_anusvara_variants(text: str) -> List[Tuple[str, str]]:
    """Expand anusvara into probable nasal consonants based on context."""
    variants = []

    # Context-aware anusvara expansion
    for m in re.finditer(r'ं', text):
        idx = m.start()
        if idx + 1 < len(text):
            nxt = text[idx + 1]

            # Determine appropriate nasal based on following consonant
            if nxt in 'कखगघङ':
                variants.append((text[:idx] + 'ङ्' + text[idx + 1 :], 'anusvara->ṅ'))
            elif nxt in 'चछजझञ':
                variants.append((text[:idx] + 'ञ्' + text[idx + 1 :], 'anusvara->ñ'))
            elif nxt in 'टठडढण':
                variants.append((text[:idx] + 'ण्' + text[idx + 1 :], 'anusvara->ṇ'))
            elif nxt in 'तथदधन':
                variants.append((text[:idx] + 'न्' + text[idx + 1 :], 'anusvara->n'))
            elif nxt in 'पफबभम':
                variants.append((text[:idx] + 'म्' + text[idx + 1 :], 'anusvara->m'))

    return variants


def _one_step_candidates(text: str, lexicon: set) -> List[Dict]:
    """Apply each reverse rule once and return scored candidates."""
    out = []
    seen = set()

    # Apply simple regex rules
    for pat, repl, name in REVERSE_RULES:
        if re.search(pat, text):
            cand = re.sub(pat, repl, text)
            cand = re.sub(r'\s+', ' ', cand).strip()  # Clean up spaces
            if cand not in seen:
                seen.add(cand)
                score = _baseline_score(text, cand, name, lexicon)
                out.append({'cand': cand, 'score': score, 'rules': [name]})

    # Add variant splits
    for cand, rule_name in reverse_vowel_sandhi_variants(text):
        cand = re.sub(r'\s+', ' ', cand).strip()
        if cand not in seen:
            seen.add(cand)
            score = _baseline_score(text, cand, rule_name, lexicon)
            out.append({'cand': cand, 'score': score, 'rules': [rule_name]})

    for cand, rule_name in reverse_visarga_variants(text):
        cand = re.sub(r'\s+', ' ', cand).strip()
        if cand not in seen:
            seen.add(cand)
            score = _baseline_score(text, cand, rule_name, lexicon)
            out.append({'cand': cand, 'score': score, 'rules': [rule_name]})

    for cand, rule_name in reverse_anusvara_variants(text):
        cand = re.sub(r'\s+', ' ', cand).strip()
        if cand not in seen:
            seen.add(cand)
            score = _baseline_score(text, cand, rule_name, lexicon)
            out.append({'cand': cand, 'score': score, 'rules': [rule_name]})

    return out


def _baseline_score(orig: str, cand: str, rule_name: str, lexicon: set) -> float:
    """
    Score candidate plausibility.

    Scoring factors:
    - Lexicon overlap (strongly rewarded)
    - Edit distance (penalized)
    - Isolated independent vowels (penalized)
    - Rule complexity (small penalty)
    """
    score = 1.0

    # Penalize isolated independent vowels
    iso_vowels = len([t for t in re.split(r'\s+', cand) if len(t) == 1 and re.match(r'[\u0905-\u0914]', t)])
    score -= 0.25 * iso_vowels

    # Lexicon reward: fraction of tokens in lexicon
    tokens = [t for t in re.split(r'\s+', cand) if t]
    if tokens and lexicon:
        found = sum(1 for t in tokens if t in lexicon)
        frac = found / len(tokens)
        score += 0.7 * frac

    # Small penalty for large edit distance
    diff = abs(len(cand) - len(orig))
    score -= 0.02 * diff

    # Prefer candidates with more word boundaries
    word_count = len(tokens)
    score += 0.05 * word_count

    # Rule complexity penalty
    if rule_name and rule_name != 'identity':
        score -= 0.03

    # Clip score range
    return max(-2.0, min(2.0, score))


def gen_candidates(line: str, k: int = 8, lexicon_path: str = None, allow_aggressive: bool = False) -> List[Dict]:
    """
    Generate up to k candidate reverse-sandhi decompositions for line.

    Args:
        line: Input string (merged Sanskrit text)
        k: Maximum number of candidates to return (default: 8)
        lexicon_path: Optional path to lexicon file (default: None)
        allow_aggressive: If True, include more aggressive splits (default: False)

    Returns:
        List of dicts: [{'cand': str, 'score': float, 'rules': [str]}, ...]
        Sorted by score descending (highest score first)

    Example:
        >>> candidates = gen_candidates("कर्मण्येवाधिकारस्ते", k=3)
        >>> for c in candidates:
        ...     print(f"{c['score']:.2f}: {c['cand']}")
    """
    line = normalize_sandhi_text(line)

    # Load lexicon
    lexicon = set(DEFAULT_LEXICON)
    if lexicon_path:
        lexicon |= load_lexicon(lexicon_path)

    # Start with original as baseline
    candidates = [{'cand': line, 'score': _baseline_score(line, line, 'identity', lexicon), 'rules': ['identity']}]

    # Generate one-step candidates
    one_step = _one_step_candidates(line, lexicon)
    candidates.extend(one_step)

    # Optionally generate two-step expansions
    if allow_aggressive:
        expanded = []
        for item in one_step[:3]:  # Only top 3 to avoid explosion
            sub_candidates = _one_step_candidates(item['cand'], lexicon)
            for s in sub_candidates[:2]:  # Only top 2 sub-candidates
                combined_rules = item['rules'] + s['rules']
                combined_score = (item['score'] + s['score']) / 2.0
                expanded.append({'cand': s['cand'], 'score': combined_score, 'rules': combined_rules})
        candidates.extend(expanded)

    # Deduplicate by candidate text, keeping best score
    best = {}
    for c in candidates:
        txt = c['cand']
        if txt not in best or c['score'] > best[txt]['score']:
            best[txt] = c

    # Sort by score descending and return top k
    result = sorted(best.values(), key=lambda x: x['score'], reverse=True)
    return result[:k]


# CLI test function
def main():
    """Test sandhi resolution with example verses."""
    examples = ["रामोऽस्ति बलवान्", "कर्मण्येवाधिकारस्ते", "सर्वे भवन्तु सुखिनः", "सह नाववतु", "धर्मो रक्षति रक्षितः"]

    print("Sanskrit Sandhi Resolution Test")
    print("=" * 80)

    for text in examples:
        print(f"\nInput: {text}")
        candidates = gen_candidates(text, k=5)
        print(f"Candidates ({len(candidates)}):")
        for i, c in enumerate(candidates, 1):
            rules_str = ', '.join(c['rules'])
            print(f"  {i}. [{c['score']:+.2f}] {c['cand']}")
            print(f"      Rules: {rules_str}")


if __name__ == "__main__":
    main()
