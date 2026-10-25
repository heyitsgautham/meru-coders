"""Fallbacks for Chanda.identify_line when no meter pattern matches the line exactly.

Mixed into backend.core.chanda.Chanda; methods rely on its other mixins through self.
They run in order: structural and syllable-count heuristics, the empirical
Vedic-to-classical confidence map, fuzzy pattern matching, and finally the
Vedic syllable-range match. Each adds meters to the line's ``chanda`` list and
``confidence_map`` in place.
"""

from .chanda_constants import (
    CONFIDENCE_VEDIC_CLASSICAL_MAP,
    VEDIC_MAPPINGS_AVAILABLE,
    get_classical_equivalents,
    normalize_vedic_meter,
)

# Vedic meter names in every spelling the tables use. A fuzzy match to one of
# these does not block the Vedic range fallback; a classical match does.
VEDIC_METER_NAMES = frozenset(
    name.lower()
    for name in (
        'गायत्री',
        'gāyatrī',
        'gayatri',
        'Gāyatrī',
        'त्रिष्टुभ्',
        'triṣṭubh',
        'tristubh',
        'Triṣṭubh',
        'जगती',
        'jagatī',
        'jagati',
        'Jagatī',
        'अनुष्टुभ्',
        'anuṣṭubh',
        'anustubh',
        'Anuṣṭubh',
        'उष्णिक्',
        'uṣṇik',
        'usnik',
        'बृहती',
        'bṛhatī',
        'brhati',
        'पङ्क्ति',
        'paṅkti',
        'pankti',
        'प्रगाथ',
        'pragātha',
        'pragatha',
        'विराट्',
        'virāṭ',
        'virat',
    )
)

# Priority of each Vedic meter in the range fallback; higher is more common in the Rigveda.
METER_FREQUENCY_WEIGHT = {
    'त्रिष्टुभ्': 100,  # 3727 verses in Rigveda
    'गायत्री': 100,  # 2171 verses
    'जगती': 100,  # 1070 verses
    'अनुष्टुभ्': 100,  # 656 verses
    'उष्णिक्': 80,  # 448 verses
    'बृहती': 70,  # 269 verses
    'पङ्क्ति': 70,  # 204 verses
    # Rare/composite meters - lower priority
    'प्रगाथ': 50,  # Composite
    'विराट्': 30,  # Rare
    'ज्योतिस्': 20,  # Rare, requires refrain
    'महापङ्क्ति': 20,  # Rare, requires refrain
    'ककुभ्': 30,  # 3-pada structure
    'द्विपदा त्रिष्टुभ्': 30,
}

# Below this confidence a line counts as unidentified and the next fallback runs.
WEAK_CONFIDENCE = 5.0


class LineFallbackMixin:
    def _heuristic_line_matches(
        self,
        lg_str,
        fuzzy,
        k,
        syllable_count,
        vedic_syllable_counts,
        vedic_priority_meter,
        chanda,
        confidence_map,
        found,
    ):
        """Fill chanda and confidence_map for a line with no exact pattern match; return the new found flag."""
        # TIER 2: pada-level structure beats a bare syllable count, which beats fuzzy similarity.
        pada_matches, syllable_matches, fuzzy_matches = self._group_heuristic_matches(
            self.match_with_confidence(lg_str, fuzzy=fuzzy, max_fuzzy=k)
        )
        if pada_matches:
            self._add_line_matches(pada_matches, chanda, confidence_map)
            found = True
        elif syllable_matches:
            # Only the top 3 syllable matches, to avoid flooding
            self._add_line_matches(syllable_matches[:3], chanda, confidence_map)
            found = True
        elif fuzzy_matches:
            self._add_line_matches(fuzzy_matches, chanda, confidence_map)
            found = True

        self._apply_vedic_classical_line_map(vedic_priority_meter, confidence_map)

        # Fuzzy pattern matching catches variants such as a Sragdharā with one L-G difference.
        # It runs before the Vedic range fallback so pattern-based matches survive.
        max_existing_confidence = max((conf for conf, _ in confidence_map.values()), default=0)
        has_classical_fuzzy_match = False
        if max_existing_confidence < WEAK_CONFIDENCE and not fuzzy:
            added, has_classical_fuzzy_match = self._fuzzy_pattern_fallback(lg_str, k, chanda, confidence_map)
            if added:
                found = True
            max_existing_confidence = max((conf for conf, _ in confidence_map.values()), default=0)

        # The Vedic syllable-range match handles real Rigveda lines a few syllables off the
        # standard counts, unless a classical meter already matched by fuzzy pattern.
        needs_vedic_fallback = (
            max_existing_confidence < WEAK_CONFIDENCE
            and syllable_count not in vedic_syllable_counts
            and not has_classical_fuzzy_match
        )
        if needs_vedic_fallback:
            range_match = self._vedic_range_match(syllable_count)
            if range_match:
                meter_name, confidence = range_match
                confidence_map[meter_name] = (confidence, 'vedic_range_fallback')
                chanda.insert(0, (meter_name, ('',)))
                found = True
        return found

    @staticmethod
    def _group_heuristic_matches(multi_level_matches):
        """Split match_with_confidence results into pada-level, syllable-count and fuzzy matches."""
        pada_matches = []
        syllable_matches = []
        fuzzy_matches = []
        for match_item, confidence, match_type in multi_level_matches:
            meter_tuple = match_item if isinstance(match_item, tuple) else (match_item, ('',))
            if match_type in ['pada_sama', 'pada_vishama']:
                pada_matches.append((meter_tuple, confidence, match_type))
            elif match_type in ['vedic_syllable', 'syllable_count']:
                syllable_matches.append((meter_tuple, confidence, match_type))
            elif match_type == 'fuzzy':
                fuzzy_matches.append((meter_tuple, confidence, match_type))
        return pada_matches, syllable_matches, fuzzy_matches

    @staticmethod
    def _add_line_matches(matches, chanda, confidence_map):
        """Record each meter's first confidence and append it to chanda once."""
        for meter_tuple, conf, mtype in matches:
            meter_name = meter_tuple[0] if isinstance(meter_tuple, tuple) else meter_tuple
            if meter_name not in confidence_map:
                confidence_map[meter_name] = (conf, mtype)
                if meter_tuple not in chanda:
                    chanda.append(meter_tuple)

    @staticmethod
    def _apply_vedic_classical_line_map(vedic_priority_meter, confidence_map):
        """Raise classical predictions that empirically map to the line's Vedic meter.

        For example a Vedic line predicted as ऋषभगजविलसित, which matches the
        चतुष्पदा भुरिग्जगती mapping 46 times in 47, gets the mapping confidence.
        """
        if not (VEDIC_MAPPINGS_AVAILABLE and vedic_priority_meter and confidence_map):
            return
        classical_equivalents = get_classical_equivalents(vedic_priority_meter)
        if not classical_equivalents:
            return
        for equiv_name in classical_equivalents[:3]:  # Top 3 mappings
            for meter_name in list(confidence_map.keys()):
                if normalize_vedic_meter(meter_name) == normalize_vedic_meter(equiv_name):
                    current_conf, current_type = confidence_map[meter_name]
                    if current_conf < CONFIDENCE_VEDIC_CLASSICAL_MAP:
                        confidence_map[meter_name] = (
                            CONFIDENCE_VEDIC_CLASSICAL_MAP,
                            f'vedic_classical_map_{current_type}',
                        )

    def _fuzzy_pattern_fallback(self, lg_str, k, chanda, confidence_map):
        """Add fuzzy pattern matches of confidence 3 or more; return (added any, added a classical meter)."""
        added = False
        has_classical = False
        for meter_tuple, confidence, match_type in self.match_with_confidence(lg_str, fuzzy=True, max_fuzzy=k):
            meter_name = meter_tuple[0]
            # Only actual pattern matches, not syllable-count-only ones
            if confidence >= 3.0 and match_type in ['fuzzy', 'exact']:
                if meter_name not in confidence_map or confidence > confidence_map[meter_name][0]:
                    confidence_map[meter_name] = (confidence, f'fuzzy_fallback_{match_type}')
                    if meter_tuple not in chanda:
                        chanda.append(meter_tuple)
                    added = True
                    if meter_name.lower() not in VEDIC_METER_NAMES:
                        has_classical = True
        return added, has_classical

    def _vedic_range_match(self, syllable_count):
        """(meter, confidence) for the Vedic meter whose syllable range best fits, or None.

        Each candidate scores its frequency weight minus 10 per syllable from the meter's
        peak count; Jyotis and Mahāpaṅkti are skipped because they need a refrain.
        """
        vedic_range_matches = []
        for meter_name, (low, high) in self.VEDIC_METER_RANGES.items():
            if low <= syllable_count <= high:
                if meter_name in ['ज्योतिस्', 'महापङ्क्ति']:
                    continue
                peak = self.VEDIC_METER_PEAKS.get(meter_name, (low + high) // 2)
                diff = abs(syllable_count - peak)
                freq_weight = METER_FREQUENCY_WEIGHT.get(meter_name, 10)
                score = freq_weight - diff * 10
                vedic_range_matches.append((meter_name, diff, peak, score))
        if not vedic_range_matches:
            return None
        vedic_range_matches.sort(key=lambda x: -x[3])
        best_match = vedic_range_matches[0]
        # Confidence based on distance from peak
        return best_match[0], max(7.0, 11.0 - best_match[1] * 0.5)
