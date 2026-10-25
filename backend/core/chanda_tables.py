"""Gaṇa symbols and the Vedic meter tables the engine scores against.

Mixed into backend.core.chanda.Chanda; methods rely on its other mixins through self.
"""


class MeterTables:
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
    GANA = {
        Y: f'{L}{G}{G}',
        R: f'{G}{L}{G}',
        T: f'{G}{G}{L}',
        N: f'{L}{L}{L}',
        B: f'{G}{L}{L}',
        J: f'{L}{G}{L}',
        S: f'{L}{L}{G}',
        M: f'{G}{G}{G}',
    }
    VEDIC_METERS = {
        # Standard Vedic meters
        'Gayatri': {'syllables': 24, 'padas': 3, 'per_pada': 8, 'description': '3×8'},
        'Ushnik': {'syllables': 28, 'padas': 4, 'per_pada': 7, 'description': '4×7'},
        'Anushtubh': {'syllables': 32, 'padas': 4, 'per_pada': 8, 'description': '4×8'},
        'Brihati': {'syllables': 36, 'padas': 4, 'per_pada': 9, 'description': '4×9'},
        'Pankti': {'syllables': 40, 'padas': 5, 'per_pada': 8, 'description': '5×8'},
        'Trishtubh': {'syllables': 44, 'padas': 4, 'per_pada': 11, 'description': '4×11'},
        'Jagati': {'syllables': 48, 'padas': 4, 'per_pada': 12, 'description': '4×12'},
        # Gāyatrī variants (Nicṛt, Bhurik, Virāṭ)
        'Nicrt_Gayatri': {'syllables': 21, 'padas': 3, 'per_pada': 7, 'description': '3×7 (निचृत्)'},
        'Bhurik_Gayatri': {'syllables': 27, 'padas': 3, 'per_pada': 9, 'description': '3×9 (भुरिक्)'},
        # Triṣṭubh variants
        'Nicrt_Trishtubh': {'syllables': 40, 'padas': 4, 'per_pada': 10, 'description': '4×10 (निचृत्)'},
        'Virat_Trishtubh': {'syllables': 48, 'padas': 4, 'per_pada': 12, 'description': '4×12 (विराट्)'},
        # Jagatī variants
        'Nicrt_Jagati': {'syllables': 44, 'padas': 4, 'per_pada': 11, 'description': '4×11 (निचृत्)'},
    }

    # Vedic meter definitions by syllable count (for Modal Identification)
    # Updated based on actual Rigveda data distribution analysis
    # Includes composite meters and rare Vedic meters
    # NOTE: Using exact names that match rigveda_with_meters_complete.csv for exact matches
    VEDIC_METERS_BY_COUNT = {
        # Dvipadā meters (half-forms)
        19: {'name': 'द्विपदा विराट्', 'name_en': 'Dvipadā Virāṭ', 'padas': 2, 'per_pada': 10},
        20: {'name': 'द्विपदा विराट्', 'name_en': 'Dvipadā Virāṭ', 'padas': 2, 'per_pada': 10},
        21: {'name': 'द्विपदा त्रिष्टुभ्', 'name_en': 'Dvipadā Triṣṭubh', 'padas': 2, 'per_pada': 11},
        22: {'name': 'द्विपदा त्रिष्टुभ्', 'name_en': 'Dvipadā Triṣṭubh', 'padas': 2, 'per_pada': 11},
        # Standard Vedic meters
        24: {'name': 'गायत्री', 'name_en': 'Gāyatrī', 'padas': 3, 'per_pada': 8},
        26: {'name': 'ककुभ्', 'name_en': 'Kakubh', 'padas': 3, 'per_pada': -1},  # 8+8+12 structure
        28: {'name': 'उष्णिक्', 'name_en': 'Uṣṇik', 'padas': 4, 'per_pada': 7},
        # Kakubh also at 28 but with 3 padas (8+8+12) - detected by pada structure
        32: {'name': 'अनुष्टुभ्', 'name_en': 'Anuṣṭubh', 'padas': 4, 'per_pada': 8},
        36: {'name': 'बृहती', 'name_en': 'Bṛhatī', 'padas': 4, 'per_pada': 9},
        # Pragātha added at peak 39 for syllable-count fallback detection
        # Pragātha is composite (Triṣṭubh 11 + Jagatī 12 pairs) but often detected by syllable count
        39: {'name': 'प्रगाथ', 'name_en': 'Pragātha', 'padas': 2, 'per_pada': -1, 'composite': True},
        40: {'name': 'पङ्क्ति', 'name_en': 'Paṅkti', 'padas': 5, 'per_pada': 8},
        42: {'name': 'ज्योतिस्', 'name_en': 'Jyotis', 'padas': 4, 'per_pada': 10, 'has_refrain': True},
        44: {'name': 'त्रिष्टुभ्', 'name_en': 'Triṣṭubh', 'padas': 4, 'per_pada': 11},
        46: {'name': 'महापङ्क्ति', 'name_en': 'Mahāpaṅkti', 'padas': 6, 'per_pada': 8},
        48: {'name': 'जगती', 'name_en': 'Jagatī', 'padas': 4, 'per_pada': 12},
        # Extended Vedic meters
        52: {'name': 'अतिजगती', 'name_en': 'Atijagatī', 'padas': 4, 'per_pada': 13},
        56: {'name': 'शक्वरी', 'name_en': 'Śakvarī', 'padas': 7, 'per_pada': 8},
        60: {'name': 'अतिशक्वरी', 'name_en': 'Atiśakvarī', 'padas': 4, 'per_pada': 15},
        64: {'name': 'अत्यष्टि', 'name_en': 'Atyaṣṭi', 'padas': 4, 'per_pada': 16},
        65: {'name': 'अष्टि', 'name_en': 'Aṣṭi', 'padas': 4, 'per_pada': 16},
        68: {'name': 'धृति', 'name_en': 'Dhṛti', 'padas': 4, 'per_pada': 17},
        72: {'name': 'अतिधृति', 'name_en': 'Atidhṛti', 'padas': 4, 'per_pada': 18},
        76: {'name': 'कृति', 'name_en': 'Kṛti', 'padas': 4, 'per_pada': 19},
    }

    # Special meters requiring structural analysis (not just syllable count)
    # Pragātha is a COMPOUND meter: 2-verse structure with Triṣṭubh (11) + Jagatī (12) pairs
    COMPOSITE_METERS = {
        'प्रगाथ': {
            'name_en': 'Pragātha',
            'type': 'compound',  # Spans multiple verses
            'syllable_range': (21, 25),  # Per verse: 11+12 = 23 (with variance 21-25)
            'structure': 'Triṣṭubh–Jagatī compound (2-verse pair)',
            # Pattern: Each verse has 2 padas: Triṣṭubh (11) + Jagatī (12)
            # Full Pragātha = [11,12] + [11,12] across 2 verses
            'pada_pattern': [11, 12],  # Per-verse pattern (Triṣṭubh + Jagatī)
            'verse_count': 2,  # Requires 2 consecutive verses
            'components': ['त्रिष्टुभ्', 'जगती'],
            'description': 'A two-verse Vedic compound meter combining Triṣṭubh and Jagatī padas',
        },
        'ककुभ्': {
            'name_en': 'Kakubh',
            'type': 'single',
            'syllable_range': (26, 29),
            'structure': '3 padas (8+8+12)',
            'pada_patterns': [[8, 8, 12]],
            'distinguisher': 'three_pada_unequal',
        },
    }

    # Refrain patterns for specific meters (Jyotis, Mahāpaṅkti)
    REFRAIN_PATTERNS = {
        'ज्योतिस्': ['सजोषसा', 'उषसा सूर्येण', 'सूर्येण च'],
        'महापङ्क्ति': ['नभंतामन्यके समे', 'अन्यके समे'],
    }

    # Syllable count ranges based on actual Rigveda data distribution
    # Calibrated to achieve ~95% coverage per meter type
    # Note: Ranges are designed to minimize overlaps while maximizing coverage
    # Based on empirical analysis of Rigveda syllable distributions
    # IMPORTANT: Our syllabification tends to count +1 syllable vs the CSV data (20.8% of cases)
    # Ranges account for this variance, with overlaps handled by peak distance scoring
    #
    # Key empirical boundaries from Rigveda data:
    #   - Dvipadā Virāṭ: peak at 19-20, mostly 18-22
    #   - Dvipadā Triṣṭubh: peak at 21-22
    #   - Gayatri: peak at 24, mostly 22-24 (99% ≤24)
    #   - Usnik: peak at 27-28, mostly 25-29
    #   - Trishtup: peak at 43, mostly 40-44 (but we compute +1, so 41-45)
    #   - Jagati: peak at 47, mostly 45-48 (but we compute +1, so 46-49)
    #   - Atyashti: peak at 66, range 61-68
    #   - Brhati: peak at 35, range 30-45
    VEDIC_METER_RANGES = {
        # Dvipadā (half-verse) meters - get priority at low syllable counts
        'द्विपदा विराट्': (17, 21),  # Peak 19-20, data: 18=6, 19=27, 20=29, 21=4
        'द्विपदा त्रिष्टुभ्': (20, 23),  # Peak 21-22
        # Standard meters
        'विराट्': (18, 44),  # Virāṭ BIMODAL: 18-22 overlaps Dvipadā + 30-44 (extended)
        'गायत्री': (19, 26),  # Peak 24, range 19-26 (data: 83% at 21 becomes Gāyatrī!)
        'उष्णिक्': (25, 30),  # Peak 28, overlap with Gayatri at 25-26 handled by peak
        'ककुभ्': (25, 29),  # Peak 26-28, 3-pada structure (8+8+12) distinguishes
        'अनुष्टुभ्': (29, 34),  # Peak 31
        'बृहती': (33, 41),  # Peak 35, expanded range from data (33-40 common)
        'प्रगाथ': (33, 43),  # Composite meter
        'पङ्क्ति': (36, 42),  # Peak 39, overlap with Trishtup at 40-41
        'ज्योतिस्': (39, 45),  # Peak 42, refrain pattern distinguishes
        'त्रिष्टुभ्': (40, 46),  # Peak 43, overlap with Pankti at 40-41, with Jagati at 45-46
        'महापङ्क्ति': (44, 50),  # Peak 47 from data
        'जगती': (45, 53),  # Peak 47, overlap with Trishtup at 45-46 handled by peak distance
        'अतिजगती': (50, 55),
        'शक्वरी': (51, 59),  # Peak 53 from data
        'अतिशक्वरी': (57, 63),  # Peak 58 from data
        'अत्यष्टि': (61, 69),  # Peak 66, range 61-68 from data (with +1)
        'अष्टि': (61, 66),  # Peak 62 from data
        'धृति': (64, 72),
        'अतिधृति': (70, 75),
        'कृति': (74, 79),
    }

    # Empirical peak syllable counts from Rigveda data analysis
    # These are the actual MODE (most common) syllable counts, not theoretical
    # Note: Our syllabification tends to count +1 syllable vs CSV data
    VEDIC_METER_PEAKS = {
        # Dvipadā meters
        'द्विपदा विराट्': 20,  # Data: 19=27, 20=29 - using 20 as peak (more common)
        'द्विपदा त्रिष्टुभ्': 21,  # Data: 21=4, 22=3
        # Standard meters
        'विराट्': 20,  # Virāṭ is BIMODAL at 19-20 (Dvipadā-like) + 30-44 (extended)
        'गायत्री': 24,  # 48% at 24, 32% at 23
        'उष्णिक्': 28,  # 37% at 28, 35% at 27
        'ककुभ्': 26,  # Data: 26=4, 28=3 - 8+8+12 structure (unequal padas)
        'अनुष्टुभ्': 31,  # 36% at 31, 32% at 32 (note: theoretical is 32!)
        'बृहती': 35,  # Peak at 35 from data (64 verses)
        'प्रगाथ': 39,  # Composite, peaks at 39 (90 verses)
        'पङ्क्ति': 39,  # Peak at 39 based on data
        'ज्योतिस्': 42,  # Peak at 41-42, has refrain
        'त्रिष्टुभ्': 43,  # 31% at 43, 28% at 44
        'महापङ्क्ति': 47,  # Peak at 47 from data (17 verses)
        'जगती': 47,  # 32% at 47, 25% at 48
        'अतिजगती': 52,
        'शक्वरी': 53,  # Peak at 53 from data
        'अतिशक्वरी': 58,  # Peak at 58 from data
        'अत्यष्टि': 66,  # Peak at 66 from data (22 verses) - UPDATED!
        'अष्टि': 62,  # Peak at 62 from data
        'धृति': 68,
        'अतिधृति': 72,
        'कृति': 76,
    }

    # Tolerance for syllable count matching
    SYLLABLE_TOLERANCE = 6
