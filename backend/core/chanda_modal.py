#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EXPERIMENTAL: Modal Chanda Identifier

This version allows the user to specify whether the input is:
- 'vedic': Uses syllable-count based identification (Gāyatrī, Triṣṭubh, Jagatī, etc.)
- 'classical': Uses L-G pattern matching (Vasantatilakā, Mandākrāntā, etc.)
- 'auto': Tries to auto-detect based on text characteristics

Author: Meru Coders Team (SIH 2025)
"""

import os

# Import the base Chanda class
from core.chanda import Chanda


class ChandaModal(Chanda):
    """
    Modal Chanda Identifier - extends base Chanda with mode selection.
    
    Modes:
        'vedic': Prioritizes syllable-count based Vedic meter identification
        'classical': Uses traditional L-G pattern matching for classical meters
        'auto': Attempts to auto-detect the appropriate mode
    """

    # Vedic meter definitions by syllable count
    VEDIC_METERS = {
        24: {'name': 'गायत्री', 'name_en': 'Gāyatrī', 'padas': 3, 'per_pada': 8},
        28: {'name': 'उष्णिक्', 'name_en': 'Uṣṇik', 'padas': 4, 'per_pada': 7},
        32: {'name': 'अनुष्टुभ्', 'name_en': 'Anuṣṭubh', 'padas': 4, 'per_pada': 8},
        36: {'name': 'बृहती', 'name_en': 'Bṛhatī', 'padas': 4, 'per_pada': 9},
        40: {'name': 'पङ्क्ति', 'name_en': 'Paṅkti', 'padas': 5, 'per_pada': 8},
        44: {'name': 'त्रिष्टुभ्', 'name_en': 'Triṣṭubh', 'padas': 4, 'per_pada': 11},
        48: {'name': 'जगती', 'name_en': 'Jagatī', 'padas': 4, 'per_pada': 12},
    }

    # Syllable count ranges for fuzzy matching
    # Key insight: Sanskrit syllabification consistently UNDERCOUNTS by 2-6 syllables
    # Ranges are designed to be NON-OVERLAPPING where possible
    # When overlap is unavoidable, prefer higher meters (due to undercounting)
    VEDIC_METER_RANGES = {
        'गायत्री': (19, 25),      # 24: target 24, allow 19-25
        'उष्णिक्': (25, 29),      # 28: target 28, allow 25-29 (gap from Gayatri)
        'अनुष्टुभ्': (29, 34),    # 32: target 32, allow 29-34
        'बृहती': (34, 38),        # 36: target 36, allow 34-38
        'पङ्क्ति': (38, 41),      # 40: target 40, allow 38-41 (NARROW - transition zone)
        'त्रिष्टुभ्': (41, 46),   # 44: target 44, allow 41-46 (KEY: 42 → Triṣṭubh)
        'जगती': (46, 52),         # 48: target 48, allow 46-52
    }

    # Tolerance for syllable count matching (Vedic texts have variations)
    # INCREASED to 5 for better Jagatī matching (severe undercounting)
    SYLLABLE_TOLERANCE = 5

    def __init__(self, data_path, **kwargs):
        """Initialize with base Chanda functionality."""
        super().__init__(data_path, **kwargs)

    def identify_modal(self, text, mode='auto', verse=True, fuzzy=False):
        """
        Identify meter with explicit mode selection.
        
        Parameters
        ----------
        text : str
            The Sanskrit verse text to identify
        mode : str
            'vedic': Use syllable-count based identification
            'classical': Use L-G pattern matching
            'auto': Auto-detect based on text analysis
        verse : bool
            Treat input as verse (multiple lines = one verse)
        fuzzy : bool
            Enable fuzzy matching for classical mode
            
        Returns
        -------
        dict
            Identification results with meter name, confidence, and details
        """

        if mode == 'vedic':
            return self._identify_vedic(text, verse)
        elif mode == 'classical':
            return self._identify_classical(text, verse, fuzzy)
        elif mode == 'auto':
            return self._identify_auto(text, verse, fuzzy)
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'vedic', 'classical', or 'auto'")

    def _identify_vedic(self, text, verse=True):
        """
        Identify Vedic meter by syllable count.
        
        Vedic meters are defined by total syllable count, not L-G pattern.
        """
        result = {
            'mode': 'vedic',
            'input': text,
            'meter': None,
            'meter_en': None,
            'confidence': 0.0,
            'syllable_count': 0,
            'expected_syllables': None,
            'structure': None,
            'lines': [],
            'all_syllables': [],
            'all_lg': [],
            'debug': {}
        }

        # Clean and split text into lines
        lines = [ln.strip() for ln in text.replace('॥', '।').split('।') if ln.strip()]
        if not lines:
            lines = [ln.strip() for ln in text.split('\n') if ln.strip()]

        total_syllables = 0
        line_details = []
        all_syllables = []
        all_lg = []

        for line in lines:
            # Remove punctuation
            clean_line = line.replace('।', '').replace('॥', '').strip()
            if not clean_line:
                continue

            # Get syllables
            syllables = self.get_syllables_icu(clean_line)
            lg = [self.get_syllable_weight_icu(s) for s in syllables]

            line_details.append({
                'line': clean_line,
                'syllables': syllables,
                'syllable_count': len(syllables),
                'lg': lg,
                'lg_pattern': ''.join(lg)
            })

            total_syllables += len(syllables)
            all_syllables.extend(syllables)
            all_lg.extend(lg)

        result['lines'] = line_details
        result['syllable_count'] = total_syllables
        result['all_syllables'] = all_syllables
        result['all_lg'] = all_lg
        result['lg_pattern'] = ''.join(all_lg)

        # Find matching Vedic meter by syllable count
        # Use a candidate list to handle ties properly
        candidates = []

        for syl_count, meter_info in self.VEDIC_METERS.items():
            diff = abs(total_syllables - syl_count)
            if diff <= self.SYLLABLE_TOLERANCE:
                candidates.append((diff, syl_count, meter_info))

        # Sort by: 1) smallest diff, 2) HIGHEST syllable count (due to undercounting)
        candidates.sort(key=lambda x: (x[0], -x[1]))

        if candidates:
            best_diff, syl_count, meter_info = candidates[0]
            result['meter'] = meter_info['name']
            result['meter_en'] = meter_info['name_en']
            result['expected_syllables'] = syl_count
            result['structure'] = f"{meter_info['padas']} pādas × {meter_info['per_pada']} syllables"

            # Calculate confidence based on how close syllable count is
            if best_diff == 0:
                result['confidence'] = 1.0
            elif best_diff == 1:
                result['confidence'] = 0.9
            else:
                result['confidence'] = 0.8

            result['debug']['match_type'] = 'exact' if best_diff == 0 else f'fuzzy (±{best_diff})'
        else:
            # Try range-based matching (accounts for syllabification errors)
            range_match = self._find_meter_by_range(total_syllables)
            if range_match:
                result['meter'] = range_match['name']
                result['meter_en'] = range_match['name_en']
                result['expected_syllables'] = range_match['expected']
                result['structure'] = range_match['structure']
                result['confidence'] = range_match['confidence']
                result['debug']['match_type'] = 'range_based'
            else:
                result['debug']['match_type'] = 'no_match'
                result['debug']['closest'] = self._find_closest_vedic_meter(total_syllables)

        return result

    def _find_meter_by_range(self, syllable_count):
        """Find Vedic meter using syllable count ranges."""
        candidates = []

        for meter_name, (low, high) in self.VEDIC_METER_RANGES.items():
            if low <= syllable_count <= high:
                # Find the expected count for this meter
                expected = None
                for syl_count, info in self.VEDIC_METERS.items():
                    if info['name'] == meter_name:
                        expected = syl_count
                        structure = f"{info['padas']} pādas × {info['per_pada']} syllables"
                        name_en = info['name_en']
                        break

                if expected:
                    # Calculate confidence based on distance from expected
                    diff = abs(syllable_count - expected)
                    confidence = max(0.5, 1.0 - (diff * 0.05))  # -5% per syllable difference

                    candidates.append({
                        'name': meter_name,
                        'name_en': name_en,
                        'expected': expected,
                        'diff': diff,
                        'confidence': confidence,
                        'structure': structure
                    })

        if candidates:
            # IMPORTANT: Prefer higher syllable-count meters when tied
            # Because syllabification UNDERCOUNTS more than overcounts
            # So if we get 42 syllables, it's more likely Triṣṭubh (44) than Paṅkti (40)
            candidates.sort(key=lambda x: (-x['expected'], x['diff']))
            return candidates[0]

        return None

    def _find_closest_vedic_meter(self, syllable_count):
        """Find the closest Vedic meter by syllable count."""
        closest = None
        min_diff = float('inf')

        for syl_count, meter_info in self.VEDIC_METERS.items():
            diff = abs(syllable_count - syl_count)
            if diff < min_diff:
                min_diff = diff
                closest = {
                    'meter': meter_info['name'],
                    'meter_en': meter_info['name_en'],
                    'expected': syl_count,
                    'diff': diff
                }

        return closest

    def _identify_classical(self, text, verse=True, fuzzy=False):
        """
        Identify Classical meter by L-G pattern matching.
        
        Uses the base Chanda class's pattern matching logic.
        """
        # Use the parent class's identification
        base_result = self.identify_from_text(text, verse=verse, fuzzy=fuzzy)

        result = {
            'mode': 'classical',
            'input': text,
            'meter': None,
            'meter_en': None,
            'confidence': 0.0,
            'pattern': None,
            'lines': [],
            'debug': {}
        }

        # Extract the top result
        if base_result and base_result.get('result'):
            inner = base_result['result']

            # Try verse-level result
            verses = inner.get('verse', [])
            if verses and len(verses) > 0:
                first_verse = verses[0]
                chanda_list = first_verse.get('chanda', [])
                if chanda_list and len(chanda_list) > 0:
                    if isinstance(chanda_list[0], list):
                        result['meter'] = chanda_list[0][0] if chanda_list[0] else None
                    else:
                        result['meter'] = chanda_list[0]

                    # Get confidence from scores
                    scores = first_verse.get('scores', [])
                    if scores and len(scores) > 0:
                        result['confidence'] = scores[0][1] if len(scores[0]) > 1 else 0.5

            # Get line details
            for line_data in inner.get('line', []):
                line_result = line_data.get('result', {})
                result['lines'].append({
                    'line': line_data.get('line', ''),
                    'lg_pattern': ''.join(line_result.get('lg', [])),
                    'syllables': line_result.get('syllables', []),
                    'chanda': line_result.get('chanda', [])[:3]  # Top 3
                })

            result['debug']['raw_result'] = base_result

        return result

    def _identify_auto(self, text, verse=True, fuzzy=False):
        """
        Auto-detect whether text is Vedic or Classical and identify accordingly.
        
        Heuristics:
        1. Check syllable count - if matches Vedic meter exactly, likely Vedic
        2. Check for Vedic-specific markers (accent marks, rare characters)
        3. Check L-G pattern - if exact match found, likely Classical
        4. Default to whichever gives higher confidence
        """
        # Get both results
        vedic_result = self._identify_vedic(text, verse)
        classical_result = self._identify_classical(text, verse, fuzzy)

        # Decision logic
        vedic_conf = vedic_result.get('confidence', 0)
        classical_conf = classical_result.get('confidence', 0)

        # Boost Vedic if syllable count is exact match
        if vedic_result.get('debug', {}).get('match_type') == 'exact':
            vedic_conf += 0.3

        # Boost Classical if it found an exact pattern match
        if classical_conf >= 0.9:
            classical_conf += 0.2

        # Choose the better result
        if vedic_conf >= classical_conf and vedic_result.get('meter'):
            result = vedic_result
            result['auto_decision'] = 'vedic'
            result['auto_reason'] = f'Vedic confidence ({vedic_conf:.2f}) >= Classical ({classical_conf:.2f})'
        elif classical_result.get('meter'):
            result = classical_result
            result['auto_decision'] = 'classical'
            result['auto_reason'] = f'Classical confidence ({classical_conf:.2f}) > Vedic ({vedic_conf:.2f})'
        else:
            # No match found
            result = {
                'mode': 'auto',
                'auto_decision': 'unknown',
                'auto_reason': 'No confident match in either mode',
                'vedic_result': vedic_result,
                'classical_result': classical_result
            }

        return result


# =============================================================================
# STANDALONE TEST
# =============================================================================

def test_modal_identification():
    """Test the modal identification with sample verses."""

    print("=" * 70)
    print("   MODAL CHANDA IDENTIFIER - EXPERIMENT")
    print("=" * 70)

    # Initialize
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    chanda = ChandaModal(data_path)

    # Test cases
    test_cases = [
        {
            'name': 'Gayatri Mantra (Vedic)',
            'text': 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि ।\nधियो यो नः प्रचोदयात् ॥',
            'expected_meter': 'गायत्री',
            'expected_mode': 'vedic'
        },
        {
            'name': 'Agni Sukta RV 1.1.1 (Vedic)',
            'text': 'अग्निमीळे पुरोहितं यज्ञस्य देवं ऋत्विजम् ।\nहोतारं रत्नधातमम् ॥',
            'expected_meter': 'गायत्री',
            'expected_mode': 'vedic'
        },
        {
            'name': 'Nasadiya Sukta (Vedic Triṣṭubh)',
            'text': 'नासदासीन्नो सदासीत्तदानीं नासीद्रजो नो व्योमा परो यत् ।\nकिमावरीवः कुह कस्य शर्मन्नम्भः किमासीद्गहनं गभीरम् ॥',
            'expected_meter': 'त्रिष्टुभ्',
            'expected_mode': 'vedic'
        },
        {
            'name': 'Kalidasa Raghuvamsha (Classical)',
            'text': 'वागर्थाविव सम्पृक्तौ वागर्थप्रतिपत्तये ।\nजगतः पितरौ वन्दे पार्वतीपरमेश्वरौ ॥',
            'expected_meter': 'अनुष्टुभ्',
            'expected_mode': 'classical'
        },
    ]

    print("\n" + "-" * 70)
    print("Testing VEDIC mode:")
    print("-" * 70)

    for tc in test_cases[:3]:  # Vedic cases
        print(f"\n>>> {tc['name']}")
        print(f"    Text: {tc['text'][:50]}...")

        result = chanda.identify_modal(tc['text'], mode='vedic')

        meter = result.get('meter', 'None')
        conf = result.get('confidence', 0)
        syl_count = result.get('syllable_count', 0)
        expected = result.get('expected_syllables', '?')

        status = "✓" if meter == tc['expected_meter'] else "✗"
        print(f"    Result: {meter} (conf: {conf:.2f})")
        print(f"    Syllables: {syl_count} (expected: {expected})")
        print(f"    Status: {status} (expected: {tc['expected_meter']})")

    print("\n" + "-" * 70)
    print("Testing CLASSICAL mode:")
    print("-" * 70)

    for tc in test_cases[3:]:  # Classical cases
        print(f"\n>>> {tc['name']}")
        print(f"    Text: {tc['text'][:50]}...")

        result = chanda.identify_modal(tc['text'], mode='classical')

        meter = result.get('meter', 'None')
        conf = result.get('confidence', 0)

        print(f"    Result: {meter} (conf: {conf:.2f})")

    print("\n" + "-" * 70)
    print("Testing AUTO mode:")
    print("-" * 70)

    for tc in test_cases:
        print(f"\n>>> {tc['name']}")

        result = chanda.identify_modal(tc['text'], mode='auto')

        meter = result.get('meter', 'None')
        decision = result.get('auto_decision', 'unknown')
        reason = result.get('auto_reason', 'N/A')

        status = "✓" if decision == tc['expected_mode'] else "✗"
        print(f"    Decision: {decision} {status}")
        print(f"    Meter: {meter}")
        print(f"    Reason: {reason}")

    print("\n" + "=" * 70)
    print("   EXPERIMENT COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    test_modal_identification()
