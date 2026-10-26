"""Chanda-name normalisation and matching for definitive_comparison.py."""

# Import transliteration library for proper Devanagari handling
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate

    HAS_TRANSLITERATION = True
except ImportError:
    HAS_TRANSLITERATION = False
    print("Warning: indic_transliteration not installed. Install with: pip install indic_transliteration")


def normalize_chanda_name(name: str) -> str:
    """
    Normalize meter name by converting to basic Latin for comparison.
    Uses proper transliteration library for accurate Devanagari→IAST conversion.

    Examples:
        'इन्द्रवज्रा' → 'indravajra'
        'indravajrā' → 'indravajra'
        'vasantatilakam' → 'vasantatilak'
    """
    if not name:
        return ''

    name = name.strip()

    # Check if contains Devanagari (Unicode range 0900-097F)
    has_devanagari = any('\u0900' <= c <= '\u097f' for c in name)

    if has_devanagari and HAS_TRANSLITERATION:
        # Use proper transliteration for accurate conversion
        name = transliterate(name, sanscript.DEVANAGARI, sanscript.IAST)
    elif has_devanagari:
        # Fallback: basic character-by-character mapping (less accurate)
        devanagari_map = {
            'अ': 'a',
            'आ': 'aa',
            'इ': 'i',
            'ई': 'ii',
            'उ': 'u',
            'ऊ': 'uu',
            'ऋ': 'ri',
            'ए': 'e',
            'ऐ': 'ai',
            'ओ': 'o',
            'औ': 'au',
            'क': 'ka',
            'ख': 'kha',
            'ग': 'ga',
            'घ': 'gha',
            'ङ': 'na',
            'च': 'ca',
            'छ': 'cha',
            'ज': 'ja',
            'झ': 'jha',
            'ञ': 'na',
            'ट': 'ta',
            'ठ': 'tha',
            'ड': 'da',
            'ढ': 'dha',
            'ण': 'na',
            'त': 'ta',
            'थ': 'tha',
            'द': 'da',
            'ध': 'dha',
            'न': 'na',
            'प': 'pa',
            'फ': 'pha',
            'ब': 'ba',
            'भ': 'bha',
            'म': 'ma',
            'य': 'ya',
            'र': 'ra',
            'ल': 'la',
            'व': 'va',
            'श': 'sha',
            'ष': 'sha',
            'स': 'sa',
            'ह': 'ha',
            'ा': 'a',
            'ि': 'i',
            'ी': 'i',
            'ु': 'u',
            'ू': 'u',
            'े': 'e',
            'ै': 'ai',
            'ो': 'o',
            'ौ': 'au',
            'ं': 'm',
            'ः': 'h',
            '्': '',
            'ृ': 'ri',
            'ँ': '',
            'ऽ': '',
        }
        for dev, lat in devanagari_map.items():
            name = name.replace(dev, lat)

    # Now normalize IAST diacritics to basic Latin
    n = name.lower()
    replacements = [
        ('ā', 'a'),
        ('ä', 'a'),  # long a
        ('ī', 'i'),  # long i
        ('ü', 'u'),
        ('ū', 'u'),  # long u
        ('ṭ', 't'),
        ('ḍ', 'd'),  # retroflex
        ('ṇ', 'n'),
        ('ṅ', 'n'),
        ('ñ', 'n'),  # nasals
        ('ṃ', 'm'),
        ('ṁ', 'm'),  # anusvara
        ('ḥ', 'h'),  # visarga
        ('ś', 'sh'),
        ('ṣ', 'sh'),  # sibilants
        ('ṛ', 'ri'),  # vocalic r
        ('ḷ', 'l'),  # vocalic l
    ]
    for old, new in replacements:
        n = n.replace(old, new)

    # Remove trailing 'm' or 'a' (common suffix variations)
    for suffix in ['m', 'a']:
        if n.endswith(suffix) and len(n) > 5:
            n = n[:-1]

    return n


def chanda_names_match(expected: str, actual_list: list) -> bool:
    """
    Check if expected meter name matches any name in actual_list.

    Uses normalized comparison with proper Devanagari transliteration.
    Also handles common spelling variants and partial matching.

    Examples that should match:
        - 'indravajrā' and 'इन्द्रवज्रा'
        - 'anuṣṭup' and 'anuṣṭubh'
        - 'vasantatilakam' and 'वसन्ततिलका'
    """
    if not expected or not actual_list:
        return False

    exp_norm = normalize_chanda_name(expected)

    # Common spelling variants (normalized_expected -> normalized_variants)
    SPELLING_VARIANTS = {
        'anushtup': ['anushtubh', 'anustubh', 'anustup', 'slok', 'shlok'],
        'slok': ['anushtup', 'anushtubh', 'anustubh'],
        'pythvi': ['prithvi', 'prthvi', 'prithv'],
        'shardulavikridita': ['shardulvikriditam', 'shardulavikriditam', 'shardulvikridita'],
        'shardulvikridita': ['shardulvikriditam', 'shardulavikriditam'],
        'indravajr': ['upajati'],  # Indravajra is a type of Upajati
        'upendravajr': ['upajati'],
    }

    for actual in actual_list:
        act_norm = normalize_chanda_name(actual)

        # Exact normalized match
        if exp_norm == act_norm:
            return True

        # Check spelling variants
        if exp_norm in SPELLING_VARIANTS:
            if act_norm in SPELLING_VARIANTS[exp_norm]:
                return True

        # Prefix match for longer names (at least 5 chars matching)
        min_len = min(len(exp_norm), len(act_norm))
        if min_len >= 5:
            # Check if first 5+ chars match (handles suffix variations)
            prefix_len = max(5, min_len - 2)
            if exp_norm[:prefix_len] == act_norm[:prefix_len]:
                return True

        # One contains the other (for compound names)
        if len(exp_norm) >= 5 and len(act_norm) >= 5:
            if exp_norm in act_norm or act_norm in exp_norm:
                return True

    return False
