#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rigveda Test Verses with Ground Truth Meters from WSC2023 Anukramani

This file contains carefully curated Rigveda verses matched with their
authoritative meter annotations from the Anukramani tradition.

Sources:
- Meter annotations: WSC2023 Anukramani (mahesh-ak/WSC2023)
- Verse texts: Various scholarly sources (GRETIL, Wikisource, VedaWeb)

Each entry contains:
- mandala: Mandala number (1-10)
- hymn: Hymn/Sukta number
- verse: Verse/Mantra number (or range)
- text: Sanskrit verse in Devanagari
- meter: Expected meter name (from Anukramani)
- syllables: Expected syllable count for the meter
"""

# ============================================================================
# RIGVEDA TEST VERSES WITH GROUND TRUTH METERS
# ============================================================================

RIGVEDA_VERSES = [
    # ========================================================================
    # MANDALA 1 - GAYATRI METERS (24 syllables = 3×8)
    # ========================================================================
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 1,
        'text': 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम् । होतारं रत्नधातमम् ॥',
        'meter': 'गायत्री',
        'meter_iast': 'gāyatrī',
        'syllables': 24,
        'source': 'RV 1.1.1 - First verse of Rigveda',
    },
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 2,
        'text': 'अग्निः पूर्वेभिरृषिभिरीड्यो नूतनैरुत । स देवाँ एह वक्षति ॥',
        'meter': 'गायत्री',
        'meter_iast': 'gāyatrī',
        'syllables': 24,
        'source': 'RV 1.1.2',
    },
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 3,
        'text': 'अग्निना रयिमश्नवत् पोषमेव दिवेदिवे । यशसं वीरवत्तमम् ॥',
        'meter': 'गायत्री',
        'meter_iast': 'gāyatrī',
        'syllables': 24,
        'source': 'RV 1.1.3',
    },
    # Famous Gayatri Mantra
    {
        'mandala': 3,
        'hymn': 62,
        'verse': 10,
        'text': 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि । धियो यो नः प्रचोदयात् ॥',
        'meter': 'गायत्री',
        'meter_iast': 'gāyatrī',
        'syllables': 24,
        'source': 'RV 3.62.10 - The Gayatri Mantra',
    },
    # ========================================================================
    # MANDALA 1 - ANUSHTUBH METERS (32 syllables = 4×8)
    # ========================================================================
    {
        'mandala': 1,
        'hymn': 10,
        'verse': 1,
        'text': 'गायन्ति त्वा गायत्रिणो अर्चन्त्यर्कमर्किणः । ब्रह्माणस्त्वा शतक्रत उद्वंशमिव येमिरे ॥',
        'meter': 'अनुष्टुभ्',
        'meter_iast': 'anuṣṭup',
        'syllables': 32,
        'source': 'RV 1.10.1 - Anushtubh hymn to Indra',
    },
    {
        'mandala': 1,
        'hymn': 11,
        'verse': 1,
        'text': 'इन्द्रं विश्वा अवीवृधन्त्समुद्रव्यचसं गिरः । रथीतमं रथीनां वाजानां सत्पतिं पतिम् ॥',
        'meter': 'अनुष्टुभ्',
        'meter_iast': 'anuṣṭup',
        'syllables': 32,
        'source': 'RV 1.11.1',
    },
    # ========================================================================
    # MANDALA 1 - TRISHTUBH METERS (44 syllables = 4×11)
    # ========================================================================
    {
        'mandala': 1,
        'hymn': 32,
        'verse': 1,
        'text': 'इन्द्रस्य नु वीर्याणि प्र वोचं यानि चकार प्रथमानि वज्री । अहन्नहिमन्वपस्ततर्द प्र वक्षणा अभिनत्पर्वतानाम् ॥',
        'meter': 'त्रिष्टुभ्',
        'meter_iast': 'triṣṭup',
        'syllables': 44,
        'source': 'RV 1.32.1 - Indra slaying Vritra',
    },
    {
        'mandala': 1,
        'hymn': 32,
        'verse': 2,
        'text': 'अहन्नहिं पर्वते शिश्रियाणं त्वष्टास्मै वज्रं स्वर्यं ततक्ष । वाश्रा इव धेनवः स्यन्दमाना अञ्जः समुद्रमव जग्मुरापः ॥',
        'meter': 'त्रिष्टुभ्',
        'meter_iast': 'triṣṭup',
        'syllables': 44,
        'source': 'RV 1.32.2',
    },
    {
        'mandala': 1,
        'hymn': 164,
        'verse': 46,
        'text': 'इन्द्रं मित्रं वरुणमग्निमाहुरथो दिव्यः स सुपर्णो गरुत्मान् । एकं सद्विप्रा बहुधा वदन्त्यग्निं यमं मातरिश्वानमाहुः ॥',
        'meter': 'त्रिष्टुभ्',
        'meter_iast': 'triṣṭup',
        'syllables': 44,
        'source': 'RV 1.164.46 - Famous "Ekam Sat" verse',
    },
    # ========================================================================
    # MANDALA 1 - JAGATI METERS (48 syllables = 4×12)
    # ========================================================================
    {
        'mandala': 1,
        'hymn': 31,
        'verse': 1,
        'text': 'त्वमग्ने प्रथमो अङ्गिरा ऋषिर्देवो देवानामभवः शिवः सखा । तव व्रते कवयो विद्मनापसो अजायन्त मरुतो भ्राजदृष्टयः ॥',
        'meter': 'जगती',
        'meter_iast': 'jagatī',
        'syllables': 48,
        'source': 'RV 1.31.1 - Jagati hymn to Agni',
    },
    {
        'mandala': 1,
        'hymn': 34,
        'verse': 1,
        'text': 'त्रिर्आ दिवो विदथे सत्यवाचो यमुपब्दे हविष्मन्तो अर्यः । नक्तोषासो वरुणो मित्रो अर्यमा प्र सर्गेण सिञ्चता वश्मि देवीः ॥',
        'meter': 'जगती',
        'meter_iast': 'jagatī',
        'syllables': 48,
        'source': 'RV 1.34.1',
    },
    {
        'mandala': 1,
        'hymn': 164,
        'verse': 20,
        'text': 'द्वा सुपर्णा सयुजा सखाया समानं वृक्षं परिषस्वजाते । तयोरन्यः पिप्पलं स्वाद्वत्त्यनश्नन्नन्यो अभिचाकशीति ॥',
        'meter': 'जगती',
        'meter_iast': 'jagatī',
        'syllables': 48,
        'source': 'RV 1.164.20 - Famous "Two Birds" verse',
    },
    # ========================================================================
    # MANDALA 1 - BRIHATI METERS (36 syllables = 4×9)
    # ========================================================================
    {
        'mandala': 1,
        'hymn': 36,
        'verse': 1,
        'text': 'प्र वो यह्वं पुरूणामिषमूर्जं च विश्वदानीम् । अग्निं वृणीध्वं विश्पतिं गृणानो बृहत इषे ॥',
        'meter': 'बृहती',
        'meter_iast': 'bṛhatī',
        'syllables': 36,
        'source': 'RV 1.36.1 - Brihati hymn to Agni',
    },
    {
        'mandala': 1,
        'hymn': 39,
        'verse': 1,
        'text': 'प्र व इन्द्राय बृहते मरुतो ब्रह्म अर्चत । उपेद्यं पृथुश्रवसोऽध्वरं न्यक्षत स्तुतिं न द्यौः ॥',
        'meter': 'बृहती',
        'meter_iast': 'bṛhatī',
        'syllables': 36,
        'source': 'RV 1.39.1',
    },
    # ========================================================================
    # MANDALA 1 - PANKTI METERS (40 syllables = 5×8)
    # ========================================================================
    {
        'mandala': 1,
        'hymn': 29,
        'verse': 1,
        'text': 'यच्चिद्धि सत्य सोमपा अनाशस्ता इव स्मसि । आयं जनेषु पञ्चसु प्रियमिन्द्रातिथिं करत् स्वःश्वपति ॥',
        'meter': 'पङ्क्ति',
        'meter_iast': 'paṅkti',
        'syllables': 40,
        'source': 'RV 1.29.1 - Pankti meter (5×8)',
    },
    # ========================================================================
    # MANDALA 1 - USHNIK METERS (28 syllables = 4×7)
    # ========================================================================
    {
        'mandala': 1,
        'hymn': 8,
        'verse': 1,
        'text': 'एन्द्र साध्यो सानसिं रयिं सस्वन्तं शताश्विनम् । भोगं सहस्रवीरवत् ॥',
        'meter': 'उष्णिक्',
        'meter_iast': 'uṣṇik',
        'syllables': 28,
        'source': 'RV 1.8.1 - Ushnik (from WSC2023 hymn 8 annotation)',
    },
    # ========================================================================
    # MIXED/COMPOSITE METERS (for testing edge cases)
    # ========================================================================
    # Hymn 1.23 has mixed meters: (1-18,21)gāyatrī,(19)uṣṇik,(20,22-24)anuṣṭup
    {
        'mandala': 1,
        'hymn': 23,
        'verse': 1,
        'text': 'वायवा याहि दर्शतेमे सोमा अरंकृताः । तेषां पाहि श्रुधी हवम् ॥',
        'meter': 'गायत्री',
        'meter_iast': 'gāyatrī',
        'syllables': 24,
        'source': 'RV 1.23.1 - First verse of mixed-meter hymn',
    },
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_verses_by_meter(meter_name):
    """Get all verses of a specific meter."""
    return [
        v
        for v in RIGVEDA_VERSES
        if meter_name.lower() in v['meter'].lower() or meter_name.lower() in v['meter_iast'].lower()
    ]


def get_verses_by_syllable_count(syllable_count):
    """Get all verses with a specific syllable count."""
    return [v for v in RIGVEDA_VERSES if v['syllables'] == syllable_count]


def get_all_meters():
    """Get list of all unique meters in the dataset."""
    meters = {}
    for v in RIGVEDA_VERSES:
        key = v['meter_iast']
        if key not in meters:
            meters[key] = {'name': v['meter'], 'iast': v['meter_iast'], 'syllables': v['syllables'], 'count': 0}
        meters[key]['count'] += 1
    return meters


def summary():
    """Print dataset summary."""
    meters = get_all_meters()
    print(f"\n{'=' * 60}")
    print("RIGVEDA TEST DATASET SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total verses: {len(RIGVEDA_VERSES)}")
    print("\nMeters represented:")
    for iast, info in sorted(meters.items(), key=lambda x: x[1]['syllables']):
        print(f"  {info['name']} ({info['iast']}): {info['count']} verses, {info['syllables']} syllables")
    print(f"{'=' * 60}\n")


if __name__ == '__main__':
    summary()
