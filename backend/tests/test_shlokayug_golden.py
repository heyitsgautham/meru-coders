#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for validating Chanda engine against ShlokaYug Golden Dataset.
Extracted from repos/ShlokaYug/Web-App/src/data/enhancedDummyData.ts and dummyData.ts

NOTE: The `CHANDAS_DATABASE` in ShlokaYug contains SIGNIFICANT ERRORS.
Many famous Anushtubh verses (Gita 4.7, Gita 18.78, Gita 6.5) are misclassified 
as Jagati, Brihati, or Pankti.
Rigveda 1.1.1 (Gayatri) is misclassified as Trishtubh.
Rigveda 1.189.1 (Trishtubh) is misclassified as Ushnik.

This test suite ONLY includes the verified correct examples, primarily from `ENHANCED_SHLOKAS`.
"""

import unittest

import pytest

from backend.config import settings
from backend.core.chanda import Chanda


class TestShlokaYugGolden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Chanda(str(settings.DATA_DIR))

    def check_meter(self, expected_meter, text, is_verse=False):
        if is_verse:
            # Use identify_from_text for full verses
            result_dict = self.c.identify_from_text(text, verse=True)
            line_results = result_dict['result']['line']
            verse_results = result_dict['result']['verse']

            # Check verse results first
            found_meters = []
            if verse_results:
                for vr in verse_results:
                    if vr['chanda']:
                        # vr['chanda'] is (['Meter1', 'Meter2'], score)
                        found_meters.extend(vr['chanda'][0])

            # Also check line results as fallback
            for lr in line_results:
                if lr['result']['found']:
                    found_meters.append(lr['result']['display_chanda'])

            found_meter_str = " / ".join(found_meters)
        else:
            # Use identify_line for single lines
            result = self.c.identify_line(text)
            found_meter_str = result['display_chanda']

        # Normalize for comparison
        expected_variants = [expected_meter]
        if expected_meter == 'Anushtubh':
            expected_variants.extend(['Anushtup', 'Śloka', 'Sloka', 'अनुष्टुभ्', 'अनुष्टुप्'])
        elif expected_meter == 'Gayatri':
            expected_variants.extend(['Gāyatrī', 'Gayatri', 'गायत्री'])
        elif expected_meter == 'Trishtubh':
            expected_variants.extend(['Triṣṭubh', 'Trishtubh', 'त्रिष्टुभ्'])
        elif expected_meter == 'Jagati':
            expected_variants.extend(['Jagatī', 'Jagati', 'जगती'])

        match_found = False
        if found_meter_str:
            for variant in expected_variants:
                if variant.lower() in found_meter_str.lower():
                    match_found = True
                    break

        self.assertTrue(match_found, f"Expected {expected_meter} (or variants {expected_variants}), but found '{found_meter_str}' for text: {text[:50]}...")

    # --- VERIFIED CORRECT EXAMPLES ---

    def test_anushtubh_gita_2_47(self):
        # "You have a right to perform your prescribed duty..."
        text = 'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन। मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥'
        self.check_meter('Anushtubh', text, is_verse=True)

    def test_gayatri_mantra(self):
        # "Om Bhur Bhuvah Svah..."
        # Note: The full text includes Vyahritis (Om Bhur Bhuvah Svah) which adds syllables.
        # The core Gayatri mantra is 24 syllables.
        # We test the core mantra here to verify Gayatri detection.
        text = 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्॥'
        self.check_meter('Gayatri', text, is_verse=True)

    def test_anushtubh_ishavasya_1(self):
        # "All this is pervaded by the Divine..."
        text = 'ईशावास्यमिदं सर्वं यत्किञ्च जगत्यां जगत्। तेन त्यक्तेन भुञ्जीथा मा गृधः कस्यस्विद्धनम्॥'
        self.check_meter('Anushtubh', text, is_verse=True)

    def test_anushtubh_gita_1_1(self):
        # "Dharmakshetre Kurukshetre..."
        text = 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः'
        self.check_meter('Anushtubh', text, is_verse=False)

    # --- CORRECTED EXAMPLES (Source data was wrong, but text is valid) ---

    @pytest.mark.xfail(
        strict=True,
        reason="Two 8-syllable padas are also an Anushtubh half-verse; "
        "only the full three-pada verse identifies as Gayatri",
    )
    def test_gayatri_rigveda_1_1_1(self):
        # ShlokaYug labeled this Trishtubh, but it is Gayatri
        text = 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम्'
        self.check_meter('Gayatri', text, is_verse=False)

    def test_anushtubh_gita_18_78(self):
        # ShlokaYug labeled this Jagati, but it is Anushtubh
        text = 'यत्र योगेश्वरः कृष्णो यत्र पार्थो धनुर्धरः'
        self.check_meter('Anushtubh', text, is_verse=False)

    def test_anushtubh_gita_6_5(self):
        # ShlokaYug labeled this Brihati, but it is Anushtubh
        text = 'उद्धरेदात्मनात्मानं नात्मानमवसादयेत्'
        self.check_meter('Anushtubh', text, is_verse=False)

    def test_anushtubh_gita_4_7(self):
        # ShlokaYug labeled this Pankti, but it is Anushtubh
        text = 'यदा यदा हि धर्मस्य ग्लानिर्भवति भारत'
        self.check_meter('Anushtubh', text, is_verse=False)

    def test_trishtubh_rigveda_1_189_1(self):
        # ShlokaYug labeled this Ushnik, but it is Trishtubh
        text = 'अग्ने नय सुपथा राये अस्मान्'
        self.check_meter('Trishtubh', text, is_verse=False)

    # --- ADDITIONAL CORRECTED EXAMPLES FROM SHLOKAYUG DATABASE ---

    def test_gayatri_rigveda_1_1_1_full(self):
        # ShlokaYug labeled this Trishtubh, but it is Gayatri
        text = 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम् होतारं रत्नधातमम्'
        self.check_meter('Gayatri', text, is_verse=True)

    def test_anushtubh_gita_18_78_full(self):
        # ShlokaYug labeled this Jagati, but it is Anushtubh
        text = 'यत्र योगेश्वरः कृष्णो यत्र पार्थो धनुर्धरः तत्र श्रीर्विजयो भूतिर्ध्रुवा नीतिर्मतिर्मम'
        self.check_meter('Anushtubh', text, is_verse=True)

    def test_anushtubh_gita_6_5_full(self):
        # ShlokaYug labeled this Brihati, but it is Anushtubh
        text = 'उद्धरेदात्मनात्मानं नात्मानमवसादयेत् आत्मैव ह्यात्मनो बन्धुरात्मैव रिपुरात्मनः'
        self.check_meter('Anushtubh', text, is_verse=True)

    def test_anushtubh_gita_4_7_full(self):
        # ShlokaYug labeled this Pankti, but it is Anushtubh
        text = 'यदा यदा हि धर्मस्य ग्लानिर्भवति भारत अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम्'
        self.check_meter('Anushtubh', text, is_verse=True)

    def test_trishtubh_rigveda_1_189_1_full(self):
        # ShlokaYug labeled this Ushnik, but it is Trishtubh
        text = 'अग्ने नय सुपथा राये अस्मान् विश्वानि देव वयुनानि विद्वान्'
        self.check_meter('Trishtubh', text, is_verse=True)

    # --- DAILY QUOTES (Partial Verses) ---

    def test_quote_yoga(self):
        # "Yoga is skill in action" - Gita 2.50 (Anushtubh pada)
        text = 'योगः कर्मसु कौशलम्'
        self.check_meter('Anushtubh', text, is_verse=False)

    def test_quote_ahimsa(self):
        # "Ahimsa Paramo Dharmah" - Mahabharata (Anushtubh pada)
        text = 'अहिंसा परमो धर्मः'
        self.check_meter('Anushtubh', text, is_verse=False)


if __name__ == '__main__':
    unittest.main()
