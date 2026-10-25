"""Word lists, patterns and syllable tables that TextClassifier scores Sanskrit text against.

Kept apart from backend/core/text_classifier.py so the classification logic
reads on its own; TextClassifier exposes each table under the same name.
"""

# =========================================================================
# VEDIC MARKERS
# =========================================================================

# Vedic-specific vocabulary (archaic forms, Vedic deities, ritual terms)
VEDIC_VOCABULARY = {
    # Deities (Vedic style invocation)
    'अग्नि',
    'इन्द्र',
    'वरुण',
    'मित्र',
    'सोम',
    'अश्विन',
    'मरुत',
    'रुद्र',
    'विष्णु',
    'सविता',
    'पूषन',
    'भग',
    'अर्यमन',
    'दक्ष',
    'अंश',
    'त्वष्टृ',
    'विवस्वत',
    'आदित्य',
    'वायु',
    'पर्जन्य',
    'द्यौस',
    'पृथिवी',
    'उषस',
    'अहि',
    'वृत्र',
    'असुर',
    'आपः',
    'जातवेदस',
    # Vedic ritual terms
    'यज्ञ',
    'होत',
    'होतृ',
    'होतार',
    'ऋत्विज',
    'अध्वर',
    'सोमपीत',
    'हव्य',
    'पुरोहित',
    'बर्हिस',
    'स्रुच',
    'स्रुव',
    'जुहू',
    'उपभृत',
    'ध्रुवा',
    'इध्म',
    'समिध',
    'आज्य',
    'घृत',
    'दधि',
    'मधु',
    'भेषज',
    'वरूथ',
    # Vedic archaic forms
    'ईळ',
    'ईड',
    'स्तु',
    'गृणा',
    'अर्च',
    'नम',
    'वन्द',
    'शंस',
    'ब्रू',
    'ऋषि',
    'कवि',
    'विप्र',
    'वेधस',
    'मेधस',
    'शूर',
    'महि',
    # Ritual actions
    'यज',
    'जुहु',
    'दा',
    'भज',
    'गम',
    'इ',
    'कृ',
    # Vedic compounds
    'रत्नधातम',
    'वीरवत्तम',
    'सत्यश्चित्र',
    'कविक्रतु',
    'घृताची',
    # Vedic verb forms (archaic endings)
    'वक्षति',
    'गच्छति',
    'करिष्यसि',
    'एमसि',
    'भरन्त',
    # Common Vedic starters and vocatives
    'अग्निमीळे',
    'इन्द्रं',
    'वायवा',
    'मित्रं',
    'सोमं',
    # Vocatives (O Vayu, O Indra, etc.) - common in Rigveda
    'वायो',
    'इन्द्रा',
    'अग्ने',
    'देव',
    'देवा',
    # Vedic imperatives and verb forms
    'याहि',
    'पृणीत',
    'श्रुधी',
    'पाहि',
    'गहि',
    'एहि',
    'जुषस्व',
    'शृणु',
    'वेधि',
    'विद्धि',
    # Vedic particles and common words
    'दृशे',
    'भुजे',
    'सुशिप्र',
    'शतक्रतु',
    'वाजिन',
    'स्तोम',
    'उक्थ',
    'ब्रह्म',
    'गिर',
    'मन्त्र',
    'ऋच',
    # Vedic adjectives and epithets
    'सुमन',
    'विश्वचर्षणि',
    'पुरुष्टुत',
    'वृषभ',
    'वृषन',
    'सुदक्ष',
    'सुक्रतु',
    'सुशंस',
    'सुमति',
    # Vedic nouns
    'रयि',
    'क्षत्र',
    'वाज',
    'सहस',
    'ओजस',
    'तेजस',
    'केतु',
    'अर्क',
    'अर्चि',
    'द्युम्न',
    'श्रवस',
    # Common Rigvedic words from misclassified verses
    'अस्माकं',
    'विश्वा',
    'सुमनस',
    'देवयंत',
}

# Vedic-specific suffixes and endings
VEDIC_SUFFIXES = [
    'वत्तम',
    'तम',
    'वान्',
    'मान्',
    'आन',
    'उस्',
    'षि',
    'न्वत्',
    'धातम',
    'कृतु',
    'श्रवस्',
]

# Vedic word patterns (regex) - archaic forms
VEDIC_PATTERNS = [
    r'स्व\S+',  # Words starting with स्व (sva-)
    r'\S+भिः',  # Instrumental plural ending -bhiḥ
    r'\S+षु',  # Locative plural ending -ṣu
    r'\S+ेभ्यः',  # Dative plural ending
    r'\S+ाय',  # Dative singular ending
]

# Vedic Unicode range (Vedic Extensions)
# U+1CD0-U+1CFF: Vedic Extensions including tone marks
VEDIC_UNICODE_RANGES = [
    (0x1CD0, 0x1CFF),  # Vedic Extensions
    (0x0951, 0x0954),  # Vedic tone marks in Devanagari
]

# Vedic special characters
VEDIC_SPECIAL_CHARS = {
    '\u0951',  # Udatta (svarita)
    '\u0952',  # Anudatta
    '\u1cd0',  # Vedic tone Karshana
    '\u1cd1',  # Vedic tone Shara
    '\u1cd2',  # Vedic tone Prenkha
    '\u1cf2',  # Vedic sign Ardhavisarga
    '\u1cf3',  # Vedic sign Rotated Ardhavisarga
    '\u1cf4',  # Vedic tone Candra Above
    '\u1cf5',  # Vedic sign Jihvamuliya
    '\u1cf6',  # Vedic sign Upadhmaniya
    'ळ',  # Used in Vedic texts
}

# Vedic syllable counts for major meters
# Maps syllable count -> (meter_name, is_exact)
VEDIC_SYLLABLE_COUNTS = {
    24: ('गायत्री', True),  # 3×8 padas
    28: ('उष्णिक्', True),  # 4×7 or 8+8+12
    32: ('अनुष्टुभ्', True),  # 4×8 padas
    36: ('बृहती', True),  # 8+8+12+8 or variations
    40: ('पङ्क्ति', True),  # 5×8 or 4×10
    44: ('त्रिष्टुभ्', True),  # 4×11 padas
    48: ('जगती', True),  # 4×12 padas
    # Variations with ±2 tolerance
    22: ('गायत्री', False),
    23: ('गायत्री', False),
    25: ('गायत्री', False),
    26: ('उष्णिक्', False),
    27: ('उष्णिक्', False),
    29: ('उष्णिक्', False),
    30: ('अनुष्टुभ्', False),
    31: ('अनुष्टुभ्', False),
    33: ('अनुष्टुभ्', False),
    34: ('बृहती', False),
    35: ('बृहती', False),
    37: ('बृहती', False),
    38: ('पङ्क्ति', False),
    39: ('पङ्क्ति', False),
    41: ('पङ्क्ति', False),
    42: ('त्रिष्टुभ्', False),
    43: ('त्रिष्टुभ्', False),
    45: ('त्रिष्टुभ्', False),
    46: ('जगती', False),
    47: ('जगती', False),
    49: ('जगती', False),
    50: ('जगती', False),
}

# =========================================================================
# CLASSICAL MARKERS
# =========================================================================

# Classical-specific vocabulary (later Sanskrit, Kavya terms)
CLASSICAL_VOCABULARY = {
    # Common Shloka/Kavya terms
    'श्लोक',
    'काव्य',
    'पद्य',
    'गद्य',
    'अलंकार',
    'रस',
    # Classical deities (with epithets)
    'राम',
    'कृष्ण',
    'शिव',
    'पार्वती',
    'गणेश',
    'हनुमान',
    'सीता',
    'राधा',
    'गोविन्द',
    'मुरारि',
    'माधव',
    'केशव',
    'नारायण',
    # Classical themes
    'प्रेम',
    'विरह',
    'शृंगार',
    'करुण',
    'वीर',
    'भक्ति',
    'ज्ञान',
    'मोक्ष',
    'धर्म',
    'अर्थ',
    'काम',
    # Nature imagery (Classical kavya)
    'मेघ',
    'वर्षा',
    'चन्द्र',
    'सूर्य',
    'तारा',
    'नक्षत्र',
    'पुष्प',
    'लता',
    'वन',
    'सरोवर',
    'नदी',
    'पर्वत',
    'समुद्र',
    # Human elements (Classical themes)
    'राजा',
    'रानी',
    'नायक',
    'नायिका',
    'सखी',
    'दूत',
    'प्रिय',
    'प्रिया',
    # Classical compounds and descriptions
    'चन्द्रमुख',
    'कमलनयन',
    'मृगनयन',
    'पद्मपत्र',
    'रत्नभूषण',
    # Meghaduta-style
    'यक्ष',
    'विरहिन',
    'प्रियतम',
    'अलक',
    'उज्जयिनी',
    # Bhagavad Gita markers
    'अर्जुन',
    'पार्थ',
    'भारत',
    'कुरुक्षेत्र',
    'धर्मक्षेत्र',
    'संजय',
    'धृतराष्ट्र',
    'पाण्डव',
    'कौरव',
    # Classical philosophy
    'योग',
    'सांख्य',
    'वेदान्त',
    'न्याय',
    'तत्त्व',
    'आत्मा',
    'ब्रह्म',
    'माया',
    'प्रकृति',
    'पुरुष',
    # Markers from danda usage in classical
    'इति',
    'एवं',
    'तथा',
    'यथा',
    'अपि',
    'तु',
    'हि',
    'च',
    'वा',
}

# Classical structural markers
CLASSICAL_STRUCTURAL_PATTERNS = [
    r'॥\s*\d+\s*॥',  # Verse numbering: ॥ 1 ॥
    r'\|\|',  # Double danda
    r'।\s*$',  # Line ending with danda
    r'॥\s*$',  # Line ending with double danda
    r'इति\s+.*॥',  # "iti" marking end
    r'\d+\s*-\s*\d+',  # Verse references (1-5)
]

# Classical meters with their typical syllable counts (often longer)
CLASSICAL_METERS_SYLLABLES = {
    # Per line counts for classical meters
    14: ['वसन्ततिलका'],  # 14 syllables per line
    17: ['शार्दूलविक्रीडित', 'पृथ्वी'],  # 17 syllables
    19: ['स्रग्धरा'],  # 19 syllables per line
    21: ['मन्दाक्रान्ता'],  # 21 syllables per quarter (long verse)
    11: ['इन्द्रवज्रा', 'उपेन्द्रवज्रा', 'उपजाति'],  # 11 per quarter
    12: ['द्रुतविलम्बित', 'वंशस्थ'],  # 12 per quarter
}
