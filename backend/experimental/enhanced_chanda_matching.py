"""Pattern, pada, Upajāti, Vedic, mātrā and fuzzy matching for EnhancedChanda.

Mixed into backend.core.enhanced_chanda.EnhancedChanda.
"""

import Levenshtein as Lev


class EnhancedMatchingMixin:
    ###########################################################################
    # Enhanced Multi-level Matching (Key Improvement)
    ###########################################################################

    def match_with_confidence(self, lg_pattern, fuzzy=False, max_fuzzy=10):
        """
        Enhanced multi-level matching with confidence scoring

        Priority order (from Chandovallari principles):
        1. Exact full match (10.0)
        1.5. Pada-level exact match (9.5) - NEW: checks individual padas
        2. Upajāti detection (9.3) - NEW: mixed Indravajrā/Upendravajrā
        3. Vedic pada-level by syllable count (6.0) - REDUCED from 8.0
        4. Vedic full verse syllable count (4.0) - REDUCED from 7.0
        5. Fuzzy match (1.0-4.0)
        """
        results = []
        syllable_count = len(lg_pattern)
        seen_meters = set()  # Track to avoid duplicates

        # Level 1: Exact full match (highest confidence)
        if lg_pattern in self.CHANDA:
            for meter_name in self.CHANDA[lg_pattern]:
                name = meter_name[0] if isinstance(meter_name, tuple) else meter_name
                if name not in seen_meters:
                    results.append((meter_name, 10.0, 'exact'))
                    seen_meters.add(name)

        # Level 1.5: Pada-level exact matching (NEW - Key improvement)
        pada_matches = self._match_pada_patterns(lg_pattern)
        for meter_name, confidence, match_type in pada_matches:
            name = meter_name[0] if isinstance(meter_name, tuple) else meter_name
            # Don't add if it's a Vedic family name and we have specific matches
            if name in self.VEDIC_FAMILY_NAMES and seen_meters:
                continue
            if name not in seen_meters:
                results.append((meter_name, confidence, match_type))
                seen_meters.add(name)

        # Level 2: Upajāti detection (NEW)
        upajati_result = self._detect_upajati(lg_pattern)
        if upajati_result:
            meter_name, variety_name = upajati_result
            if meter_name not in seen_meters:
                results.append(((f'उपजाति ({variety_name})', ''), 9.3, 'upajati'))
                seen_meters.add(meter_name)

        # Level 3: Vedic pada-level matching (REDUCED confidence)
        # Only if no pada-exact matches found
        if not pada_matches:
            vedic_pada_results = self._match_vedic_pada(lg_pattern)
            for meter_name, confidence, match_type in vedic_pada_results:
                name = meter_name[0] if isinstance(meter_name, tuple) else meter_name
                if name not in seen_meters:
                    results.append((meter_name, confidence, match_type))
                    seen_meters.add(name)

        # Level 4: Vedic full syllable count (REDUCED confidence)
        vedic_meter = self._identify_vedic_by_syllable(syllable_count)
        if vedic_meter:
            name = vedic_meter[0] if isinstance(vedic_meter, tuple) else vedic_meter
            if name not in seen_meters:
                results.append((vedic_meter, 4.0, 'vedic_syllable'))
                seen_meters.add(name)

        # Level 5: Mātrā-based matching (NEW)
        matra_result = self._match_matra_meter(lg_pattern)
        if matra_result:
            meter_name, confidence = matra_result
            if meter_name not in seen_meters:
                results.append(((meter_name, ''), confidence, 'matra'))
                seen_meters.add(meter_name)

        # Level 6: Fuzzy matching (lowest confidence)
        if fuzzy and len(results) < max_fuzzy:
            fuzzy_results = self._fuzzy_match(lg_pattern, max_fuzzy - len(results))
            for meter_name, confidence, match_type in fuzzy_results:
                name = meter_name[0] if isinstance(meter_name, tuple) else meter_name
                if name not in seen_meters:
                    results.append((meter_name, confidence, match_type))
                    seen_meters.add(name)

        # Sort by confidence (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def _match_pada_patterns(self, lg_pattern):
        """
        Match pada-level patterns from database (Key improvement)

        This checks if individual padas match known patterns like:
        - Indravajrā (त त ज ग ग)
        - Vaṁśasthavila (ज त ज र)
        - etc.
        """
        results = []

        for num_padas in [4, 3, 2]:
            padas = self.split_into_padas(lg_pattern, num_padas)
            if not padas:
                continue

            first_pada = padas[0]

            # Check if first pada matches a known pattern
            if first_pada in self.PADA_INDEX:
                all_sama = all(pada == first_pada for pada in padas)

                for meter_name, base_conf, _source in self.PADA_INDEX[first_pada]:
                    # Skip Vedic family names if we're looking for specific meters
                    if meter_name in self.VEDIC_FAMILY_NAMES:
                        continue

                    if all_sama:
                        # All padas identical - Samavṛtta (highest pada confidence)
                        confidence = base_conf
                        results.append(((meter_name, ''), confidence, 'pada_exact_sama'))
                    else:
                        # Check if this could be Upajāti (handled separately)
                        # Or other ardhasamavṛtta
                        confidence = base_conf - 0.5
                        results.append(((meter_name, ''), confidence, 'pada_partial'))

            # Also check each pada individually
            for pada in padas:
                if pada in self.PADA_INDEX and pada != first_pada:
                    for meter_name, base_conf, _source in self.PADA_INDEX[pada]:
                        if meter_name in self.VEDIC_FAMILY_NAMES:
                            continue
                        confidence = base_conf - 1.0  # Lower confidence for mixed
                        existing = [r[0][0] if isinstance(r[0], tuple) else r[0] for r in results]
                        if meter_name not in existing:
                            results.append(((meter_name, ''), confidence, 'pada_mixed'))

            break  # Use first successful split

        return results

    def _detect_upajati(self, lg_pattern):
        """
        Detect 14 varieties of Upajāti

        Upajāti combines Indravajrā and Upendravajrā padas
        """
        if len(lg_pattern) != 44:  # 4 × 11 syllables
            return None

        padas = self.split_into_padas(lg_pattern, 4)
        if not padas:
            return None

        # Classify each pada as Indravajrā (इ) or Upendravajrā (उ)
        pada_types = []
        for pada in padas:
            # Use fuzzy matching with tolerance for real-world variations
            if self._pattern_matches(pada, self.INDRAVAJRA_PATTERN, tolerance=1):
                pada_types.append('इ')
            elif self._pattern_matches(pada, self.UPENDRAVAJRA_PATTERN, tolerance=1):
                pada_types.append('उ')
            else:
                return None  # Not an Upajāti

        # Check if all padas are same type (not Upajāti, but pure Indravajrā/Upendravajrā)
        if len(set(pada_types)) == 1:
            return None

        # Look up the specific Upajāti variety
        pada_tuple = tuple(pada_types)
        if pada_tuple in self.UPAJATI_VARIETIES:
            variety_name = self.UPAJATI_VARIETIES[pada_tuple]
            return ('उपजाति', variety_name)

        # Generic Upajāti (mixed but not named variety)
        return ('उपजाति', 'मिश्र')

    def _pattern_matches(self, pattern1, pattern2, tolerance=2):
        """Check if two patterns match within tolerance"""
        if len(pattern1) != len(pattern2):
            return False
        differences = sum(1 for a, b in zip(pattern1, pattern2, strict=False) if a != b)
        return differences <= tolerance

    def _match_vedic_pada(self, lg_pattern):
        """Match Vedic meters by pada syllable count (reduced confidence)"""
        results = []

        vedic_pada_meters = {
            7: ('उष्णिक्', 'Ushnik'),
            8: [('गायत्री', 'Gayatri'), ('अनुष्टुभ्', 'Anushtubh')],
            9: ('बृहती', 'Brihati'),
            11: ('त्रिष्टुभ्', 'Trishtubh'),
            12: ('जगती', 'Jagati'),
        }

        for num_padas in [4, 3, 2]:
            padas = self.split_into_padas(lg_pattern, num_padas)
            if not padas:
                continue

            pada_syllables = len(padas[0])

            if pada_syllables in vedic_pada_meters:
                candidates = vedic_pada_meters[pada_syllables]
                if not isinstance(candidates, list):
                    candidates = [candidates]

                all_sama = all(pada == padas[0] for pada in padas)

                for dev_name, _eng_name in candidates:
                    if all_sama:
                        confidence = 6.0  # REDUCED from 8.0
                        results.append(((dev_name, ''), confidence, 'vedic_pada_sama'))
                    else:
                        confidence = 5.5  # REDUCED from 6.5
                        results.append(((dev_name, ''), confidence, 'vedic_pada_vishama'))

            break

        return results

    def _identify_vedic_by_syllable(self, syllable_count):
        """Identify Vedic meter by total syllable count"""
        vedic_mapping = {24: 'गायत्री', 28: 'उष्णिक्', 32: 'अनुष्टुभ्', 36: 'बृहती', 40: 'पङ्क्ति', 44: 'त्रिष्टुभ्', 48: 'जगती'}

        # Exact match
        if syllable_count in vedic_mapping:
            return (vedic_mapping[syllable_count], '')

        # Vedic tolerance: ±1-2 syllables (from Chandovallari)
        for expected, meter in vedic_mapping.items():
            if abs(syllable_count - expected) <= 2:
                return (meter, '')

        return None

    def _match_matra_meter(self, lg_pattern):
        """Match mātrā-based meters (Āryā family)"""
        total_matra = self.count_matra(lg_pattern)

        # Check Āryā family patterns
        for meter_name, info in self.ARYA_FAMILY.items():
            expected_total = sum(info['matras'])
            if abs(total_matra - expected_total) <= 2:
                return (meter_name, 5.0)

        return None

    def _fuzzy_match(self, lg_pattern, max_results):
        """Fuzzy matching using Levenshtein distance"""
        results = []
        syllable_count = len(lg_pattern)

        for chanda_lg, chanda_names in self.CHANDA.items():
            if len(chanda_lg) == syllable_count:
                distance = Lev.distance(lg_pattern, chanda_lg)
                if distance <= 3:
                    similarity = 1 - (distance / len(chanda_lg))
                    confidence = similarity * 4.0

                    for name in chanda_names:
                        results.append((name, confidence, 'fuzzy'))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]
