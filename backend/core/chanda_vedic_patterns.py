"""Pragātha, composite, Paṅkti and refrain detection for Vedic verses.

Mixed into backend.core.chanda.Chanda; methods rely on its other mixins through self.
"""


class VedicPatternMixin:
    def _detect_pragatha(self, verses):
        """
        Detect Pragātha meter from a list of verses.

        Pragātha is a 2-verse compound structure where each verse has:
        - 1st pāda: Triṣṭubh (11 syllables)
        - 2nd pāda: Jagatī (12 syllables)

        Pattern: [11, 12] + [11, 12] across 2 consecutive verses

        Parameters:
        -----------
        verses : list
            List of verse strings (at least 2 for Pragātha detection)

        Returns:
        --------
        tuple: (is_pragatha: bool, pattern_info: dict or None)
        """
        if len(verses) < 2:
            return False, None

        patterns = []
        verse_details = []

        # Analyze first 2 verses (Pragātha = 2-verse pair)
        for i, verse in enumerate(verses[:2]):
            padas = self._split_into_vedic_padas(verse)

            if len(padas) < 2:
                # Can't determine pada structure
                return False, None

            # Get syllable counts for first 2 padas
            syllables = [p[1] for p in padas[:2]]
            patterns.append(syllables)
            verse_details.append(
                {
                    'verse_num': i + 1,
                    'padas': padas,
                    'syllables': syllables,
                    'pada1_meter': 'Triṣṭubh' if 10 <= syllables[0] <= 12 else 'Unknown',
                    'pada2_meter': 'Jagatī' if 11 <= syllables[1] <= 13 else 'Unknown',
                }
            )

        # Check for Pragātha pattern: [11, 12] + [11, 12]
        # Allow variance: 10-12 for Triṣṭubh, 11-13 for Jagatī
        expected_ranges = {
            'pada1': (10, 12),  # Triṣṭubh (nominal 11)
            'pada2': (11, 13),  # Jagatī (nominal 12)
        }

        is_pragatha = True
        confidence = 1.0

        for pattern in patterns:
            if len(pattern) < 2:
                is_pragatha = False
                break

            p1, p2 = pattern[0], pattern[1]

            # Check if pada1 is in Triṣṭubh range
            if not (expected_ranges['pada1'][0] <= p1 <= expected_ranges['pada1'][1]):
                # Allow slight variance with reduced confidence
                if 9 <= p1 <= 13:
                    confidence *= 0.8
                else:
                    is_pragatha = False
                    break

            # Check if pada2 is in Jagatī range
            if not (expected_ranges['pada2'][0] <= p2 <= expected_ranges['pada2'][1]):
                # Allow slight variance with reduced confidence
                if 10 <= p2 <= 14:
                    confidence *= 0.8
                else:
                    is_pragatha = False
                    break

        if is_pragatha:
            return True, {
                'meter': 'प्रगाथ',
                'meter_en': 'Pragātha',
                'type': 'compound',
                'patterns': patterns,
                'verse_details': verse_details,
                'structure': 'Triṣṭubh–Jagatī–Triṣṭubh–Jagatī',
                'confidence': confidence,
                'description': 'Pragātha: 2-verse compound with Triṣṭubh (11) + Jagatī (12) pairs',
            }

        return False, None

    def _detect_pragatha_single_verse(self, text):
        """
        Detect if a single verse matches Pragātha pada structure (11+12).

        This is used when we only have one verse but want to check if it
        follows the Triṣṭubh + Jagatī pattern.

        Returns: (is_match: bool, confidence: float, details: dict)
        """
        padas = self._split_into_vedic_padas(text)

        if len(padas) < 2:
            return False, 0.0, {}

        p1_syls = padas[0][1]
        p2_syls = padas[1][1]

        # Check for Triṣṭubh (11) + Jagatī (12) pattern
        # Allow variance: 10-12 for first pada, 11-13 for second
        is_trishtubh = 10 <= p1_syls <= 12
        is_jagati = 11 <= p2_syls <= 13

        if is_trishtubh and is_jagati:
            confidence = 0.9
            # Perfect match (11+12) gets higher confidence
            if p1_syls == 11 and p2_syls == 12:
                confidence = 1.0

            return (
                True,
                confidence,
                {
                    'pada1': {'syllables': p1_syls, 'meter': 'त्रिष्टुभ्'},
                    'pada2': {'syllables': p2_syls, 'meter': 'जगती'},
                    'total': p1_syls + p2_syls,
                },
            )

        return False, 0.0, {}

    def _detect_composite_meter(self, text, total_syllables):
        """
        Detect composite meters (Pragātha, Virāṭ, etc.) based on structural analysis.

        These meters require pada-level structure analysis, not just total syllable count.

        Returns: (meter_name, confidence) or (None, 0.0)
        """
        padas = self._split_into_padas(text)

        if not padas:
            return None, 0.0

        pada_syllables = [p[1] for p in padas]
        num_padas = len(pada_syllables)

        # =====================================================================
        # PRAGĀTHA DETECTION (NEW - Triṣṭubh + Jagatī compound)
        # =====================================================================
        # Pragātha single-verse pattern: 11 (Triṣṭubh) + 12 (Jagatī) = 23 syllables
        # For proper Pragātha, we need 2 consecutive verses, but a single verse
        # with 11+12 pattern is a strong indicator.
        if 21 <= total_syllables <= 25 and num_padas == 2:
            is_pragatha, confidence, details = self._detect_pragatha_single_verse(text)
            if is_pragatha and confidence >= 0.8:
                return 'प्रगाथ', confidence

        # Check Virāṭ (2 padas of 10 syllables each = 20 total)
        if num_padas == 2 and total_syllables in range(18, 23):
            # Virāṭ: Dvipadā form with 10+10 structure
            # But NOT if it looks like Pragātha (11+12)
            p1, p2 = pada_syllables[0], pada_syllables[1]
            if abs(p1 - p2) <= 2:  # Both padas roughly equal = Virāṭ
                if all(8 <= s <= 12 for s in pada_syllables):
                    return 'विराट्', 0.9

        # Check Dvipadā Triṣṭubh (2 padas of 11 syllables each = 22 total)
        if num_padas == 2 and total_syllables in range(20, 25):
            p1, p2 = pada_syllables[0], pada_syllables[1]
            if abs(p1 - p2) <= 1:  # Both padas roughly equal
                if all(10 <= s <= 12 for s in pada_syllables):
                    return 'द्विपदा त्रिष्टुभ्', 0.85

        # Check Kakubh (8+8+12 structure = 28 total, or 8+12+8)
        if num_padas == 3 and total_syllables in range(26, 31):
            # Kakubh: Odd pada structure with one 12-syllable pada
            sorted_padas = sorted(pada_syllables)
            if sorted_padas[0] in range(7, 10) and sorted_padas[1] in range(7, 10) and sorted_padas[2] in range(10, 14):
                return 'ककुभ्', 0.85

        # Check for 4-pada patterns (Bṛhatī-family or Satobṛhatī)
        # This is legacy code that may catch some edge cases
        if num_padas >= 4 and total_syllables in range(33, 45):
            if num_padas == 4:
                p1, p2, p3, p4 = pada_syllables[:4]
                # Bṛhatī: First two short (8), third long (12), fourth short (8)
                if 6 <= p1 <= 10 and 6 <= p2 <= 10 and 10 <= p3 <= 14 and 6 <= p4 <= 10:
                    return 'बृहती', 0.8
                # Satobṛhatī: First long (12), second short (8), third long (12), fourth short (8)
                if 10 <= p1 <= 14 and 6 <= p2 <= 10 and 10 <= p3 <= 14 and 6 <= p4 <= 10:
                    return 'बृहती', 0.75  # Satobṛhatī is in Bṛhatī family

        # Check for refrain patterns (Jyotis, Mahāpaṅkti)
        refrain_meter = self._detect_refrain_pattern(text)
        if refrain_meter:
            return refrain_meter, 0.9

        return None, 0.0

    # Paṅkti-EXCLUSIVE endings (appear in Paṅkti, ZERO in Pragātha - from Rigveda analysis)
    PANKTI_EXCLUSIVE_ENDINGS = [
        'उत्तरः',  # 23 in Paṅkti, 0 in Pragātha
        'स्वराज्यं',  # 19 in Paṅkti, 0 in Pragātha
        'स्रव',  # 19 in Paṅkti, 0 in Pragātha
        'विवक्षसे',  # 17 in Paṅkti, 0 in Pragātha
        'अश्वसूनृते',  # 10 in Paṅkti, 0 in Pragātha
        'तुवीमघ',  # 7 in Paṅkti, 0 in Pragātha
        'हरी',  # 5 in Paṅkti, 0 in Pragātha (as final word)
        'चनाममत्',  # 3 in Paṅkti, 0 in Pragātha
    ]

    # Paṅkti-exclusive word sequences (100% precision)
    PANKTI_EXCLUSIVE_SEQUENCES = [
        'परि स्रव',  # 19 in Paṅkti
        'इंद्र उत्तरः',  # 16+ in Paṅkti
        'विश्वस्मादिंद्र उत्तरः',  # Complete phrase
        'अस्य रोदसी',  # 10 in Paṅkti
        'सुजाते अश्वसूनृते',  # 10 in Paṅkti
        'श्रुतं हवं',  # 9 in Paṅkti
        'सहस्रेषु तुवीमघ',  # 7 in Paṅkti
        'ते हरी',  # 5 in Paṅkti
        'नो वृधे',  # 4 in Paṅkti
        'वस्वीरनु स्वराज्यं',  # 3 in Paṅkti
        'किं चनाममत्',  # 3 in Paṅkti
        'अधि धन्वसु',  # 3 in Paṅkti
        'इंद्रस्य रातयः',  # 3 in Paṅkti
    ]

    # Traditional Paṅkti refrains (from Rigveda analysis)
    PANKTI_REFRAINS = [
        'आ तू न इंद्र शंसय',  # Very long refrain
        'स्तोतृभ्य आ भर',  #
        'माध्वी मम श्रुतं हवं',  #
        'भद्रा इंद्रस्य रातयः',  #
        'ज्याका अधि धन्वसु',  #
        'मे अस्य रोदसी',  #
        'अर्चन्ननु स्वराज्यं',  # Common refrain
        'वस्वीरनु स्वराज्यं',  # Variant
    ]

    def _detect_pankti_signals(self, text, syllable_count):
        """
        Detect Paṅkti-specific signals in verse text.

        Based on empirical analysis of Rigveda:
        - Paṅkti has exclusive word endings (100% precision)
        - Paṅkti has characteristic refrain patterns
        - These signals are ABSENT in Pragātha

        Returns a score: higher = more likely Paṅkti
        """
        score = 0.0

        # 1. Check for exclusive word endings (strongest signal)
        words = text.strip().split()
        last_word = words[-1] if words else ''

        if last_word in self.PANKTI_EXCLUSIVE_ENDINGS:
            score += 5.0  # Very strong Paṅkti signal

        # 2. Check for exclusive word sequences
        last_60 = text[-60:] if len(text) > 60 else text
        for seq in self.PANKTI_EXCLUSIVE_SEQUENCES:
            if seq in last_60:
                score += 4.0
                break  # Only count once

        # 3. Check for refrain patterns
        last_50 = text[-50:] if len(text) > 50 else text
        for refrain in self.PANKTI_REFRAINS:
            if refrain in last_50:
                score += 3.0
                break  # Only count once

        # 4. Syllable count signal (Paṅkti favored at certain counts)
        if syllable_count >= 43:
            score += 2.0  # Mahāpaṅkti range
        elif syllable_count in [40, 41, 42]:
            score += 0.5  # Slight Paṅkti signal

        return score

    def _detect_refrain_pattern(self, text):
        """
        Detect meters that have characteristic refrain patterns.

        Jyotis often ends with 'सजोषसा' or 'उषसा सूर्येण च'
        Mahāpaṅkti may have 'नभंतामन्यके समे'
        """

        for meter_name, refrains in self.REFRAIN_PATTERNS.items():
            for refrain in refrains:
                if refrain in text:
                    return meter_name

        return None

    def _find_meter_by_range(self, syllable_count):
        """Find Vedic meter using syllable count ranges."""
        candidates = []
        for meter_name, (low, high) in self.VEDIC_METER_RANGES.items():
            if low <= syllable_count <= high:
                expected = None
                for syl_count, info in self.VEDIC_METERS_BY_COUNT.items():
                    if info['name'] == meter_name:
                        expected = syl_count
                        name_en = info['name_en']
                        break

                if expected:
                    diff = abs(syllable_count - expected)
                    confidence = max(0.5, 1.0 - (diff * 0.05))
                    candidates.append(
                        {
                            'name': meter_name,
                            'name_en': name_en,
                            'expected': expected,
                            'diff': diff,
                            'confidence': confidence,
                        }
                    )

        if candidates:
            candidates.sort(key=lambda x: (-x['expected'], x['diff']))
            return candidates[0]
        return None
