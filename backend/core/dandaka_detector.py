"""
Daṇḍaka and Rājaśyāmalā Stotram Detection Module

This module handles identification of:
1. Daṇḍaka verses - classified by akṣara count, not metre
2. Rājaśyāmalā Stotram - unmetrical Tantric devotional hymns
"""

import re
import unicodedata
from typing import Any, Dict

# Daṇḍaka classification ranges (by akṣara count)
DANDAKA_TYPES = [
    (0, 26, 'Saṃkīrṇa-daṇḍakam'),
    (27, 51, 'Madhyama-daṇḍakam'),
    (52, 108, 'Prabandha-daṇḍakam'),
    (109, float('inf'), 'Ati-daṇḍakam'),
]

# Rājaśyāmalā Stotram semantic markers
RAJASHYAMALA_KEYWORDS = [
    'श्यामला', 'राजश्यामला', 'मातङ्गी', 'वाग्देवी', 'वरदा',
    'विद्यादात्री', 'राज्यम्', 'ऐश्वर्यम्', 'मातङ्ग', 'श्याम',
    'षोडशी', 'त्रिपुरसुन्दरी', 'महाविद्या', 'तन्त्र'
]

RAJASHYAMALA_TITLE_PATTERNS = [
    r'राज\s*श्यामला\s*स्तोत्रम्?',
    r'श्री\s*मत्\s*राज्ञा\s*श्यामला\s*देव्याः?\s*स्तोत्रम्?',
    r'राज\s*श्यामला\s*स्तव',
    r'श्यामला\s*दण्डकम्?',
]


def normalize_text(text: str) -> str:
    """Normalize Unicode text to NFC form"""
    return unicodedata.normalize('NFC', text)


def count_aksaras(text: str) -> int:
    """
    Count akṣaras (syllables) using traditional Sanskrit rules:
    - Independent vowels = 1 akṣara
    - Consonant + vowel sign = 1 akṣara
    - Consonant + virāma (्) = 0 akṣaras
    - Consonant alone = 1 akṣara (implicit 'a')
    - Anusvāra (ं), Visarga (ः) do NOT add akṣaras
    - Punctuation & whitespace ignored
    """
    text = normalize_text(text)

    # Remove punctuation and whitespace
    text = re.sub(r'[।॥\s\d\.,;:!?()\[\]{}\"\']+', '', text)

    aksara_count = 0
    i = 0

    while i < len(text):
        char = text[i]

        # Skip anusvāra, visarga, and chandrabindu (they modify previous akṣara)
        if char in 'ंः\u0901\u0902\u0903':
            i += 1
            continue

        # Independent vowels
        if '\u0905' <= char <= '\u0914':  # अ to औ
            aksara_count += 1
            i += 1
            continue

        # Consonants
        if '\u0915' <= char <= '\u0939':  # क to ह
            # Check if followed by virāma
            if i + 1 < len(text) and text[i + 1] == '\u094D':  # ्
                # Consonant + virāma = no akṣara
                i += 2
                continue
            else:
                # Consonant (with implicit 'a' or vowel sign) = 1 akṣara
                aksara_count += 1
                # Skip following vowel sign if present
                if i + 1 < len(text) and '\u093E' <= text[i + 1] <= '\u094C':
                    i += 2
                else:
                    i += 1
                continue

        # Vowel signs (should be handled with consonants, but count if standalone)
        if '\u093E' <= char <= '\u094C':  # ा to ौ
            aksara_count += 1
            i += 1
            continue

        # Move to next character
        i += 1

    return aksara_count


def count_viramas(text: str) -> int:
    """Count virāma (्) characters in text"""
    text = normalize_text(text)
    return text.count('\u094D')


def calculate_density(aksara_count: int, virama_count: int) -> float:
    """Calculate virāma density (compound indicator)"""
    if aksara_count == 0:
        return 0.0
    return virama_count / aksara_count


def classify_dandaka_unit(aksara_count: int) -> str:
    """Classify a unit into daṇḍaka type based on akṣara count"""
    for min_count, max_count, classification in DANDAKA_TYPES:
        if min_count <= aksara_count <= max_count:
            return classification
    return 'Ati-daṇḍakam'  # Default for very large counts


def detect_dandaka(text: str) -> Dict[str, Any]:
    """
    Detect if text is a Daṇḍakam and classify units.
    
    Returns:
        Dict with:
            - is_dandaka: bool
            - units: List of unit analysis
            - total_aksaras: int
            - total_viramas: int
            - average_density: float
    """
    text = normalize_text(text)

    # Split by daṇḍa (।) and double daṇḍa (॥)
    units = re.split(r'[।॥]+', text)
    units = [u.strip() for u in units if u.strip()]

    if not units:
        return {
            'is_dandaka': False,
            'units': [],
            'total_aksaras': 0,
            'total_viramas': 0,
            'average_density': 0.0
        }

    analyzed_units = []
    total_aksaras = 0
    total_viramas = 0

    for unit_text in units:
        aksara_count = count_aksaras(unit_text)
        virama_count = count_viramas(unit_text)
        density = calculate_density(aksara_count, virama_count)
        classification = classify_dandaka_unit(aksara_count)

        analyzed_units.append({
            'text': unit_text[:100] + '...' if len(unit_text) > 100 else unit_text,
            'aksara_count': aksara_count,
            'virama_count': virama_count,
            'density': round(density, 3),
            'classification': classification
        })

        total_aksaras += aksara_count
        total_viramas += virama_count

    average_density = calculate_density(total_aksaras, total_viramas)

    # Consider it a daṇḍaka if:
    # 1. Has long units (>26 akṣaras on average)
    # 2. High compound density (virama_density > 0.15)
    avg_aksaras_per_unit = total_aksaras / len(analyzed_units)
    is_dandaka = avg_aksaras_per_unit > 26 or average_density > 0.15

    return {
        'is_dandaka': is_dandaka,
        'units': analyzed_units,
        'total_aksaras': total_aksaras,
        'total_viramas': total_viramas,
        'average_density': round(average_density, 3)
    }


def detect_rajashyamala(text: str) -> Dict[str, Any]:
    """
    Detect if text is Rājaśyāmalā Stotram using semantic and structural markers.
    
    Returns:
        Dict with:
            - is_rajashyamala: bool
            - confidence: float (0-1)
            - matched_keywords: List[str]
            - title_match: bool
            - semantic_markers: List[str]
            - structure_type: str
    """
    text = normalize_text(text)

    # Check for title patterns
    title_match = False
    for pattern in RAJASHYAMALA_TITLE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            title_match = True
            break

    # Check for semantic keywords
    matched_keywords = []
    for keyword in RAJASHYAMALA_KEYWORDS:
        if keyword in text:
            matched_keywords.append(keyword)

    # Semantic markers (phrases common in Rājaśyāmalā)
    semantic_patterns = [
        r'वाग्देव',
        r'विद्या.*दात्र',
        r'राज्य.*प्रद',
        r'ऐश्वर्य',
        r'मातङ्ग',
        r'षोडश',
        r'महाविद्या'
    ]

    semantic_markers = []
    for pattern in semantic_patterns:
        if re.search(pattern, text):
            semantic_markers.append(pattern)

    # Calculate confidence
    confidence = 0.0
    if title_match:
        confidence += 0.4
    confidence += min(len(matched_keywords) * 0.1, 0.4)
    confidence += min(len(semantic_markers) * 0.05, 0.2)

    # Determine structure type
    structure_type = 'unknown'
    if title_match or confidence > 0.6:
        if 'तन्त्र' in matched_keywords or 'महाविद्या' in matched_keywords:
            structure_type = 'tantric-hymn'
        elif any('मन्त्र' in text for _ in range(1)):
            structure_type = 'mantra-based'
        else:
            structure_type = 'stotra-prose'

    is_rajashyamala = confidence >= 0.5 or title_match

    return {
        'is_rajashyamala': is_rajashyamala,
        'confidence': round(confidence, 2),
        'matched_keywords': matched_keywords,
        'title_match': title_match,
        'semantic_markers': semantic_markers,
        'structure_type': structure_type
    }


def analyze_dandaka_mode(text: str) -> Dict[str, Any]:
    """
    Complete analysis for Daṇḍaka mode.
    Checks both Daṇḍaka and Rājaśyāmalā identification.
    
    Returns combined result with text_type classification.
    """
    dandaka_result = detect_dandaka(text)
    rajashyamala_result = detect_rajashyamala(text)

    # Determine primary text type
    if rajashyamala_result['is_rajashyamala']:
        text_type = 'rajashyamala-stotram'
    elif dandaka_result['is_dandaka']:
        text_type = 'dandaka'
    elif rajashyamala_result['confidence'] > 0.3 and dandaka_result['is_dandaka']:
        text_type = 'mixed'
    else:
        text_type = 'unclassified'

    return {
        'mode': 'dandaka',
        'dandaka': dandaka_result,
        'rajashyamala': rajashyamala_result,
        'text_type': text_type
    }
