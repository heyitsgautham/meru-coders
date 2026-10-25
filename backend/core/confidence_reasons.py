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
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from .confidence_explanations import MATCH_TYPE_EXPLANATIONS


class ConfidenceLevel(Enum):
    """Human-readable confidence level categories."""

    VERY_HIGH = "very_high"  # ≥9.0 - Exact pattern or validated match
    HIGH = "high"  # ≥7.0 - Structural/pada-level match
    MEDIUM = "medium"  # ≥5.0 - Syllable-based match
    LOW = "low"  # ≥3.0 - Fuzzy match with decent similarity
    VERY_LOW = "very_low"  # <3.0 - Low confidence fuzzy match


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
            'technical_details': self.technical_details,
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
    **kwargs,
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
    explanation = MATCH_TYPE_EXPLANATIONS.get(base_match_type, MATCH_TYPE_EXPLANATIONS['unknown'])

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
    except KeyError:
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
        technical_details=technical_details,
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
    confidence_scores: Dict[str, Tuple[float, str]], pattern: str = None, syllable_count: int = None, **kwargs
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
            **kwargs,
        )
        reasons[meter_name] = reason.to_dict()

    return reasons


def get_primary_confidence_reason(
    confidence_scores: Dict[str, Tuple[float, str]], pattern: str = None, syllable_count: int = None, **kwargs
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
        **kwargs,
    )

    return reason.to_dict()


# ============================================================================
# Utility Functions
# ============================================================================


def format_confidence_for_display(reason: Dict[str, Any], include_technical: bool = False) -> str:
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
