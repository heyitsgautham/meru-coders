#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adapter to test chanda_gpt.py against existing test suites.

This wraps the functional API of chanda_gpt.py to match the Chanda class interface
expected by test_csv_accuracy.py, test_rigveda_validation.py, and test_matching_chandas_dataset.py
"""

from reference.alternative_implementations import chanda_gpt


class ChandaGPTAdapter:
    """
    Adapter class to make chanda_gpt.py compatible with existing test infrastructure.

    Maps the functional API of chanda_gpt.identify_from_text() to the Chanda class interface.
    """

    def __init__(self, data_path=None):
        """Initialize adapter (data_path not used by chanda_gpt)"""
        self.data_path = data_path

    def identify_line(self, text):
        """
        Identify meter for a single line.

        Maps chanda_gpt output to the format expected by tests:
        - found: bool
        - display_chanda_primary: str (primary meter name)
        - display_chanda: str (full display string)
        - chanda: list of tuples [(meter_name, confidence)]
        - display_lg: list of 'L'/'G' strings
        - display_length: int (syllable count)
        - display_matra: int (matra count)
        - fuzzy: list of fuzzy matches
        """
        result = chanda_gpt.identify_from_text(text, variant='lenient')

        meter = result.get('identified_meter')
        confidence = result.get('confidence', 0.0)

        # Map meter names from English to Devanagari
        meter_map = {
            'Gayatri': 'गायत्री',
            'Ushnih': 'उष्णिक्',
            'Anushtubh': 'अनुष्टुभ्',
            'Brihati': 'बृहती',
            'Pankti': 'पङ्क्ति',
            'Trishtubh': 'त्रिष्टुभ्',
            'Jagati': 'जगती',
            'Nicrt_Gayatri': 'निचृद्गायत्री',
            'Bhurik_Gayatri': 'भुरिग्गायत्री',
            'Nicrt_Trishtubh': 'निचृत् त्रिष्टुभ्',
            'Virat_Trishtubh': 'विराट् त्रिष्टुभ्',
            'Nicrt_Jagati': 'निचृत् जगती',
        }

        meter_devanagari = meter_map.get(meter, meter) if meter else None

        # Convert L/G pattern to list of strings
        lg_pattern = result.get('lg_pattern', [])

        return {
            'found': meter is not None,
            'display_chanda_primary': meter_devanagari or '',
            'display_chanda': meter_devanagari or '',
            'chanda': [(meter_devanagari, confidence)] if meter_devanagari else [],
            'display_lg': lg_pattern,
            'display_length': result.get('syllable_count', 0),
            'display_matra': result.get('matra_count', 0),
            'fuzzy': [],  # chanda_gpt doesn't provide fuzzy matches
            'display_syllables': result.get('syllables', []),
        }

    def identify_from_text(self, text, verse=False):
        """
        Identify meter from text (single line or verse).

        Returns format compatible with test_csv_accuracy.py
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        if verse and len(lines) > 1:
            # Verse-level analysis
            full_text = ' '.join(lines)
            result = chanda_gpt.identify_from_text(full_text, variant='lenient')

            meter = result.get('identified_meter')
            confidence = result.get('confidence', 0.0)

            meter_map = {
                'Gayatri': 'गायत्री',
                'Ushnih': 'उष्णिक्',
                'Anushtubh': 'अनुष्टुभ्',
                'Brihati': 'बृहती',
                'Pankti': 'पङ्क्ति',
                'Trishtubh': 'त्रिष्टुभ्',
                'Jagati': 'जगती',
                'Nicrt_Gayatri': 'निचृद्गायत्री',
                'Bhurik_Gayatri': 'भुरिग्गायत्री',
                'Nicrt_Trishtubh': 'निचृत् त्रिष्टुभ्',
                'Virat_Trishtubh': 'विराट् त्रिष्टुभ्',
                'Nicrt_Jagati': 'निचृत् जगती',
            }

            meter_devanagari = meter_map.get(meter, meter) if meter else None

            return {'result': {'verse': [{'chanda': [[meter_devanagari, confidence]] if meter_devanagari else []}]}}
        else:
            # Line-by-line analysis
            line_results = []
            for line in lines:
                line_result = self.identify_line(line)
                line_results.append({'line': line, 'result': line_result})

            return {'result': {'line': line_results}}

    def identify_verse_holistically(self, lines):
        """
        Holistic verse identification (used by test_matching_chandas_dataset.py)
        """
        full_text = ' '.join(lines)
        result = chanda_gpt.identify_from_text(full_text, variant='lenient')

        meter = result.get('identified_meter')

        meter_map = {
            'Gayatri': 'गायत्री',
            'Ushnih': 'उष्णिक्',
            'Anushtubh': 'अनुष्टुभ्',
            'Brihati': 'बृहती',
            'Pankti': 'पङ्क्ति',
            'Trishtubh': 'त्रिष्टुभ्',
            'Jagati': 'जगती',
            'Nicrt_Gayatri': 'निचृद्गायत्री',
            'Bhurik_Gayatri': 'भुरिग्गायत्री',
            'Nicrt_Trishtubh': 'निचृत् त्रिष्टुभ्',
            'Virat_Trishtubh': 'विराट् त्रिष्टुभ्',
            'Nicrt_Jagati': 'निचृत् जगती',
        }

        meter_devanagari = meter_map.get(meter, meter) if meter else None

        return {'found': meter is not None, 'meter': meter_devanagari or ''}

    def _identify_vedic_mode(self, text):
        """
        Vedic mode identification (used by test_rigveda_validation.py)
        """
        result = chanda_gpt.identify_from_text(text, variant='lenient')

        meter = result.get('identified_meter')

        meter_map = {
            'Gayatri': 'गायत्री',
            'Ushnih': 'उष्णिक्',
            'Anushtubh': 'अनुष्टुभ्',
            'Brihati': 'बृहती',
            'Pankti': 'पङ्क्ति',
            'Trishtubh': 'त्रिष्टुभ्',
            'Jagati': 'जगती',
            'Nicrt_Gayatri': 'निचृद्गायत्री',
            'Bhurik_Gayatri': 'भुरिग्गायत्री',
            'Nicrt_Trishtubh': 'निचृत् त्रिष्टुभ्',
            'Virat_Trishtubh': 'विराट् त्रिष्टुभ्',
            'Nicrt_Jagati': 'निचृत् जगती',
        }

        meter_devanagari = meter_map.get(meter, meter) if meter else None

        return {'meter': meter_devanagari}
