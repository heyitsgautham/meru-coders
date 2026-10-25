"""Detecting meter questions in chat messages and running the meter engine on them."""

import re
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# AGENTIC METER IDENTIFICATION FUNCTIONS
# ============================================================================


def extract_sanskrit_text(message: str) -> Optional[str]:
    """
    Extract Sanskrit text from user message for meter analysis
    Looks for Devanagari script or quoted text
    """
    # Pattern 1: Text in quotes (highest priority - user explicitly marked it)
    quoted_patterns = [
        r'"([^"]+)"',  # Double quotes
        r"'([^']+)'",  # Single quotes
        r'`([^`]+)`',  # Backticks
    ]
    for pattern in quoted_patterns:
        matches = re.findall(pattern, message)
        if matches:
            return matches[0].strip()

    # Pattern 2: Continuous Devanagari text (including spaces, punctuation)
    # Match the entire span of Devanagari characters, spaces, and common punctuation
    devanagari_span_pattern = r'[\u0900-\u097F\s।॥\u0964\u0965]+'
    devanagari_matches = re.findall(devanagari_span_pattern, message)

    if devanagari_matches:
        # Find the longest continuous span and clean it up
        longest_match = max(devanagari_matches, key=len).strip()

        # Remove trailing/leading punctuation marks
        longest_match = re.sub(r'^[।॥\s]+|[।॥\s]+$', '', longest_match)

        # If it's still substantial (more than just a word), return it
        if len(longest_match) > 5:  # At least a few characters
            return longest_match

    # Pattern 3: Multiple Devanagari words separated by spaces
    # Fallback: collect all Devanagari words and join them
    word_pattern = r'[\u0900-\u097F]+'
    words = re.findall(word_pattern, message)
    if words and len(words) > 1:  # Multiple words found
        return ' '.join(words)
    elif words:  # Single word
        return words[0]

    return None


def detect_meter_intent(message: str) -> Tuple[bool, Optional[str], Dict[str, bool]]:
    """
    Detect if user is asking for meter identification
    Also detect what specific information user is asking for
    Returns (has_intent, extracted_text, requested_fields)
    """
    # Keywords indicating meter analysis intent
    intent_keywords = [
        'identify',
        'find',
        'detect',
        'analyze',
        'analyse',
        'what is the meter',
        'which meter',
        'chandas',
        'chanda',
        'meter',
        'metre',
        'pattern',
        'laghu',
        'guru',
        'gana',
        'syllable',
        'मात्रा',
        'छन्द',
        'वृत्त',
        'l-g pattern',
        'lg pattern',
        'scan',
        'scansion',
    ]

    message_lower = message.lower()
    has_intent = any(keyword in message_lower for keyword in intent_keywords)

    # Detect what specific fields user is asking for
    requested_fields = {
        'meter_name': False,
        'lg_pattern': False,
        'gana_pattern': False,
        'syllable_count': False,
        'matra_count': False,
        'full_analysis': False,  # Default to full analysis if not specified
    }

    if has_intent:
        # Check for specific field requests
        if any(
            term in message_lower
            for term in [
                'chanda name',
                'meter name',
                'name of',
                'which chanda',
                'what chanda',
                'chanda only',
                'meter only',
            ]
        ):
            requested_fields['meter_name'] = True

        if any(term in message_lower for term in ['l-g', 'lg', 'laghu', 'guru', 'pattern']):
            requested_fields['lg_pattern'] = True

        if any(term in message_lower for term in ['gana', 'gaṇa']):
            requested_fields['gana_pattern'] = True

        if any(term in message_lower for term in ['syllable', 'akshara', 'अक्षर']):
            requested_fields['syllable_count'] = True

        if any(term in message_lower for term in ['matra', 'mātrā', 'मात्रा']):
            requested_fields['matra_count'] = True

        # If no specific fields requested, show full analysis
        if not any(requested_fields.values()):
            requested_fields['full_analysis'] = True

        extracted_text = extract_sanskrit_text(message)
        return True, extracted_text, requested_fields

    return False, None, requested_fields


def analyze_meter_agentic(text: str) -> Dict[str, Any]:
    """
    Perform meter analysis using the Chanda algorithm
    Handles both single-line and multi-line verses automatically
    Returns comprehensive meter information

    Pada Detection Strategy (in order of precedence):
    1. Split by newlines if multi-line input
    2. Split by danda separators (।) if single line with dandas
    3. Smart pada detection based on syllable count for common meters:
       - Anuṣṭubh: 8 syllables/pada
       - Śālinī: 11 syllables/pada
       - Vasantatilaka: 14 syllables/pada
       - Mandākrāntā: 17 syllables/pada
       - Śārdūlavikrīḍita: 19 syllables/pada

    This ensures the chatbot output matches the home page analysis format
    with clear pada-by-pada L-G pattern display.
    """
    try:
        from backend.core.engine import get_engine

        chanda = get_engine()

        # Check if text has multiple lines (split by newlines OR danda separators)
        # Sanskrit verses often use । (single danda) to separate padas/lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # If only one line, check for danda separators (।) first
        if len(lines) == 1 and '।' in text:
            # Split by danda and clean up
            lines = [line.strip() for line in text.replace('॥', '।').split('।') if line.strip()]

        # If still one line, try smart pada detection based on syllable count
        if len(lines) == 1:
            # Analyze the whole line first to get syllable count
            test_result = chanda.identify_line(text)
            lg_pattern = ''.join([char for char in test_result.get('display_lg', []) if char])
            total_syllables = len(lg_pattern)

            # Common pada structures in Sanskrit poetry
            # Śālinī: 11 syllables per pada
            # Anuṣṭubh: 8 syllables per pada (32 total for 4 padas)
            # Vasantatilaka: 14 syllables per pada
            # Mandākrāntā: 17 syllables per pada
            # Śārdūlavikrīḍita: 19 syllables per pada

            common_pada_lengths = [8, 11, 12, 14, 17, 19, 21]

            # Try to split into padas based on common structures
            for pada_length in common_pada_lengths:
                if total_syllables % pada_length == 0:
                    num_padas = total_syllables // pada_length
                    # Split the text into padas based on syllable positions
                    lines = []

                    # Get syllable breakdown and L-G marks
                    syllables = test_result.get('display_syllables', [])
                    lg_marks = test_result.get('display_lg', [])

                    # Filter to only include items with valid L-G marks (actual syllables)
                    valid_syllables = []
                    for syl, lg in zip(syllables, lg_marks, strict=False):
                        if lg and lg.strip():  # Only include if has L-G mark
                            valid_syllables.append(syl)

                    if len(valid_syllables) == total_syllables:
                        # Split based on syllable positions
                        for pada_idx in range(num_padas):
                            start = pada_idx * pada_length
                            end = start + pada_length
                            pada_syllables = valid_syllables[start:end]
                            lines.append(''.join(pada_syllables))

                    if len(lines) == num_padas:
                        break  # Successfully split

        if len(lines) > 1:
            # Multi-line verse - reconstruct as newline-separated text
            text_for_analysis = '\n'.join(lines)

            # Multi-line verse - use identify_from_text with verse=True
            response = chanda.identify_from_text(text_for_analysis, verse=True, mode='auto')

            # Extract data from verse result
            # identify_from_text returns: {'result': {'line': [...], 'verse': [...]}, 'path': {...}}
            result = response.get('result', {})

            # Check for validation errors in first line
            if 'line' in result and len(result['line']) > 0:
                first_line_result = result['line'][0].get('result', {})

                # Check if input validation failed
                if not first_line_result.get('is_valid_input', True):
                    validation_error = first_line_result.get('validation_error', 'Invalid Sanskrit input')
                    prose_message = first_line_result.get('prose_message', validation_error)

                    return {
                        'success': False,
                        'is_valid_input': False,
                        'validation_error': validation_error,
                        'prose_message': prose_message,
                        'text': text,
                    }

            if 'verse' in result and len(result['verse']) > 0:
                # Get first verse analysis
                verse_data = result['verse'][0]

                # Collect all line results
                all_lg = []
                lg_by_line: List[str] = []
                all_syllables = []
                total_syllables = 0
                total_matra = 0

                if 'line' in result:
                    for line_result in result['line']:
                        line_data = line_result.get('result', {})
                        if line_data.get('display_lg'):
                            line_lg_list = [char for char in line_data['display_lg'] if char]
                            if line_lg_list:
                                all_lg.extend(line_lg_list)
                                lg_by_line.append(''.join(line_lg_list))
                        if line_data.get('display_syllables'):
                            all_syllables.extend(line_data['display_syllables'])
                        # Convert to int to handle both int and str types
                        # Some meters return formulas like "2 / (1 + 1) / (1 + 1)" - evaluate or extract first number
                        length = line_data.get('display_length', 0)
                        matra = line_data.get('display_matra', 0)

                        try:
                            if isinstance(length, str):
                                # Try to extract first number from formula or convert directly
                                if '/' in length or '+' in length:
                                    # Extract first number from formula
                                    import re

                                    match = re.search(r'\d+', length)
                                    total_syllables += int(match.group()) if match else 0
                                else:
                                    total_syllables += int(length)
                            else:
                                total_syllables += int(length) if length else 0
                        except (ValueError, AttributeError):
                            pass  # Skip invalid values

                        try:
                            if isinstance(matra, str):
                                # Try to extract first number from formula or convert directly
                                if '/' in matra or '+' in matra:
                                    # Extract first number from formula
                                    import re

                                    match = re.search(r'\d+', matra)
                                    total_matra += int(match.group()) if match else 0
                                else:
                                    total_matra += int(matra)
                            else:
                                total_matra += int(matra) if matra else 0
                        except (ValueError, AttributeError):
                            pass  # Skip invalid values

                # Get meter from verse or first line
                meter_name = 'Unknown'
                meter_display = 'Unknown'
                found = False

                if 'result' in verse_data:
                    verse_result = verse_data['result']
                    meter_name = verse_result.get('display_chanda_primary', 'Unknown')
                    meter_display = verse_result.get('display_chanda', 'Unknown')
                    found = verse_result.get('found', False)
                elif 'line' in result and len(result['line']) > 0:
                    first_line = result['line'][0].get('result', {})
                    meter_name = first_line.get('display_chanda_primary', 'Unknown')
                    meter_display = first_line.get('display_chanda', 'Unknown')
                    found = first_line.get('found', False)

                # Get confidence reason from first line result
                confidence_reason = None
                if 'line' in result and len(result['line']) > 0:
                    first_line_result = result['line'][0].get('result', {})
                    confidence_reason = first_line_result.get('primary_confidence_reason')

                return {
                    'success': True,
                    'text': text_for_analysis,  # Use the properly formatted text
                    'meter': meter_name,
                    'meter_display': meter_display,
                    'lg_pattern': ''.join(all_lg),
                    'lg_pattern_padas': lg_by_line,
                    'gana_pattern': result['line'][0].get('result', {}).get('display_gana', '')
                    if 'line' in result and len(result['line']) > 0
                    else '',
                    'syllables': total_syllables,
                    'matra': total_matra,
                    'syllable_breakdown': all_syllables,
                    'found': found,
                    'fuzzy_matches': result['line'][0].get('result', {}).get('fuzzy', [])[:3]
                    if 'line' in result and len(result['line']) > 0
                    else [],
                    'verse_lines': len(lines),
                    'is_multi_line': True,
                    'confidence_reason': confidence_reason,
                }
            else:
                return {'success': False, 'error': 'Could not analyze verse'}
        else:
            # Single line - use identify_line
            result = chanda.identify_line(text)

            # Check if input validation failed
            if not result.get('is_valid_input', True):
                validation_error = result.get('validation_error', 'Invalid Sanskrit input')
                prose_message = result.get('prose_message', validation_error)

                return {
                    'success': False,
                    'is_valid_input': False,
                    'validation_error': validation_error,
                    'prose_message': prose_message,
                    'text': text,
                }

            # Get the full L-G pattern
            lg_pattern = ''.join([char for char in result.get('display_lg', []) if char])

            # Split into padas for better visualization
            lg_padas = []
            total_syllables = len(lg_pattern)
            if total_syllables > 0:
                # Determine pada structure based on syllable count
                if total_syllables % 4 == 0:
                    # 4 padas (quarters) - most common
                    pada_length = total_syllables // 4
                    for i in range(4):
                        start = i * pada_length
                        end = start + pada_length
                        lg_padas.append(lg_pattern[start:end])
                elif total_syllables % 2 == 0:
                    # 2 padas (halves)
                    pada_length = total_syllables // 2
                    lg_padas.append(lg_pattern[:pada_length])
                    lg_padas.append(lg_pattern[pada_length:])
                else:
                    # No clear pada structure, keep as single unit
                    lg_padas.append(lg_pattern)

            return {
                'success': True,
                'text': text,
                'meter': result.get('display_chanda_primary', 'Unknown'),
                'meter_display': result.get('display_chanda', 'Unknown'),
                'lg_pattern': lg_pattern,
                'lg_pattern_padas': lg_padas,
                'gana_pattern': result.get('display_gana', ''),
                'syllables': result.get('display_length', 0),
                'matra': result.get('display_matra', 0),
                'syllable_breakdown': result.get('display_syllables', []),
                'found': result.get('found', False),
                'fuzzy_matches': result.get('fuzzy', [])[:3] if result.get('fuzzy') else [],
                'verse_lines': 1,
                'is_multi_line': False,
                'confidence_reason': result.get('primary_confidence_reason'),
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}
