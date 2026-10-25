"""Vedic meter identification by syllable count and verse-level holistic analysis.

Mixed into backend.core.chanda.Chanda; methods rely on its other mixins through self.
"""

from .chanda_constants import (
    PANKTI_SIGNAL_THRESHOLD,
)


class VedicMixin:
    # ----------------------------------------------------------------------- #

    def identify_vedic_meter(self, syllable_count, lg_pattern=None, allow_ambiguous=False):
        """Identify Vedic meter by syllable count with ±1 tolerance and pattern matching

        Supports standard Vedic meters and their variants:
        - Nicṛt (निचृत्): Shortened form (-1 syllable per pada)
        - Bhurik (भुरिक्): Extended form (+1 syllable per pada)
        - Virāṭ (विराट्): Further extended form

        Args:
            syllable_count: Number of syllables
            lg_pattern: L-G pattern string (optional)
            allow_ambiguous: If False, skip 21/27 syllable counts which conflict
                            with classical pada meters like Sragdharā (21 per pada).
                            Set to True only for verse-level holistic identification.
        """
        # Map syllable counts to actual meter names
        # Includes standard meters AND common variants (Nicṛt, Bhurik)
        vedic_mapping = {
            # Gāyatrī family (3 padas) - ONLY if allow_ambiguous is True
            # 21: 'निचृद्गायत्री',   # Conflicts with Sragdharā pada (21 per pada)
            24: 'गायत्री',  # Standard Gayatri - 3×8
            # 27: 'भुरिग्गायत्री',   # Conflicts with some classical meters
            # Uṣṇik family (4 padas)
            28: 'उष्णिक्',  # Ushnik - 4×7
            # Anuṣṭubh family (4 padas)
            32: 'अनुष्टुभ्',  # Anushtubh - 4×8
            # Bṛhatī family (4 padas)
            36: 'बृहती',  # Brihati - 4×9
            # Paṅkti family (5 padas)
            40: 'पङ्क्ति',  # Pankti - 5×8
            # Triṣṭubh family (4 padas)
            44: 'त्रिष्टुभ्',  # Trishtubh - 4×11
            # Jagatī family (4 padas)
            48: 'जगती',  # Jagati - 4×12
        }

        # Add ambiguous syllable counts only when explicitly allowed
        # (e.g., for verse-level holistic identification with confirmed structure)
        if allow_ambiguous:
            vedic_mapping[21] = 'निचृद्गायत्री'  # Nicrt Gayatri - 3×7
            vedic_mapping[27] = 'भुरिग्गायत्री'  # Bhurik Gayatri - 3×9

        # For pada-level identification (single pada, not full verse)
        pada_mapping = {
            7: 'उष्णिक्',  # Ushnik pada OR Nicrt Gayatri pada
            8: 'गायत्री',  # Gayatri/Anushtubh pada
            9: 'बृहती',  # Brihati pada OR Bhurik Gayatri pada
            11: 'त्रिष्टुभ्',  # Trishtubh pada
            12: 'जगती',  # Jagati pada
        }

        # Helper function to get English meter name for VEDIC_METERS lookup
        def get_english_name(sanskrit_name):
            name_map = {
                'गायत्री': 'Gayatri',
                'निचृद्गायत्री': 'Nicrt_Gayatri',  # 3×7 = 21 syllables
                'भुरिग्गायत्री': 'Bhurik_Gayatri',  # 3×9 = 27 syllables
                'त्रिष्टुभ्': 'Trishtubh',
                'जगती': 'Jagati',
                'उष्णिक्': 'Ushnik',
                'अनुष्टुभ्': 'Anushtubh',
                'बृहती': 'Brihati',
                'पङ्क्ति': 'Pankti',
            }
            return name_map.get(sanskrit_name, sanskrit_name)

        # First try pada-level matching with pattern verification
        if syllable_count in pada_mapping and lg_pattern:
            meter_name = pada_mapping[syllable_count]
            if meter_name in self.VEDIC_PADA_PATTERNS:
                expected_pattern = self.VEDIC_PADA_PATTERNS[meter_name]
                if self.pattern_matches_with_tolerance(lg_pattern, expected_pattern, tolerance=2):
                    english_name = get_english_name(meter_name)
                    return meter_name, self.VEDIC_METERS.get(english_name)

        # Try full verse matching
        # Exact match
        if syllable_count in vedic_mapping:
            meter_name = vedic_mapping[syllable_count]
            english_name = get_english_name(meter_name)
            return meter_name, self.VEDIC_METERS.get(english_name)

        # Allow ±2 syllable tolerance for Vedic texts with accent marks
        # Vedic accent marks (Udātta, Anudātta) can cause syllable count variations
        # Find the CLOSEST match within ±2 tolerance
        # When distances are equal, prefer LARGER meter (accent removal tends to reduce count)
        best_match = None
        best_difference = float('inf')
        best_expected_count = 0

        for expected_count, meter_name in vedic_mapping.items():
            difference = abs(syllable_count - expected_count)
            if difference <= 2:
                # Prefer match with smaller difference, or larger expected count if equal
                if difference < best_difference or (
                    difference == best_difference and expected_count > best_expected_count
                ):
                    best_difference = difference
                    best_match = meter_name
                    best_expected_count = expected_count

        if best_match:
            english_name = get_english_name(best_match)
            return best_match, self.VEDIC_METERS.get(english_name)

        # Try pada-level without pattern (less confident)
        if syllable_count in pada_mapping:
            meter_name = pada_mapping[syllable_count]
            english_name = get_english_name(meter_name)
            return meter_name, self.VEDIC_METERS.get(english_name)

        return None, None

    ###########################################################################

    def identify_verse_holistically(self, verse_lines):
        """
        Identify verse as a complete unit (Bug #2 fix)
        Aggregates multiple lines and processes them together.

        ENHANCED: Now includes structure detection to properly prioritize
        Vedic meters over pada-level exact matches.
        """
        # Combine all lines in the verse
        combined_text = ' '.join(verse_lines)
        syllables, lg_marks = self.mark_lg(combined_text)
        lg_str = ''.join(lg_marks)

        # Calculate total syllables
        total_syllables = len(lg_str)

        # ENHANCED: Detect verse structure first
        structure = self.detect_verse_structure(verse_lines)

        # Try to identify by total syllable count with pattern
        meter_name, meter_info = self.identify_vedic_meter(total_syllables, lg_str)

        # ENHANCED: If structure confirms a Vedic meter, use that
        if structure['vedic_structure_confirmed'] and structure['expected_vedic_meter']:
            meter_name = structure['expected_vedic_meter']

        result = {
            'found': False,
            'meter': meter_name,
            'total_syllables': total_syllables,
            'lg_str': lg_str,
            'structure': structure,  # Include structure for use in aggregation
        }

        if meter_name:
            result['found'] = True

        return result

    def _identify_vedic_mode(self, text):
        """
        Identify Vedic meter by syllable count (Modal Logic).
        Uses empirical peak syllable counts from Rigveda data analysis.

        Enhanced with composite meter detection for Pragātha, Virāṭ, etc.
        """
        result = {'mode': 'vedic', 'meter': None, 'confidence': 0.0, 'syllable_count': 0, 'debug': {}}

        # Clean and split text into lines
        lines = [ln.strip() for ln in text.replace('॥', '।').split('।') if ln.strip()]
        if not lines:
            lines = [ln.strip() for ln in text.split('\n') if ln.strip()]

        total_syllables = 0

        for line in lines:
            clean_line = line.replace('।', '').replace('॥', '').strip()
            if not clean_line:
                continue

            # Use mark_lg which handles syllabization method selection
            # mark_lg returns (syllables, lg_marks)
            _, lg = self.mark_lg(clean_line)
            total_syllables += len(lg)

        result['syllable_count'] = total_syllables

        # Try composite meter detection first (Pragātha, Virāṭ, Kakubh, etc.)
        # These require pada-level structure analysis
        composite_meter, composite_conf = self._detect_composite_meter(text, total_syllables)
        if composite_meter and composite_conf >= 0.8:
            # Found a composite meter with high confidence
            meter_info = None
            for info in self.VEDIC_METERS_BY_COUNT.values():
                if info['name'] == composite_meter:
                    meter_info = info
                    break

            if meter_info:
                result['meter'] = composite_meter
                result['meter_en'] = meter_info['name_en']
                result['confidence'] = composite_conf
                result['debug']['match_type'] = 'composite_structure'
                result['debug']['pada_analysis'] = True
                return result

        # PRAGĀTHA vs PAṄKTI DISCRIMINATOR (for overlap zone 34-42 syllables)
        # Based on empirical analysis: Paṅkti has exclusive endings/refrains, Pragātha doesn't
        if 34 <= total_syllables <= 46:
            pankti_score = self._detect_pankti_signals(text, total_syllables)
            if pankti_score >= PANKTI_SIGNAL_THRESHOLD:
                # Strong Paṅkti signal - use Paṅkti or Mahāpaṅkti
                if total_syllables >= 43:
                    result['meter'] = 'महापङ्क्ति'
                    result['meter_en'] = 'Mahāpaṅkti'
                else:
                    result['meter'] = 'पङ्क्ति'
                    result['meter_en'] = 'Paṅkti'
                result['confidence'] = min(0.95, 0.6 + pankti_score * 0.08)
                result['expected_syllables'] = 40 if total_syllables < 43 else 47
                result['debug']['match_type'] = 'pankti_discriminator'
                result['debug']['pankti_score'] = pankti_score
                return result

        # Use peak-based matching (empirical data from Rigveda analysis)
        # This accounts for the fact that actual syllable counts vary from theoretical
        candidates = []

        # Define priority for common Vedic meters (higher = preferred when distances equal)
        # 7 major Vedic meters have highest priority
        METER_PRIORITY = {
            'गायत्री': 100,
            'उष्णिक्': 100,
            'अनुष्टुभ्': 100,
            'बृहती': 100,
            'पङ्क्ति': 100,
            'त्रिष्टुभ्': 100,
            'जगती': 100,
            # Pragātha promoted to major meter priority at peak syllable counts
            # (only matched when exactly at 38, 39, or 40 syllables)
            'प्रगाथ': 100,  # Pragātha at peak range gets high priority
            # Rare/composite meters have lower priority (only match with strong evidence)
            'विराट्': 50,
            'ज्योतिस्': 20,  # Requires refrain pattern
            'महापङ्क्ति': 20,  # Requires refrain pattern
            'ककुभ्': 50,  # 3-pada structure
            'द्विपदा त्रिष्टुभ्': 50,
        }

        for meter_name, peak in self.VEDIC_METER_PEAKS.items():
            # Check if syllable count is within range for this meter
            if meter_name in self.VEDIC_METER_RANGES:
                low, high = self.VEDIC_METER_RANGES[meter_name]
                if low <= total_syllables <= high:
                    # Skip rare meters that require structural analysis without it
                    # These should only be detected via _detect_composite_meter
                    if meter_name in ['ज्योतिस्', 'महापङ्क्ति']:
                        # Only add these if we detected a refrain pattern
                        refrain_match = self._detect_refrain_pattern(text)
                        if refrain_match != meter_name:
                            continue  # Skip, let standard meters handle it

                    # PRAGĀTHA: Special handling due to wide distribution and overlaps
                    # Pragātha has peak at 39 (22% of verses) but ranges from 33-45
                    # It overlaps with Bṛhatī (35), Paṅkti (39), and Triṣṭubh (43)
                    # Since Pragātha requires pada structure (11+12 pattern) for definitive ID,
                    # we only include it as a candidate when syllable count is in peak zone
                    if meter_name == 'प्रगाथ':
                        # Only match Pragātha at exactly 38, 39, or 40 syllables (peak zone)
                        # This is where Pragātha is statistically most common
                        if total_syllables not in [38, 39, 40]:
                            continue  # Skip, let other meters handle it

                    # Calculate distance from peak
                    diff = abs(total_syllables - peak)
                    # Get meter info
                    meter_info = None
                    for info in self.VEDIC_METERS_BY_COUNT.values():
                        if info['name'] == meter_name:
                            meter_info = info
                            break

                    if meter_info:
                        # Confidence based on distance from peak
                        if diff == 0:
                            confidence = 1.0
                        elif diff == 1:
                            confidence = 0.95
                        elif diff == 2:
                            confidence = 0.90
                        elif diff <= 4:
                            confidence = 0.80
                        else:
                            confidence = 0.70

                        priority = METER_PRIORITY.get(meter_name, 10)

                        candidates.append(
                            {
                                'meter': meter_name,
                                'meter_en': meter_info['name_en'],
                                'diff': diff,
                                'confidence': confidence,
                                'peak': peak,
                                'priority': priority,
                            }
                        )

        # PADA-FIRST APPROACH: Use pada structure as the PRIMARY discriminator
        # This is critical for disambiguating Trishtubh/Pankti/Jagati which overlap in syllable count
        # Trishtubh: 4 padas × 11 syllables, Pankti: 5 padas × 8 syllables, Jagati: 4 padas × 12 syllables

        # Expected pada structures for major meters (padas, avg_syllables_per_pada, allowed_range)
        PADA_EXPECTED = {
            'गायत्री': (3, 8, (7.5, 8.5)),  # 3 padas of 8 syllables
            'उष्णिक्': (3, 9.3, (8.5, 10)),  # 3 padas, ~9.3 avg (28/3)
            'अनुष्टुभ्': (4, 8, (7.5, 8.5)),  # 4 padas of 8 syllables
            'बृहती': (4, 9, (8.5, 9.5)),  # 4 padas, ~9 avg (36/4)
            'पङ्क्ति': (5, 8, (7.5, 8.5)),  # 5 padas of 8 syllables - KEY: 5 padas!
            'त्रिष्टुभ्': (4, 11, (9.5, 11.5)),  # 4 padas of 11 syllables - KEY: avg 10-11
            'जगती': (4, 12, (11.5, 13)),  # 4 padas of 12 syllables - KEY: avg 12+
        }

        padas = self._split_into_padas(text)
        num_padas = len(padas) if padas else 0
        avg_pada = sum(p[1] for p in padas) / num_padas if num_padas > 0 else 0

        if candidates:
            # EMPIRICAL LIKELIHOOD ADJUSTMENT
            # Based on actual Rigveda data distributions for overlap regions
            # At certain syllable counts, one meter is much more likely than another
            # IMPORTANT: These bonuses are calibrated against OUR syllable counting,
            # which differs slightly from the dataset (avagraha handling, etc.)
            # Format: {syllable_count: {meter: bonus_score}}
            SYLLABLE_LIKELIHOOD_BONUS = {
                # Dvipadā Virāṭ + Virāṭ zone (18-20 syllables)
                # 19: Dvipadā Virāṭ 47% + Virāṭ 46% = 93% Virāṭ-family, 7% Gāyatrī
                # 20: Virāṭ 48% + Dvipadā Virāṭ 35% = 83% Virāṭ-family, 12% Gāyatrī
                18: {'द्विपदा विराट्': 70},  # 100% Dvipadā Virāṭ
                19: {'द्विपदा विराट्': 40, 'विराट्': 35},  # Both Virāṭ types dominate
                20: {'विराट्': 40, 'द्विपदा विराट्': 35},  # Virāṭ 48%, Dvipadā 35%
                # Transition zone - Gāyatrī takes over at 21+
                21: {'गायत्री': 60, 'द्विपदा त्रिष्टुभ्': 20},  # Gāyatrī 84%!
                22: {'गायत्री': 65, 'द्विपदा त्रिष्टुभ्': 10},  # Gāyatrī 97%
                # Gayatri vs Usnik overlap (23-26)
                # Key: Gayatri peak=24, Usnik peak=28
                23: {'गायत्री': 65},  # Gāyatrī 99%
                24: {'गायत्री': 65},  # Gayatri peak at 24 (strong)
                25: {'गायत्री': 10, 'उष्णिक्': 25},  # Usnik 50% vs Gayatri 20% but Gayatri has MORE verses
                26: {'उष्णिक्': 35, 'ककुभ्': 20},  # Usnik 63%, Kakubh starts
                # Usnik vs Anushtubh overlap (27-30)
                27: {'उष्णिक्': 50},  # Usnik 73%
                28: {'उष्णिक्': 45},  # Usnik 69%
                29: {'अनुष्टुभ्': 35},  # Anushtubh 64% (critical - winning over Usnik!)
                30: {'अनुष्टुभ्': 50},  # Anushtubh 75%
                31: {'अनुष्टुभ्': 55},  # Anushtubh 80% (PEAK)
                32: {'अनुष्टुभ्': 50},  # Anushtubh 76%
                # Brhati zone (33-36 syllables) - complex overlap
                # At 33: Anuṣṭubh 40%, Virāṭ 22%, Bṛhatī 19%, Pragātha 16%
                # At 34: Bṛhatī 48%, Pragātha 44% - Bṛhatī dominates
                33: {'अनुष्टुभ्': 30, 'विराट्': 20, 'बृहती': 15, 'प्रगाथ': 12},  # Anuṣṭubh leads at 33!
                34: {'बृहती': 25, 'प्रगाथ': 20},  # Brhati 48%, Pragatha 40%
                35: {'बृहती': 25, 'प्रगाथ': 22},  # Brhati 47%, Pragatha 42% (PEAK)
                36: {'बृहती': 20, 'प्रगाथ': 15},  # Brhati 47%, Pragatha 33%
                37: {'पङ्क्ति': 30, 'प्रगाथ': 30, 'बृहती': -10},  # Pankti=Pragatha 34%, Brhati 10% (penalize)
                # Pankti/Pragatha/Trishtubh overlap zone (38-41 syllables)
                # Based on analysis of OUR syllable counting
                38: {'पङ्क्ति': 30, 'प्रगाथ': 20, 'बृहती': 5},  # Pankti 35%, Pragatha 21%, Brhati 13%
                39: {'प्रगाथ': 30, 'त्रिष्टुभ्': 20, 'पङ्क्ति': 20},  # Pragatha 33%, Trishtubh 24%, Pankti 22%
                40: {'त्रिष्टुभ्': 40, 'पङ्क्ति': 8},  # Trishtubh 55%, Pankti/Pragatha ~12% each
                41: {'त्रिष्टुभ्': 50},  # Trishtubh 95%
                # Trishtubh vs Jagati overlap (using OUR computed syllables)
                # At 42-44: Triṣṭubh dominates (97-99%), at 45: still leads (67%)
                42: {'त्रिष्टुभ्': 50},  # 99.7% Trishtubh
                43: {'त्रिष्टुभ्': 50},  # 99.0% Trishtubh
                44: {'त्रिष्टुभ्': 40},  # 97.4% Trishtubh
                45: {'त्रिष्टुभ्': 20, 'महापङ्क्ति': 15},  # 66.7% Trishtubh, 32.1% Jagati, Mahapankti starts
                46: {'जगती': 30, 'महापङ्क्ति': 35},  # Mahapankti peak=47 but range starts
                47: {'जगती': 40, 'महापङ्क्ति': 40},  # Both peak here
                48: {'जगती': 60},  # 100% Jagati
                49: {'जगती': 60},  # 100% Jagati
            }

            # Apply likelihood bonus
            if total_syllables in SYLLABLE_LIKELIHOOD_BONUS:
                bonus_dict = SYLLABLE_LIKELIHOOD_BONUS[total_syllables]
                for cand in candidates:
                    if cand['meter'] in bonus_dict:
                        cand['likelihood_bonus'] = bonus_dict[cand['meter']]
                    else:
                        cand['likelihood_bonus'] = 0
            else:
                for cand in candidates:
                    cand['likelihood_bonus'] = 0

            # Score each candidate using COMBINED approach (pada structure + peak distance + likelihood)
            for cand in candidates:
                meter = cand['meter']
                pada_score = 0

                if meter in PADA_EXPECTED and num_padas >= 3:
                    exp_padas, exp_avg, avg_range = PADA_EXPECTED[meter]

                    # Pada count match (VERY important for Pankti which has 5 padas)
                    if num_padas == exp_padas:
                        pada_score += 40
                    elif abs(num_padas - exp_padas) == 1:
                        pada_score += 15

                    # Average pada length match (CRITICAL for Trishtubh vs Jagati)
                    if avg_range[0] <= avg_pada <= avg_range[1]:
                        pada_score += 60  # Perfect match within range
                    else:
                        avg_diff = min(abs(avg_pada - avg_range[0]), abs(avg_pada - avg_range[1]))
                        pada_score += max(0, 40 - avg_diff * 25)

                    # Extra bonus for perfect structure match
                    if num_padas == exp_padas and avg_range[0] <= avg_pada <= avg_range[1]:
                        pada_score += 20  # Bonus for both matching

                cand['pada_score'] = pada_score

            # Sort by: 1) combined score (higher better), 2) distance from peak (lower better)
            # Combined score = pada_score * 2 - diff * 10 + priority + likelihood_bonus
            for cand in candidates:
                cand['combined_score'] = (
                    cand.get('pada_score', 0) * 2
                    - cand['diff'] * 10
                    + cand['priority']
                    + cand.get('likelihood_bonus', 0)
                )

            candidates.sort(key=lambda x: (-x['combined_score'], x['diff']))
            best = candidates[0]

            # Debug info
            result['debug']['pada_validated'] = True
            result['debug']['num_padas'] = num_padas
            result['debug']['avg_pada'] = round(avg_pada, 2)
            result['debug']['pada_score'] = best.get('pada_score', 0)
            result['debug']['combined_score'] = best.get('combined_score', 0)

            result['meter'] = best['meter']
            result['meter_en'] = best['meter_en']
            result['confidence'] = best['confidence']
            result['expected_syllables'] = best['peak']
            result['debug']['match_type'] = 'peak_based'
            result['debug']['candidates'] = [(c['meter'], c['diff']) for c in candidates[:3]]
        else:
            # Fallback: try exact match from VEDIC_METERS_BY_COUNT
            for syl_count, meter_info in self.VEDIC_METERS_BY_COUNT.items():
                diff = abs(total_syllables - syl_count)
                if diff <= self.SYLLABLE_TOLERANCE:
                    candidates.append((diff, syl_count, meter_info))

            if candidates:
                candidates.sort(key=lambda x: (x[0], x[1]))
                best_diff, syl_count, meter_info = candidates[0]
                result['meter'] = meter_info['name']
                result['meter_en'] = meter_info['name_en']
                result['confidence'] = max(0.5, 1.0 - (best_diff * 0.1))
                result['expected_syllables'] = syl_count
                result['debug']['match_type'] = 'fallback_exact'

        return result
