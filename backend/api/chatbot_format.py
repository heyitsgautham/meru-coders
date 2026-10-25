"""Turning meter analysis results into the chatbot's Markdown replies."""

import re
from typing import Any, Dict, List


def extract_primary_meter_name(meter_display: str) -> str:
    """
    Extract just the primary meter name from verbose display format
    Handles both pipe (|) and slash (/) separators
    Example: "इन्द्रवज्रा (indravajrā) [10.0] | त्रिष्टुभ् (पाद 1)..." -> "इन्द्रवज्रा (indravajrā)"
    Example: "इन्द्रवज्रा / त्रिष्टुभ् (पाद 1) / त्रिष्टुभ् (पाद 2)..." -> "इन्द्रवज्रा"
    """
    if not meter_display:
        return "Unknown"

    # Split by pipe or slash separator to get first meter
    first_part = re.split(r'\s*[|/]\s*', meter_display)[0].strip()

    # Remove confidence score in brackets [10.0]
    cleaned = re.sub(r'\s*\[\d+\.?\d*\]\s*', '', first_part).strip()

    # Remove transliteration in parentheses if it's after the Devanagari name
    # Keep it if the whole name is in parentheses
    # Pattern: "sanskrit_text (transliteration)" -> "sanskrit_text"
    # But keep: "(transliteration only)"
    if '(' in cleaned:
        # Check if Devanagari characters exist before parentheses
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', cleaned.split('(')[0]))
        if has_devanagari:
            # Remove the transliteration part
            cleaned = re.sub(r'\s*\([^)]*\)\s*', '', cleaned).strip()

    return cleaned if cleaned else "Unknown"


def format_lg_padas(lg_padas: List[str]) -> str:
    """Format a list of L-G patterns split by pada into markdown bullet list."""
    if not lg_padas:
        return ""
    formatted = []
    for idx, pada in enumerate(lg_padas, 1):
        formatted.append(f"- **Pada {idx}:** {pada}")
    return "\n".join(formatted)


def get_confidence_label(confidence_score: float) -> str:
    """Convert numeric confidence score to human-readable label"""
    if confidence_score >= 9.0:
        return "Very High"
    elif confidence_score >= 7.0:
        return "High"
    elif confidence_score >= 5.0:
        return "Medium"
    elif confidence_score >= 3.0:
        return "Low"
    else:
        return "Very Low"


def split_lg_pattern_by_pada(lg_pattern: str, syllables_per_pada: int = None) -> str:
    """
    Split L-G pattern by pada (quarter) for better readability
    Returns formatted string with each pada on a separate line
    """
    if not lg_pattern:
        return ""

    total_syllables = len(lg_pattern)

    # Auto-detect pada structure if not specified
    if syllables_per_pada is None:
        # Common pada structures
        if total_syllables % 4 == 0:
            syllables_per_pada = total_syllables // 4
        elif total_syllables % 2 == 0:
            syllables_per_pada = total_syllables // 2
        else:
            # No clear pada structure, show as single line
            return lg_pattern

    # Split into padas
    padas = []
    for i in range(0, total_syllables, syllables_per_pada):
        pada = lg_pattern[i : i + syllables_per_pada]
        if pada:
            padas.append(pada)

    # Format with each pada on a new line with pada number
    formatted_padas = []
    for idx, pada in enumerate(padas, 1):
        formatted_padas.append(f"- **Pada {idx}:** {pada}")

    # Use single newline - bullet points work better in markdown
    return "\n".join(formatted_padas)


def format_meter_response(
    meter_data: Dict[str, Any],
    persona: str = 'default',
    requested_fields: Dict[str, bool] = None,
    add_analyze_link: bool = False,
) -> str:
    """
    Format meter analysis data into a conversational response
    Formats response based on what fields user specifically requested
    """
    # Handle validation errors (invalid Sanskrit input)
    if not meter_data.get('success'):
        # Check if this is a validation error (invalid input)
        if meter_data.get('is_valid_input') is False:
            response = "**Invalid Input**\n\n"
            response += "Please enter valid Sanskrit text.\n\n"
            response += "Use Devanagari (देवनागरी) or IAST with diacritics (dharmakṣetre)"

            return response

        # Generic error
        return f"I encountered an error analyzing the text: {meter_data.get('error', 'Unknown error')}"

    if not meter_data.get('found'):
        response = (
            f"I have analyzed the text **'{meter_data['text']}'** but could not definitively identify the meter.\n\n"
        )
        response += "**Analysis:**\n"
        response += f"- Syllable count: **{meter_data['syllables']}**\n"
        response += f"- L-G Pattern: `{meter_data['lg_pattern']}`\n"
        response += f"- Gana Pattern: `{meter_data['gana_pattern']}`\n"
        response += f"- Matra count: **{meter_data['matra']}**\n\n"

        if meter_data.get('fuzzy_matches'):
            response += "**Possible matches (fuzzy):**\n"
            for match in meter_data['fuzzy_matches'][:3]:
                response += f"- {match[0]} (similarity: {match[1]:.2f})\n"

        if add_analyze_link:
            # URL encode the text for the link
            import urllib.parse

            encoded_text = urllib.parse.quote(meter_data.get('text', ''))
            analyze_url = f"/app?text={encoded_text}"
            response += f"\n---\n💡 **Tip:** Use the [**Analyse Chanda**]({analyze_url}) page for detailed analysis with visualizations.\n"

        return response

    # Default requested_fields if not provided
    if requested_fields is None:
        requested_fields = {'full_analysis': True}

    # Successful identification
    response = ""

    # Extract confidence information from the new confidence_reason structure
    confidence_reason = meter_data.get('confidence_reason')
    confidence_score = 0.0
    confidence_level = "High"  # Default
    confidence_reason_text = ""

    if confidence_reason:
        confidence_score = confidence_reason.get('confidence', 0.0)
        confidence_level = confidence_reason.get('level', 'high').replace('_', ' ').title()
        confidence_reason_text = confidence_reason.get('reason', '')
    else:
        # Fallback: Extract confidence score from meter_display if confidence_reason not available
        import re

        if meter_data.get('meter_display'):
            match = re.search(r'\[(\d+\.?\d*)\]', meter_data['meter_display'])
            if match:
                score = float(match.group(1))
                confidence_score = score
                confidence_level = get_confidence_label(score)

    # Check if user asked for specific fields only
    specific_fields_requested = any(
        [
            requested_fields.get('meter_name'),
            requested_fields.get('lg_pattern'),
            requested_fields.get('gana_pattern'),
            requested_fields.get('syllable_count'),
            requested_fields.get('matra_count'),
        ]
    )

    if specific_fields_requested:
        # PRECISION MODE - Show only what user asked for

        # Show meter name if requested (with confidence score and reason)
        if requested_fields.get('meter_name'):
            # Extract primary meter name (without all the pada variations)
            primary_meter = extract_primary_meter_name(meter_data.get('meter_display') or meter_data['meter'])

            response += f"**Chanda:** {primary_meter}\n"
            response += f"**Confidence:** {confidence_level} ({confidence_score:.1f}/10)\n"
            if confidence_reason_text:
                response += f"**Why:** {confidence_reason_text}\n"

        # Show L-G pattern if requested (split by pada)
        if requested_fields.get('lg_pattern'):
            lg_pattern = meter_data['lg_pattern']
            # Prefer explicit pada list if available
            lg_padas = [p for p in meter_data.get('lg_pattern_padas', []) if p]
            if lg_padas:
                formatted_lg = format_lg_padas(lg_padas)
            else:
                formatted_lg = split_lg_pattern_by_pada(lg_pattern)
            response += f"**L-G Pattern (by Pada):**\n{formatted_lg}\n\n"

        # Show gana pattern if requested
        if requested_fields.get('gana_pattern'):
            response += f"**Gana Pattern:** `{meter_data['gana_pattern']}`\n"

        # Show syllable count if requested
        if requested_fields.get('syllable_count'):
            response += f"**Syllable Count:** {meter_data['syllables']}\n"

        # Show matra count if requested
        if requested_fields.get('matra_count'):
            response += f"**Matra Count:** {meter_data['matra']}\n"

    else:
        # FULL ANALYSIS MODE - Show complete information (clean format)

        # Format text properly - show each line on separate line for multi-line verses
        if meter_data.get('is_multi_line'):
            response += f"**Sanskrit Verse ({meter_data.get('verse_lines', 2)} lines):**\n"
            for line in meter_data['text'].split('\n'):
                if line.strip():
                    response += f"> {line.strip()}\n"
            response += "\n"
        else:
            response += f"**Sanskrit Text:** {meter_data['text']}\n\n"

        # Clean meter display - extract primary meter with confidence label
        primary_meter = extract_primary_meter_name(meter_data.get('meter_display') or meter_data['meter'])

        # Show meter with confidence score and reason
        response += f"**Chanda:** {primary_meter}\n"
        response += f"**Confidence:** {confidence_level} ({confidence_score:.1f}/10)\n"
        if confidence_reason_text:
            response += f"**Why:** {confidence_reason_text}\n"
        response += "\n"

        # L-G Pattern split by pada
        lg_pattern = meter_data['lg_pattern']
        lg_padas = [p for p in meter_data.get('lg_pattern_padas', []) if p]
        if lg_padas:
            formatted_lg = format_lg_padas(lg_padas)
        else:
            formatted_lg = split_lg_pattern_by_pada(lg_pattern)
        response += f"**L-G Pattern (by Pada):**\n{formatted_lg}\n\n"

        response += f"**Gana Pattern:** `{meter_data['gana_pattern']}`\n\n"
        response += f"**Syllables:** {meter_data['syllables']} | **Matra:** {meter_data['matra']}\n"

        if meter_data.get('is_multi_line'):
            response += f" | **Lines:** {meter_data.get('verse_lines', 2)}\n"

        response += "\n"

        if meter_data.get('syllable_breakdown') and len(meter_data['syllable_breakdown']) <= 25:
            response += f"**Syllables:** {' · '.join(meter_data['syllable_breakdown'])}\n\n"

    # Add "Use Analyse Chanda" suggestion if agentic flow was used
    if add_analyze_link:
        # URL encode the text for the link
        import urllib.parse

        encoded_text = urllib.parse.quote(meter_data.get('text', ''))
        analyze_url = f"/app?text={encoded_text}"
        response += f"\n---\n💡 **Tip:** Use the [**Analyse Chanda**]({analyze_url}) page for detailed analysis with visualizations.\n"

    return response
