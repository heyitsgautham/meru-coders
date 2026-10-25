"""Explanation templates for every match type the confidence scoring system emits.

backend/core/confidence_reasons.py fills these templates to explain a score.
"""

from typing import Any, Dict

# ============================================================================
# MATCH TYPE EXPLANATIONS
# ============================================================================
# This dictionary contains templates for generating explanations for each
# match type used in the confidence scoring system.
#
# Each entry has:
#   - reason_template: English explanation template (supports {placeholders})
#   - description: Brief description of when this match type is used
#   - base_score: The typical confidence score for this match type
# ============================================================================

MATCH_TYPE_EXPLANATIONS: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # TIER 1: EXACT MATCHES (10.0)
    # =========================================================================
    'exact_pattern': {
        'reason_template': 'The L-G (laghu-guru) pattern "{pattern}" exactly matches the meter "{meter}" in the database.',
        'description': 'Direct pattern match in CHANDA dictionary',
        'base_score': 10.0,
    },
    'exact': {
        'reason_template': 'Exact match found - the pattern "{pattern}" directly corresponds to meter "{meter}".',
        'description': 'Alias for exact_pattern used in match_with_confidence',
        'base_score': 10.0,
    },
    # =========================================================================
    # TIER 1b: REGEX/VALIDATED MATCHES (9.0-9.8)
    # =========================================================================
    'exact_regex': {
        'reason_template': 'The pattern matches "{meter}" using flexible syllable positions. Some positions in this meter allow either L or G.',
        'description': 'Regex pattern match with wildcards (l/g = either)',
        'base_score': 9.0,
    },
    'vedic_classical_map': {
        'reason_template': 'This meter was identified through empirical Vedic-Classical mapping. Historical analysis shows "{meter}" frequently appears in Vedic texts with this pattern.',
        'description': 'SIH 2025 empirical mapping from Vedic to Classical meters',
        'base_score': 9.8,
    },
    'vedic_classical_map_exact_pattern': {
        'reason_template': 'Exact pattern match enhanced by Vedic-Classical mapping. The pattern matches "{meter}" which is a well-documented classical equivalent for Vedic compositions.',
        'description': 'Exact match boosted by Vedic-Classical empirical mapping',
        'base_score': 9.8,
    },
    'vedic_classical_map_fuzzy': {
        'reason_template': 'Fuzzy match enhanced by Vedic-Classical mapping. The pattern is similar to "{meter}" which frequently appears as a classical equivalent in Vedic texts.',
        'description': 'Fuzzy match boosted by Vedic-Classical empirical mapping',
        'base_score': 9.8,
    },
    # =========================================================================
    # TIER 1c: VEDIC SYLLABLE PRIORITY (9.5-11.0)
    # =========================================================================
    'vedic_syllable_priority': {
        'reason_template': 'Identified as Vedic meter "{meter}" based on syllable count ({syllables} syllables). This is the primary identification as no classical pattern match was found.',
        'description': 'Vedic meter by syllable count when no classical match exists',
        'base_score': 11.0,
    },
    'vedic_syllable_secondary': {
        'reason_template': 'Also matches Vedic meter "{meter}" by syllable count ({syllables} syllables). A classical meter with exact pattern match takes precedence.',
        'description': 'Vedic meter as secondary option when classical match exists',
        'base_score': 9.5,
    },
    # =========================================================================
    # TIER 2: STRUCTURAL/PADA MATCHES (7.5-9.0)
    # =========================================================================
    'pada_exact_sama': {
        'reason_template': 'All {num_padas} padas (quarters) have identical patterns matching "{meter}". This "sama" (uniform) structure is characteristic of this meter.',
        'description': 'All padas identical - sama vṛtta pattern',
        'base_score': 9.0,
    },
    'pada_sama': {
        'reason_template': 'Identified through sama (uniform) pada structure. All {num_padas} padas share the same pattern, typical of "{meter}".',
        'description': 'Sama pada structure match',
        'base_score': 9.0,
    },
    'pada_vedic_sama': {
        'reason_template': 'Vedic meter "{meter}" identified by uniform pada structure. All {num_padas} padas have {syllables_per_pada} syllables each with identical patterns.',
        'description': 'Vedic meter with sama pada structure',
        'base_score': 8.0,
    },
    'pada_similar': {
        'reason_template': 'The {num_padas} padas have similar (but not identical) patterns. Each pada differs by at most {max_difference} syllables from the expected pattern of "{meter}".',
        'description': 'Padas within Levenshtein distance tolerance',
        'base_score': 7.5,
    },
    'pada_vishama': {
        'reason_template': 'Identified as vishama (varied) meter "{meter}". The padas have intentionally different patterns following a known alternating structure.',
        'description': 'Vishama vṛtta - intentionally varied pada patterns',
        'base_score': 7.5,
    },
    'pada_vedic_similar': {
        'reason_template': 'Vedic meter "{meter}" identified with slight pada variations. The pattern approximates the expected {syllables_per_pada}-syllable pada structure.',
        'description': 'Vedic meter with similar (not exact) pada structure',
        'base_score': 6.5,
    },
    # =========================================================================
    # TIER 3: SYLLABLE COUNT MATCHES (4.0-6.0)
    # =========================================================================
    'vedic_syllable': {
        'reason_template': 'Identified as Vedic meter "{meter}" based on syllable count alone ({syllables} syllables). This matches the expected count for {meter_family} family meters.',
        'description': 'Vedic meter by syllable count only',
        'base_score': 6.0,
    },
    'vedic_range_fallback': {
        'reason_template': 'Identified as Vedic meter "{meter}" - syllable count ({syllables}) falls within the acceptable range ({range_low}-{range_high}) for this meter, {distance} syllables from the peak of {peak}.',
        'description': 'Vedic meter by syllable range with tolerance',
        'base_score': 7.0,  # Variable: 7.0-11.0 based on distance from peak
    },
    'syllable_count': {
        'reason_template': 'Matched by syllable count ({syllables} syllables). Multiple meters share this syllable count, so this is a less certain identification.',
        'description': 'Generic syllable count match - lower confidence',
        'base_score': 4.0,
    },
    # =========================================================================
    # TIER 4: FUZZY MATCHES (1.0-4.0)
    # =========================================================================
    'fuzzy': {
        'reason_template': 'Pattern similarity match to "{meter}". The input pattern is {similarity_pct}% similar to the expected pattern (Levenshtein distance: {distance}).',
        'description': 'Levenshtein distance-based fuzzy match',
        'base_score': 2.5,  # Variable: 1.0-4.0 based on similarity
    },
    'fuzzy_fallback_exact': {
        'reason_template': 'Close pattern match found for "{meter}" via fuzzy search. The pattern has minor variations ({distance} differences) from the canonical form.',
        'description': 'Fuzzy match that found a near-exact pattern',
        'base_score': 3.5,
    },
    'fuzzy_fallback_fuzzy': {
        'reason_template': 'Approximate match to "{meter}" found via extended search. Pattern similarity: {similarity_pct}% ({distance} character differences).',
        'description': 'Fuzzy match as fallback when no exact match',
        'base_score': 3.0,
    },
    # =========================================================================
    # SPECIAL CASES
    # =========================================================================
    'matra_meter': {
        'reason_template': 'Identified as mātrā-based meter "{meter}". The mātrā (mora) count of each pada ({matra_sequence}) matches the expected pattern.',
        'description': 'Mātrā-based meter identification',
        'base_score': 8.0,
    },
    'jaati_meter': {
        'reason_template': 'Classified as jāti "{meter}" based on total mātrā count ({total_matra}). Jāti meters are defined by mātrā totals rather than specific L-G patterns.',
        'description': 'Jāti (mātrā-based family) identification',
        'base_score': 7.0,
    },
    'composite_structure': {
        'reason_template': 'Identified as composite meter "{meter}". This verse combines elements from multiple meters in a recognized composite structure.',
        'description': 'Composite/pragātha structure',
        'base_score': 7.5,
    },
    'pankti_discriminator': {
        'reason_template': 'Identified as "{meter}" using Paṅkti-family discrimination. The pattern structure distinguishes this from other 40-syllable meters.',
        'description': 'Paṅkti family discrimination',
        'base_score': 8.0,
    },
    'peak_based': {
        'reason_template': 'Identified as "{meter}" based on syllable count alignment with statistical peak ({peak} syllables). Historical analysis shows most {meter} verses have this count.',
        'description': 'Peak-based statistical identification',
        'base_score': 7.0,
    },
    'fallback_exact': {
        'reason_template': 'Secondary exact match found for "{meter}" after primary identification methods. This provides additional confidence.',
        'description': 'Fallback exact match',
        'base_score': 8.0,
    },
    # Unknown/default case
    'unknown': {
        'reason_template': 'Match type not recognized. The meter "{meter}" was identified with confidence {confidence}.',
        'description': 'Unknown match type - should not normally occur',
        'base_score': 5.0,
    },
}
