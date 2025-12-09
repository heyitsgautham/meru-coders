#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confidence Scoring Reasons Module

Provides detailed human-readable explanations for confidence scores
in meter (chandas) identification.

This module handles all match types from the multi-level confidence scoring
system in chanda.py, converting numeric scores and match type codes into
comprehensive explanations.

Confidence Score Scale: 0.0 - 11.0
- 10.0-11.0: Exact matches (highest confidence)
- 9.0-9.8: Validated/regex pattern matches  
- 7.5-8.0: Structural pada-level matches
- 6.0-6.5: Syllable-based matches
- 4.0-5.0: Fallback matches
- 1.0-4.0: Fuzzy matches (lowest confidence)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum


class ConfidenceLevel(Enum):
    """Human-readable confidence level categories."""
    VERY_HIGH = "very_high"    # ≥9.0 - Exact pattern or validated match
    HIGH = "high"              # ≥7.0 - Structural/pada-level match
    MEDIUM = "medium"          # ≥5.0 - Syllable-based match
    LOW = "low"                # ≥3.0 - Fuzzy match with decent similarity
    VERY_LOW = "very_low"      # <3.0 - Low confidence fuzzy match


@dataclass
class ConfidenceReason:
    """
    Detailed explanation for a confidence score.
    
    Attributes:
        match_type: Internal match type code (e.g., 'exact_pattern')
        confidence: Numeric confidence score (0.0-11.0)
        level: Human-readable confidence level
        reason: English explanation of why this score was assigned
        technical_details: Additional technical information for debugging/analysis
    """
    match_type: str
    confidence: float
    level: ConfidenceLevel
    reason: str
    technical_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'match_type': self.match_type,
            'confidence': self.confidence,
            'level': self.level.value,
            'reason': self.reason,
            'technical_details': self.technical_details
        }


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


def get_confidence_level(confidence_score: float) -> ConfidenceLevel:
    """
    Convert numeric confidence score to categorical level.
    
    Args:
        confidence_score: Numeric score (0.0-11.0)
    
    Returns:
        ConfidenceLevel enum value
    """
    if confidence_score >= 9.0:
        return ConfidenceLevel.VERY_HIGH
    elif confidence_score >= 7.0:
        return ConfidenceLevel.HIGH
    elif confidence_score >= 5.0:
        return ConfidenceLevel.MEDIUM
    elif confidence_score >= 3.0:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.VERY_LOW


def get_confidence_reason(
    match_type: str,
    confidence: float,
    meter_name: str = '',
    pattern: str = None,
    syllable_count: int = None,
    num_padas: int = None,
    syllables_per_pada: int = None,
    similarity: float = None,
    distance: int = None,
    range_low: int = None,
    range_high: int = None,
    peak: int = None,
    matra_sequence: str = None,
    total_matra: int = None,
    max_difference: int = None,
    **kwargs
) -> ConfidenceReason:
    """
    Generate a detailed confidence reason from match data.
    
    This function takes the raw match information from the chanda.py
    identification engine and generates a human-readable explanation
    with full technical details.
    
    Args:
        match_type: Internal match type code (e.g., 'exact_pattern', 'fuzzy')
        confidence: Numeric confidence score (0.0-11.0)
        meter_name: Name of the identified meter
        pattern: The L-G pattern string
        syllable_count: Total number of syllables
        num_padas: Number of padas (quarters) detected
        syllables_per_pada: Syllables per pada for sama meters
        similarity: Fuzzy match similarity (0.0-1.0)
        distance: Levenshtein distance for fuzzy matches
        range_low: Lower bound of Vedic meter syllable range
        range_high: Upper bound of Vedic meter syllable range
        peak: Statistical peak syllable count for Vedic meters
        matra_sequence: Mātrā pattern for mātrā-based meters
        total_matra: Total mātrā count for jāti identification
        max_difference: Maximum pada difference for similar matches
        **kwargs: Additional context data
    
    Returns:
        ConfidenceReason object with complete explanation
    """
    # Handle compound match types (e.g., 'vedic_classical_map_exact_pattern')
    base_match_type = match_type
    for key in MATCH_TYPE_EXPLANATIONS:
        if match_type.startswith(key) and key != 'unknown':
            base_match_type = key
            break
    
    # Get the explanation template
    explanation = MATCH_TYPE_EXPLANATIONS.get(
        base_match_type,
        MATCH_TYPE_EXPLANATIONS['unknown']
    )
    
    # Calculate similarity percentage for fuzzy matches
    similarity_pct = None
    if similarity is not None:
        similarity_pct = round(similarity * 100, 1)
    elif distance is not None and pattern:
        similarity_pct = round((1 - distance / len(pattern)) * 100, 1)
    
    # Calculate distance from peak for range matches
    distance_from_peak = None
    if peak is not None and syllable_count is not None:
        distance_from_peak = abs(syllable_count - peak)
    
    # Determine meter family for Vedic meters
    meter_family = _get_vedic_meter_family(meter_name, syllable_count)
    
    # Build the reason string from template
    reason_template = explanation['reason_template']
    
    # Prepare template variables
    template_vars = {
        'meter': meter_name or 'Unknown',
        'pattern': pattern or '',
        'syllables': syllable_count or 0,
        'num_padas': num_padas or 4,
        'syllables_per_pada': syllables_per_pada or (syllable_count // 4 if syllable_count else 0),
        'similarity_pct': similarity_pct or 0,
        'distance': distance or 0,
        'range_low': range_low or 0,
        'range_high': range_high or 0,
        'peak': peak or 0,
        'matra_sequence': matra_sequence or '',
        'total_matra': total_matra or 0,
        'max_difference': max_difference or 2,
        'meter_family': meter_family,
        'confidence': confidence,
    }
    
    # Format the reason string
    try:
        reason = reason_template.format(**template_vars)
    except KeyError as e:
        # Fallback if template variable is missing
        reason = f"Meter '{meter_name}' identified with confidence {confidence:.1f} (match type: {match_type})"
    
    # Build technical details
    technical_details = {
        'match_type_raw': match_type,
        'base_match_type': base_match_type,
        'base_score': explanation['base_score'],
        'description': explanation['description'],
    }
    
    # Add optional technical details
    if pattern:
        technical_details['pattern'] = pattern
        technical_details['pattern_length'] = len(pattern)
    
    if syllable_count:
        technical_details['syllable_count'] = syllable_count
    
    if num_padas:
        technical_details['num_padas'] = num_padas
        if syllables_per_pada:
            technical_details['syllables_per_pada'] = syllables_per_pada
    
    if similarity_pct is not None:
        technical_details['similarity_percentage'] = similarity_pct
    
    if distance is not None:
        technical_details['levenshtein_distance'] = distance
    
    if range_low is not None and range_high is not None:
        technical_details['vedic_range'] = {'low': range_low, 'high': range_high}
        if peak:
            technical_details['vedic_peak'] = peak
            if distance_from_peak is not None:
                technical_details['distance_from_peak'] = distance_from_peak
    
    if matra_sequence:
        technical_details['matra_sequence'] = matra_sequence
    
    if total_matra:
        technical_details['total_matra'] = total_matra
    
    # Add any extra context
    for key, value in kwargs.items():
        if value is not None and key not in technical_details:
            technical_details[key] = value
    
    # Create and return the ConfidenceReason
    return ConfidenceReason(
        match_type=match_type,
        confidence=confidence,
        level=get_confidence_level(confidence),
        reason=reason,
        technical_details=technical_details
    )


def _get_vedic_meter_family(meter_name: str, syllable_count: int = None) -> str:
    """
    Determine the Vedic meter family for a given meter.
    
    Args:
        meter_name: Name of the meter
        syllable_count: Total syllable count (optional, used as fallback)
    
    Returns:
        Family name string
    """
    # Known Vedic meter families by name
    meter_families = {
        # Gāyatrī family (24 syllables)
        'गायत्री': 'Gāyatrī',
        'gayatri': 'Gāyatrī',
        'gāyatrī': 'Gāyatrī',
        
        # Uṣṇik family (28 syllables)
        'उष्णिक्': 'Uṣṇik',
        'usnik': 'Uṣṇik',
        'uṣṇik': 'Uṣṇik',
        
        # Anuṣṭubh family (32 syllables)
        'अनुष्टुभ्': 'Anuṣṭubh',
        'anustubh': 'Anuṣṭubh',
        'anuṣṭubh': 'Anuṣṭubh',
        
        # Bṛhatī family (36 syllables)
        'बृहती': 'Bṛhatī',
        'brhati': 'Bṛhatī',
        'bṛhatī': 'Bṛhatī',
        
        # Paṅkti family (40 syllables)
        'पङ्क्ति': 'Paṅkti',
        'pankti': 'Paṅkti',
        'paṅkti': 'Paṅkti',
        
        # Triṣṭubh family (44 syllables)
        'त्रिष्टुभ्': 'Triṣṭubh',
        'tristubh': 'Triṣṭubh',
        'triṣṭubh': 'Triṣṭubh',
        
        # Jagatī family (48 syllables)
        'जगती': 'Jagatī',
        'jagati': 'Jagatī',
        'jagatī': 'Jagatī',
    }
    
    # Try to find by meter name
    meter_lower = meter_name.lower() if meter_name else ''
    for key, family in meter_families.items():
        if key.lower() in meter_lower or meter_lower in key.lower():
            return family
    
    # Fallback to syllable count
    if syllable_count:
        syllable_families = {
            24: 'Gāyatrī',
            28: 'Uṣṇik',
            32: 'Anuṣṭubh',
            36: 'Bṛhatī',
            40: 'Paṅkti',
            44: 'Triṣṭubh',
            48: 'Jagatī',
        }
        
        # Check exact match first
        if syllable_count in syllable_families:
            return syllable_families[syllable_count]
        
        # Check within range (±4 syllables)
        for count, family in syllable_families.items():
            if abs(syllable_count - count) <= 4:
                return family
    
    return 'Classical'


def build_confidence_reasons(
    confidence_scores: Dict[str, Tuple[float, str]],
    pattern: str = None,
    syllable_count: int = None,
    **kwargs
) -> Dict[str, Dict[str, Any]]:
    """
    Build confidence reasons for all meters in a confidence_scores dict.
    
    This is a convenience function to convert the entire confidence_scores
    dictionary from chanda.py into detailed reasons.
    
    Args:
        confidence_scores: Dict of meter_name -> (confidence, match_type)
        pattern: The L-G pattern string
        syllable_count: Total syllable count
        **kwargs: Additional context passed to each reason
    
    Returns:
        Dict of meter_name -> ConfidenceReason.to_dict()
    """
    reasons = {}
    
    for meter_name, (confidence, match_type) in confidence_scores.items():
        reason = get_confidence_reason(
            match_type=match_type,
            confidence=confidence,
            meter_name=meter_name,
            pattern=pattern,
            syllable_count=syllable_count or (len(pattern) if pattern else None),
            **kwargs
        )
        reasons[meter_name] = reason.to_dict()
    
    return reasons


def get_primary_confidence_reason(
    confidence_scores: Dict[str, Tuple[float, str]],
    pattern: str = None,
    syllable_count: int = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Get the confidence reason for the highest-confidence meter.
    
    Args:
        confidence_scores: Dict of meter_name -> (confidence, match_type)
        pattern: The L-G pattern string
        syllable_count: Total syllable count
        **kwargs: Additional context
    
    Returns:
        ConfidenceReason.to_dict() for the primary meter, or None if empty
    """
    if not confidence_scores:
        return None
    
    # Find highest confidence meter
    primary_meter = max(confidence_scores.items(), key=lambda x: x[1][0])
    meter_name, (confidence, match_type) = primary_meter
    
    reason = get_confidence_reason(
        match_type=match_type,
        confidence=confidence,
        meter_name=meter_name,
        pattern=pattern,
        syllable_count=syllable_count or (len(pattern) if pattern else None),
        **kwargs
    )
    
    return reason.to_dict()


# ============================================================================
# Utility Functions
# ============================================================================

def format_confidence_for_display(
    reason: Dict[str, Any],
    include_technical: bool = False
) -> str:
    """
    Format a confidence reason for display in UI.
    
    Args:
        reason: ConfidenceReason.to_dict() output
        include_technical: Whether to include technical details
    
    Returns:
        Formatted string for display
    """
    level = reason.get('level', 'medium')
    confidence = reason.get('confidence', 0)
    reason_text = reason.get('reason', '')
    
    # Map level to display text
    level_display = {
        'very_high': 'Very High',
        'high': 'High',
        'medium': 'Medium',
        'low': 'Low',
        'very_low': 'Very Low',
    }
    
    output = f"**Confidence:** {level_display.get(level, 'Unknown')} ({confidence:.1f}/10)\n\n"
    output += f"**Why:** {reason_text}"
    
    if include_technical:
        tech = reason.get('technical_details', {})
        if tech:
            output += "\n\n**Technical Details:**\n"
            for key, value in tech.items():
                if key not in ['match_type_raw', 'base_match_type', 'description']:
                    output += f"- {key}: {value}\n"
    
    return output
