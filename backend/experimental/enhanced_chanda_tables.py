"""Gaṇa symbols, Vedic meter tables and Upajāti definitions for EnhancedChanda.

Mixed into backend.core.enhanced_chanda.EnhancedChanda.
"""


class EnhancedTables:
    # Gaṇa symbols
    Y = 'Y'
    R = 'R'
    T = 'T'
    N = 'N'
    B = 'B'
    J = 'J'
    S = 'S'
    M = 'M'
    L = 'L'
    G = 'G'
    SYMBOLS = f'{Y}{R}{T}{N}{B}{J}{S}{M}{L}{G}'

    # Gaṇa patterns (from Chandovallari Section 3)
    GANA = {
        Y: f'{L}{G}{G}',  # ya-gaṇa: u--
        R: f'{G}{L}{G}',  # ra-gaṇa: -u-
        T: f'{G}{G}{L}',  # ta-gaṇa: --u
        N: f'{L}{L}{L}',  # na-gaṇa: uuu
        B: f'{G}{L}{L}',  # bha-gaṇa: -uu
        J: f'{L}{G}{L}',  # ja-gaṇa: u-u
        S: f'{L}{L}{G}',  # sa-gaṇa: uu-
        M: f'{G}{G}{G}',  # ma-gaṇa: ---
    }

    # Vedic Meters (from Chandovallari Section 6)
    VEDIC_METERS = {
        'Gayatri': {'syllables': 24, 'padas': 3, 'per_pada': 8, 'description': '3×8'},
        'Ushnik': {'syllables': 28, 'padas': 4, 'per_pada': 7, 'description': '4×7'},
        'Anushtubh': {'syllables': 32, 'padas': 4, 'per_pada': 8, 'description': '4×8'},
        'Brihati': {'syllables': 36, 'padas': 4, 'per_pada': 9, 'description': '4×9'},
        'Pankti': {'syllables': 40, 'padas': 5, 'per_pada': 8, 'description': '5×8'},
        'Trishtubh': {'syllables': 44, 'padas': 4, 'per_pada': 11, 'description': '4×11'},
        'Jagati': {'syllables': 48, 'padas': 4, 'per_pada': 12, 'description': '4×12'},
    }

    # Extended Vedic Meters
    EXTENDED_VEDIC = {
        'Atijagati': {'syllables': 52, 'per_pada': 13},
        'Shakvari': {'syllables': 56, 'per_pada': 14},
        'Atishakvari': {'syllables': 60, 'per_pada': 15},
        'Ashti': {'syllables': 64, 'per_pada': 16},
        'Atyashti': {'syllables': 68, 'per_pada': 17},
        'Dhriti': {'syllables': 72, 'per_pada': 18},
        'Atidhriti': {'syllables': 76, 'per_pada': 19},
    }

    # Vedic family names (used to prevent boosting over specific meters)
    VEDIC_FAMILY_NAMES = {
        'त्रिष्टुभ्',
        'Trishtubh',
        'Triṣṭubh',
        'त्रिष्टुप्',
        'जगती',
        'Jagati',
        'Jagatī',
        'गायत्री',
        'Gayatri',
        'Gāyatrī',
        'अनुष्टुभ्',
        'Anushtubh',
        'Anuṣṭubh',
        'Anuṣṭup',
        'उष्णिक्',
        'Ushnik',
        'Uṣṇik',
        'बृहती',
        'Brihati',
        'Bṛhatī',
        'पङ्क्ति',
        'Pankti',
        'Paṅkti',
    }

    # Classical pada patterns (from Chandovallari Section 11)
    # Pattern: (Devanagari name, IAST name, Gaṇa formula)
    CLASSICAL_PADA_PATTERNS = {
        # 11-syllable Triṣṭup class (Section 11)
        'GGLGGLGGLGG': ('इन्द्रवज्रा', 'Indravajrā', 'त त ज ग ग'),
        'LGLLGGLGGLGG': ('उपेन्द्रवज्रा', 'Upendravajrā', 'ज त ज ग ग'),
        'GGGGGLLGGLLGG': ('शालिनी', 'Śālinī', 'म त त ग ग'),
        'GLGLLLGLGLGL': ('रथोद्धता', 'Rathoddhata', 'र न र ल ग'),
        'GLGLLLGLLGG': ('स्वागता', 'Svāgatā', 'र न भ ग ग'),
        'GLLGLLGLLGG': ('दोधक', 'Dodhakam', 'भ भ भ ग ग'),
        # 12-syllable Jagatī class
        'LGLLGGLGGLGLG': ('वंशस्थ', 'Vaṁśasthavilam', 'ज त ज र'),
        'GGLGGLGGLGLG': ('इन्द्रवंशा', 'Indravaṁśā', 'त त ज र'),
        'LGGLGGLGGLGG': ('भुजङ्गप्रयात', 'Bhujangaprayātam', 'य य य य'),
        'LLGLLGLLGLLG': ('तोटक', 'Toṭakam', 'स स स स'),
        'GLGGLGGLGGLG': ('स्रग्विणी', 'Sragviṇī', 'र र र र'),
        'LLLGLLGLLGLG': ('द्रुतविलम्बित', 'Drutavilambitam', 'न भ भ र'),
        # 13-syllable meters
        'GGGLLLLLGLGLGG': ('प्रहर्षिणी', 'Praharṣiṇī', 'म न ज र ग'),
        'LGLLGLLLLGLGLG': ('रुचिरा', 'Rucirā', 'ज भ स ज ग'),
        # 14-syllable Śakvarī class
        'GGLGLLLLGLLGG': ('वसन्ततिलका', 'Vasantatilakam', 'त भ ज ज ग ग'),
        # 15-syllable Atiśakvarī class
        'LLLLLLGGGLGGLGG': ('मालिनी', 'Mālinī', 'न न म य य'),
        # 17-syllable Atyaṣṭi class
        'LGGGGGLLLLLLGGLLLG': ('शिखरिणी', 'Śikhariṇī', 'य म न स भ ल ग'),
        'GGGGLLLLLLGGLGGLGG': ('मन्दाक्रान्ता', 'Mandākrāntā', 'म भ न त त ग ग'),
        # 19-syllable Atidhṛti class
        'GGGLLLGLLLLGGGLLGLG': ('शार्दूलविक्रीडित', 'Śārdūlavikrīḍitam', 'म स ज स त त ग'),
        # 21-syllable Prakṛti class
        'GGGGLLGLLLLLLGGLGGLGG': ('स्रग्धरा', 'Sragdharā', 'म र भ न य य य'),
    }

    # Yati (caesura) positions for meters (from Chandovallari Section 5 & 11)
    YATI_POSITIONS = {
        'इन्द्रवज्रा': [5, 11],
        'उपेन्द्रवज्रा': [5, 11],
        'शालिनी': [4, 11],
        'रथोद्धता': [4, 11],
        'वंशस्थ': [5, 12],
        'भुजङ्गप्रयात': [6, 12],
        'तोटक': [4, 8, 12],
        'द्रुतविलम्बित': [4, 8, 12],
        'वसन्ततिलका': [8, 14],
        'मालिनी': [8, 15],
        'शिखरिणी': [6, 17],
        'मन्दाक्रान्ता': [4, 10, 17],
        'शार्दूलविक्रीडित': [12, 19],
        'स्रग्धरा': [7, 14, 21],
    }

    # 14 Upajāti varieties (from Chandovallari Section on Upajāti)
    # इ = Indravajrā pada, उ = Upendravajrā pada
    UPAJATI_VARIETIES = {
        ('उ', 'इ', 'इ', 'इ'): 'कीर्तिः',
        ('इ', 'उ', 'इ', 'इ'): 'वाणी',
        ('उ', 'उ', 'इ', 'इ'): 'माला',
        ('इ', 'इ', 'उ', 'इ'): 'शाला',
        ('उ', 'इ', 'उ', 'इ'): 'हंसी',
        ('इ', 'उ', 'उ', 'इ'): 'माया',
        ('उ', 'उ', 'उ', 'इ'): 'जाया',
        ('इ', 'इ', 'इ', 'उ'): 'बाला',
        ('उ', 'इ', 'इ', 'उ'): 'आर्द्रा',
        ('इ', 'उ', 'इ', 'उ'): 'भद्रा',
        ('उ', 'उ', 'इ', 'उ'): 'प्रेमा',
        ('इ', 'इ', 'उ', 'उ'): 'रामा',
        ('उ', 'इ', 'उ', 'उ'): 'ऋद्धिः',
        ('इ', 'उ', 'उ', 'उ'): 'बुद्धिः',
    }

    # Indravajrā and Upendravajrā patterns for Upajāti detection
    INDRAVAJRA_PATTERN = 'GGLGGLGGLGG'
    UPENDRAVAJRA_PATTERN = 'LGLLGGLGGLGG'

    # Āryā family mātrā patterns (from Chandovallari Section 10)
    ARYA_FAMILY = {
        'आर्या': {'matras': [12, 18, 12, 15], 'description': 'Base Āryā'},
        'गीति': {'matras': [12, 18, 12, 18], 'description': 'Gīti'},
        'उपगीति': {'matras': [12, 15, 12, 15], 'description': 'Upagīti'},
        'उद्गीति': {'matras': [12, 15, 12, 18], 'description': 'Udgīti'},
        'आर्यागीति': {'matras': [12, 20, 12, 20], 'description': 'Āryāgīti'},
    }
