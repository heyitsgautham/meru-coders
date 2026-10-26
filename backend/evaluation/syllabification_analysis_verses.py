"""The verses syllabification_analysis.py syllabifies with each method."""

TEST_VERSES = [
    # =========================================================================
    # SIMPLE VERSES (Short, clear words)
    # =========================================================================
    {
        'id': 'Simple-1',
        'text': 'राम',
        'expected_syllables': 2,
        'expected_lg': 'GL',
        'category': 'simple',
        'notes': 'Simple 2-syllable word',
    },
    {
        'id': 'Simple-2',
        'text': 'नमस्ते',
        'expected_syllables': 3,
        'expected_lg': 'LGG',
        'category': 'simple',
        'notes': 'Common greeting',
    },
    {
        'id': 'Simple-3',
        'text': 'भगवान्',
        'expected_syllables': 3,
        'expected_lg': 'LLG',
        'category': 'simple',
        'notes': 'Word ending in halanta',
    },
    {
        'id': 'Simple-4',
        'text': 'ओम्',
        'expected_syllables': 1,
        'expected_lg': 'G',
        'category': 'simple',
        'notes': 'Single long syllable with anusvara',
    },
    # =========================================================================
    # GAYATRI (24 syllables = 3×8)
    # =========================================================================
    {
        'id': 'Gayatri-1',
        'text': 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि । धियो यो नः प्रचोदयात् ॥',
        'expected_syllables': 24,
        'expected_lg': 'GGLLGLGGGGLGGLGLLGLGLGG',  # May need verification
        'category': 'gayatri',
        'notes': 'Famous Gayatri Mantra',
    },
    {
        'id': 'Gayatri-2',
        'text': 'अग्निमीळे पुरोहितं यज्ञस्य देवं ऋत्विजम् । होतारं रत्नधातमम् ॥',
        'expected_syllables': 24,
        'expected_lg': None,  # Need to verify
        'category': 'gayatri',
        'notes': 'RV 1.1.1',
    },
    # =========================================================================
    # ANUSHTUBH (32 syllables = 4×8)
    # =========================================================================
    {
        'id': 'Anushtubh-1',
        'text': 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः',
        'expected_syllables': 16,
        'expected_lg': 'GLGGLGGLLLGGLLLL',
        'category': 'anushtubh',
        'notes': 'BG 1.1 first half',
    },
    {
        'id': 'Anushtubh-2',
        'text': 'सहस्रशीर्षा पुरुषः सहस्राक्षः सहस्रपात्',
        'expected_syllables': 16,
        'expected_lg': 'LLGGGLLGLLGGLLLG',
        'category': 'anushtubh',
        'notes': 'Purusha Sukta first half',
    },
    # =========================================================================
    # TRISHTUBH (44 syllables = 4×11) - MOST PROBLEMATIC
    # =========================================================================
    {
        'id': 'Trishtubh-1',
        'text': 'इन्द्रस्य नु वीर्याणि प्र वोचं यानि चकार प्रथमानि वज्री',
        'expected_syllables': 22,
        'expected_lg': 'GGLLLGGLLLGGGLLGLGLGG',
        'category': 'trishtubh',
        'notes': 'RV 1.32.1 first half (pada 1-2)',
    },
    {
        'id': 'Trishtubh-2',
        'text': 'अहन्नहिमन्वपस्ततर्द प्र वक्षणा अभिनत्पर्वतानाम्',
        'expected_syllables': 22,
        'expected_lg': 'LGLLGLGLGLGGLGLLGLGGG',
        'category': 'trishtubh',
        'notes': 'RV 1.32.1 second half (pada 3-4)',
    },
    {
        'id': 'Trishtubh-3',
        'text': 'नासदासीन्नो सदासीत्तदानीं नासीद्रजो नो व्योमा परो यत्',
        'expected_syllables': 22,
        'expected_lg': None,
        'category': 'trishtubh',
        'notes': 'Nasadiya Sukta first half',
    },
    # =========================================================================
    # JAGATI (48 syllables = 4×12) - SEVERELY UNDERCOUNTED
    # =========================================================================
    {
        'id': 'Jagati-1',
        'text': 'इन्द्रं मित्रं वरुणमग्निमाहुरथो दिव्यः स सुपर्णो गरुत्मान्',
        'expected_syllables': 24,
        'expected_lg': None,
        'category': 'jagati',
        'notes': 'RV 1.164.46 first half (pada 1-2)',
    },
    {
        'id': 'Jagati-2',
        'text': 'एकं सद्विप्रा बहुधा वदन्त्यग्निं यमं मातरिश्वानमाहुः',
        'expected_syllables': 24,
        'expected_lg': None,
        'category': 'jagati',
        'notes': 'RV 1.164.46 second half (pada 3-4)',
    },
    {
        'id': 'Jagati-3',
        'text': 'द्वा सुपर्णा सयुजा सखाया समानं वृक्षं परिषस्वजाते',
        'expected_syllables': 24,
        'expected_lg': None,
        'category': 'jagati',
        'notes': 'RV 1.164.20 first half',
    },
    # =========================================================================
    # COMPLEX CONJUNCTS - Testing specific problematic patterns
    # =========================================================================
    {
        'id': 'Conjunct-1',
        'text': 'क्षत्रियः',
        'expected_syllables': 3,
        'expected_lg': 'GLG',
        'category': 'conjunct',
        'notes': 'क्ष conjunct',
    },
    {
        'id': 'Conjunct-2',
        'text': 'ज्ञानम्',
        'expected_syllables': 2,
        'expected_lg': 'GG',
        'category': 'conjunct',
        'notes': 'ज्ञ conjunct',
    },
    {
        'id': 'Conjunct-3',
        'text': 'स्वर्गः',
        'expected_syllables': 2,
        'expected_lg': 'GG',
        'category': 'conjunct',
        'notes': 'स्व conjunct with visarga',
    },
    {
        'id': 'Conjunct-4',
        'text': 'प्रज्ञा',
        'expected_syllables': 2,
        'expected_lg': 'GG',
        'category': 'conjunct',
        'notes': 'Double conjunct प्र + ज्ञ',
    },
    {
        'id': 'Conjunct-5',
        'text': 'त्र्यम्बकम्',
        'expected_syllables': 3,
        'expected_lg': 'GGG',
        'category': 'conjunct',
        'notes': 'त्र्य complex conjunct',
    },
    # =========================================================================
    # VEDIC SPECIFIC - Special characters
    # =========================================================================
    {
        'id': 'Vedic-1',
        'text': 'अग्निः',
        'expected_syllables': 2,
        'expected_lg': 'GG',
        'category': 'vedic',
        'notes': 'Visarga ending',
    },
    {
        'id': 'Vedic-2',
        'text': 'देवाः',
        'expected_syllables': 2,
        'expected_lg': 'GG',
        'category': 'vedic',
        'notes': 'Long vowel + visarga',
    },
]
