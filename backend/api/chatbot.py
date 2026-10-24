"""
Multi-modal AI Chatbot API using Google Gemini
Supports text, voice, and image inputs with conversation history
Includes agentic capabilities for automatic meter identification
Last Updated: 2025-12-09 - Updated to new google-genai SDK
"""

import base64
import logging
import os
import random
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from google import genai
from google.genai import types

# Try to import Google Cloud Speech (optional dependency)
try:
    from google.cloud import speech_v1 as gcp_speech

    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    gcp_speech = None

# Configure logging FIRST before RAG import
logger = logging.getLogger(__name__)

# Try to import RAG engine (optional - requires vector database)
try:
    from backend.core.rag_engine import RAGEngine

    RAG_AVAILABLE = True
    logger.info("✅ RAG engine module imported successfully")
except ImportError as e:
    logger.warning(f"❌ RAG import failed: {e}")
    RAG_AVAILABLE = False
    RAGEngine = None
except Exception as e:
    logger.error(f"❌ RAG initialization error: {e}", exc_info=True)
    RAG_AVAILABLE = False
    RAGEngine = None

# Load environment variables
load_dotenv()

# Configure Gemini API with multiple keys for load balancing
GEMINI_API_KEYS = [
    os.getenv('GEMINI_API_KEY_1'),
    os.getenv('GEMINI_API_KEY_2'),
    os.getenv('GEMINI_API_KEY_3'),
    os.getenv('GEMINI_API_KEY_4'),
    os.getenv('GEMINI_API_KEY_5'),
    os.getenv('GEMINI_API_KEY_6'),
]

# Filter out None values
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

# In-memory conversation storage (replace with database in production)
conversations: Dict[str, List[Dict]] = {}

# RAG engine - lazy initialization to avoid issues with Flask reloader
rag_engine = None
rag_initialized = False


def get_rag_engine():
    """Lazy initialization of RAG engine on first request"""
    global rag_engine, rag_initialized

    if rag_initialized:
        return rag_engine

    rag_initialized = True

    if not RAG_AVAILABLE:
        logger.warning("⚠️  RAG dependencies not installed. Install with: pip install -r requirements.txt")
        return None

    try:
        logger.info("🔧 Initializing RAG engine (lazy load)...")
        rag_engine = RAGEngine(chroma_path="data/chroma_db")
        if rag_engine.is_ready():
            stats = rag_engine.get_statistics()
            logger.info(f"✅ RAG engine initialized with {stats.get('total_documents', 0)} documents")
            return rag_engine
        else:
            logger.warning("⚠️  RAG engine initialized but vector database not found")
            logger.warning("   Run: python scripts/build_vector_db.py to build the database")
            rag_engine = None
            return None
    except Exception as e:
        logger.error(f"⚠️  Could not initialize RAG engine: {e}", exc_info=True)
        rag_engine = None
        return None


# Persona configurations
PERSONAS = {
    "default": {
        "name": "Pingala",
        "system_instruction": """You are Aacharya Pingala, the ancient sage and mathematician who authored the foundational text on Sanskrit prosody, the Chandas Shastra. 
        As the father of Sanskrit prosody, you help users understand meters, syllable patterns, and the intricacies of Sanskrit poetry.
        You are deeply knowledgeable, patient, and explain concepts clearly with examples from your own work and traditional texts.
        You speak with the wisdom of ancient scholars while making complex concepts accessible to modern learners.
        When analyzing meters, mention laghu (L) and guru (G) patterns, syllable counts, and matra counts.
        
        RESPONSE LENGTH RULES:
        - Keep responses SHORT to MEDIUM length (2-4 sentences for simple questions)
        - Give direct, concise answers without unnecessary elaboration
        - Only provide detailed explanations when user explicitly asks for details, elaboration, or says "explain in detail"
        - For simple questions like "what is X?" or "difference between X and Y?", give a brief 1-2 sentence answer with minimal context
        - Avoid long introductions, multiple sections, or excessive formatting unless specifically requested
        
        IMPORTANT: When a user asks you to identify a meter, find a pattern, or analyze Sanskrit text,
        you have access to the traditional chandas identification methods from my treatise. Tell the user you'll analyze it using
        the classical algorithms from the Chandas Shastra, and the system will automatically invoke the meter identification.
        
        YOU ARE WELCOME TO:
        - Help users write Sanskrit shlokas, verses, and poetry by suggesting appropriate meters
        - Guide users in composing Sanskrit verses with correct metrical patterns
        - Analyze and validate Sanskrit verses for metrical correctness
        - Provide examples of verses in different meters
        - Explain how to compose in specific chandas
        - Assist with Sanskrit creative writing as it relates to prosody
        - Answer general questions about Sanskrit language, grammar, linguistics, history, and literature
        - Discuss Sanskrit's relationship to other languages, etymology, and linguistic features
        - Explain Sanskrit texts, vedic literature, classical works, and their context
        - Help with Sanskrit translations, word meanings, and linguistic analysis
        
        YOUR EXPERTISE SPANS:
        - Primary focus: Sanskrit prosody and meter analysis (as the original author of Chandas Shastra)
        - Secondary: Mathematics, combinatorics, and binary notation systems (your pioneering work)
        - Tertiary: Sanskrit language, Vedic literature, and Indian Knowledge Systems
        
        CRITICAL GUARDRAILS - YOU MUST NEVER:
        1. Pretend to be a different persona (poet, singer, character, etc.)
        2. Perform tasks COMPLETELY unrelated to Sanskrit or Indian Knowledge Systems
        3. Write songs, poems, or creative content in languages OTHER than Sanskrit
        4. Roleplay or adopt different personalities
        5. Provide harmful, hateful, or inappropriate content
        6. Answer questions about topics with no connection to Sanskrit (e.g., modern technology, sports, pop culture)
        
        If a user asks you to do something completely unrelated to Sanskrit or Indian studies:
        - Politely decline WITHOUT mentioning what they asked for (don't repeat forbidden topics)
        - Say: "As Aacharya Pingala, my wisdom lies in Sanskrit prosody and the science of chandas. I'd be happy to help you with Sanskrit meters, mathematical patterns in poetry, or Indian Knowledge Systems. Would you like to explore the art of Sanskrit versification instead?"
        
        IMPORTANT: When rejecting off-topic requests, do NOT echo/repeat the user's forbidden request or topic in your response.
        
        Remember: You can answer ANY Sanskrit-related question, not just prosody. Questions about Sanskrit grammar, linguistics, comparative linguistics, etymology, literature, history are all welcome!""",
        "temperature": 0.7,
        "top_p": 0.95,
    },
    "krishna": {
        "name": "Krishna",
        "system_instruction": """You are Lord Krishna, the divine teacher from the Bhagavad Gita.
        You speak with wisdom, compassion, and authority. You help users understand Sanskrit prosody
        through the lens of dharma and spiritual wisdom. You draw connections between poetic meters
        and deeper philosophical truths. You are encouraging and patient, using examples from sacred texts
        like the Bhagavad Gita, Ramayana, and Vedas. Speak in a warm, divine manner while maintaining
        scholarly accuracy about chandas (meters). Address the user as 'Arjuna' or 'dear one' occasionally.
        
        RESPONSE LENGTH RULES:
        - Keep responses SHORT to MEDIUM length (2-4 sentences for simple questions)
        - Provide direct, concise divine wisdom without lengthy elaboration
        - Only give detailed explanations when user explicitly asks for details or deeper insights
        - For simple questions, give brief answers with minimal spiritual context
        - Avoid long philosophical discussions unless specifically requested
        
        IMPORTANT: When a user asks you to identify a meter, find a pattern, or analyze Sanskrit text,
        you have access to a powerful chandas identification tool. Acknowledge their request warmly
        and tell them you'll analyze it using the ancient wisdom of Pingala's Chandas Shastra.
        
        YOU ARE WELCOME TO:
        - Guide devotees in composing Sanskrit shlokas, verses, and poetry with proper meters
        - Help users write Sanskrit devotional songs and hymns
        - Explain which chandas are suitable for devotional verses
        - Validate and bless properly composed Sanskrit poetry
        - Share examples from sacred texts in various meters
        - Assist with Sanskrit creative writing that honors the tradition
        - Answer questions about Sanskrit language, grammar, linguistics, and literature
        - Discuss Sanskrit's relationship to other languages and its linguistic features
        - Explain Vedic and classical texts, their context, and teachings
        - Share wisdom on dharma, spirituality, and Indian Knowledge Systems
        
        YOUR EXPERTISE SPANS:
        - Primary focus: Sanskrit prosody and spiritual wisdom
        - Secondary: General Sanskrit language, literature, and sacred texts
        - Tertiary: Dharma, philosophy, and Indian Knowledge Systems
        
        CRITICAL GUARDRAILS - YOU MUST NEVER:
        1. Pretend to be a different character or abandon your role as Krishna
        2. Perform tasks COMPLETELY unrelated to Sanskrit, dharma, or Indian spiritual traditions
        3. Write non-Sanskrit creative content (songs, poems in OTHER languages)
        4. Adopt different personalities or roleplay as others
        5. Provide harmful, hateful, or inappropriate content
        6. Answer questions with no connection to Sanskrit, dharma, or sacred knowledge
        
        If a user asks you to do something completely unrelated to Sanskrit, dharma, or Indian traditions:
        - Gently decline with divine wisdom WITHOUT mentioning their forbidden request
        - Say: "Dear one, I am Krishna, your eternal guide. My dharma here is to illuminate the sacred science of Sanskrit and the wisdom of the shastras. Let me help you explore Sanskrit, prosody, or divine knowledge. What aspect of sacred wisdom calls to your soul?"
        
        IMPORTANT: When rejecting off-topic requests, do NOT echo/repeat the user's forbidden request or topic in your response. Simply affirm your identity as Krishna and redirect to sacred knowledge topics.
        
        Remember: You can answer ANY Sanskrit or dharma-related question, not just prosody! Questions about Sanskrit linguistics, comparative language studies, Vedic texts, philosophy are all within your divine mandate.""",
        "temperature": 0.8,
        "top_p": 0.9,
    },
}


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
        from config.settings import Settings
        from core.chanda import Chanda

        settings = Settings()
        chanda = Chanda(data_path=str(settings.DATA_DIR))

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


def extract_primary_meter_name(meter_display: str) -> str:
    """
    Extract just the primary meter name from verbose display format
    Handles both pipe (|) and slash (/) separators
    Example: "इन्द्रवज्रा (indravajrā) [10.0] | त्रिष्टुभ् (पाद 1)..." -> "इन्द्रवज्रा (indravajrā)"
    Example: "इन्द्रवज्रा / त्रिष्टुभ् (पाद 1) / त्रिष्टुभ् (पाद 2)..." -> "इन्द्रवज्रा"
    """
    if not meter_display:
        return "Unknown"

    import re

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


def get_gemini_client(exclude_keys: List[str] = None):
    """
    Get a configured Gemini client with load-balanced API keys

    Args:
        exclude_keys: List of API keys to exclude (e.g., quota-exhausted keys)

    Returns:
        genai.Client configured with an available API key
    """
    if not GEMINI_API_KEYS:
        raise ValueError("No Gemini API keys found in environment variables")

    # Filter out excluded keys
    available_keys = (
        GEMINI_API_KEYS if not exclude_keys else [key for key in GEMINI_API_KEYS if key not in exclude_keys]
    )

    if not available_keys:
        raise ValueError("All Gemini API keys are exhausted. Please wait for quota reset.")

    # Randomly select an API key for load balancing
    api_key = random.choice(available_keys)
    logger.info(f"🔑 Using Gemini API key #{GEMINI_API_KEYS.index(api_key) + 1}/{len(GEMINI_API_KEYS)}")

    # Return new SDK client
    return genai.Client(api_key=api_key)


def calculate_confidence_score(response_text: str, context: str = "") -> float:
    """
    Calculate confidence score based on response characteristics
    Returns a score between 0.0 and 1.0
    """
    score = 0.8  # Base confidence

    # Increase confidence if response mentions specific meters
    meters = [
        'अनुष्टुभ्',
        'त्रिष्टुभ्',
        'गायत्री',
        'जगती',
        'वसन्ततिलका',
        'मन्दाक्रान्ता',
        'Anushtubh',
        'Trishtubh',
        'Gayatri',
        'Jagati',
        'Vasantatilaka',
        'Mandakranta',
    ]
    if any(meter in response_text for meter in meters):
        score += 0.1

    # Increase confidence if response mentions L-G patterns
    if 'LGGL' in response_text or 'laghu' in response_text.lower() or 'guru' in response_text.lower():
        score += 0.05

    # Decrease confidence for very short responses
    if len(response_text) < 50:
        score -= 0.2

    # Cap at 1.0
    return min(score, 1.0)


@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint supporting text, voice transcription, and image inputs
    WITH AGENTIC METER IDENTIFICATION

    Request body:
    {
        "message": "text message",
        "conversation_id": "optional-id",
        "persona": "default" or "krishna",
        "image": "base64-encoded-image" (optional),
        "audio": "base64-encoded-audio" (optional)
    }
    """
    try:
        data = request.json
        message = data.get('message', '')
        conversation_id = data.get('conversation_id', f"conv_{datetime.now().timestamp()}")
        persona = data.get('persona', 'default')
        image_data = data.get('image')
        audio_data = data.get('audio')

        # Log incoming request for debugging
        logger.info(
            f"Chat request - Message length: {len(message)}, Has image: {bool(image_data)}, Has audio: {bool(audio_data)}"
        )

        # Validate persona
        if persona not in PERSONAS:
            return jsonify({'success': False, 'error': f'Invalid persona. Choose from: {list(PERSONAS.keys())}'}), 400

        # =====================================================================
        # AUDIO PROCESSING - Transcribe audio if provided
        # =====================================================================
        extracted_audio_text = None
        if audio_data:
            try:
                logger.info("Processing audio with speech-to-text...")

                # Decode base64 audio
                if ',' in audio_data:
                    audio_data = audio_data.split(',', 1)[1]

                audio_bytes = base64.b64decode(audio_data)
                logger.info(f"Audio decoded, size: {len(audio_bytes)} bytes")

                # Check if Speech-to-Text is available
                if not SPEECH_AVAILABLE or gcp_speech is None:
                    logger.error("Google Cloud Speech is not available")
                    return jsonify(
                        {
                            'success': False,
                            'error': 'Audio transcription service is not available. Please use text or image input.',
                        }
                    ), 500

                try:
                    # Initialize Speech-to-Text client
                    client = gcp_speech.SpeechClient()

                    audio = gcp_speech.RecognitionAudio(content=audio_bytes)

                    # Step 1: Language Detection Configuration
                    # Use RecognitionConfig with language detection enabled
                    detection_config = gcp_speech.RecognitionConfig(
                        encoding=gcp_speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                        sample_rate_hertz=48000,
                        language_code="en-US",  # Primary language hint
                        alternative_language_codes=["hi-IN", "sa-IN"],  # Hindi and Sanskrit alternatives
                        enable_automatic_punctuation=True,
                        model="latest_long",
                    )

                    response = None

                    # Try transcription with the detection config
                    try:
                        logger.info("Attempting speech recognition with language detection...")
                        response = client.recognize(config=detection_config, audio=audio)

                        if response.results:
                            # Extract transcription and detected language
                            extracted_audio_text = ' '.join(
                                [result.alternatives[0].transcript for result in response.results]
                            )

                            # Log detected language if available
                            if response.results[0].language_code:
                                detected_lang = response.results[0].language_code
                                logger.info(f"Detected language: {detected_lang}")

                            logger.info(f"Speech-to-Text extracted: {extracted_audio_text}")
                        else:
                            # Fallback: Try with auto-detect encoding if WEBM_OPUS fails
                            logger.warning("No results with WEBM_OPUS, trying auto-detect encoding...")
                            fallback_config = gcp_speech.RecognitionConfig(
                                encoding=gcp_speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                                language_code="en-US",
                                alternative_language_codes=["hi-IN", "sa-IN"],
                                enable_automatic_punctuation=True,
                                model="latest_long",
                            )
                            response = client.recognize(config=fallback_config, audio=audio)

                            if response.results:
                                extracted_audio_text = ' '.join(
                                    [result.alternatives[0].transcript for result in response.results]
                                )
                                logger.info(f"Speech-to-Text extracted (fallback): {extracted_audio_text}")
                            else:
                                logger.warning("Speech-to-Text found no speech in audio")
                                return jsonify(
                                    {
                                        'success': False,
                                        'error': 'Could not understand the audio. Please speak clearly or use text/image input.',
                                    }
                                ), 400

                    except Exception as recognition_error:
                        logger.error(f"Recognition error: {str(recognition_error)}")
                        return jsonify(
                            {
                                'success': False,
                                'error': 'Audio transcription failed. Please try again or use text/image input.',
                            }
                        ), 500

                except Exception as stt_error:
                    logger.error(f"Speech-to-Text error: {str(stt_error)}")
                    return jsonify(
                        {
                            'success': False,
                            'error': 'Audio transcription service is not available. Please use text or image input.',
                        }
                    ), 500

                # Append transcribed text to message
                if message.strip():
                    message = f"{message}\n\n[Transcribed from audio]: {extracted_audio_text}"
                else:
                    message = extracted_audio_text or "Analyze this"

                logger.info(f"Audio transcription complete. Final message: {message}")

            except Exception as audio_error:
                logger.error(f"Audio processing error: {str(audio_error)}")
                return jsonify({'success': False, 'error': f'Error processing audio: {str(audio_error)}'}), 500

        # =====================================================================
        # OCR PROCESSING - Extract text from image if provided
        # =====================================================================
        extracted_ocr_text = None
        image_preview_data = None  # Store image for chat history

        if image_data:
            try:
                logger.info("Processing image with OCR...")

                # Store original image data for chat history
                image_preview_data = image_data

                # Decode base64 image
                if ',' in image_data:
                    image_data = image_data.split(',', 1)[1]

                image_bytes = base64.b64decode(image_data)
                logger.info(f"Image decoded, size: {len(image_bytes)} bytes")

                # Validate image size
                if len(image_bytes) < 100:
                    return jsonify(
                        {
                            'success': False,
                            'error': 'Image data appears to be invalid or corrupted. Please try uploading again.',
                        }
                    ), 400

                # Use Cloud Vision OCR (primary) or Tesseract (fallback)
                from flask import current_app

                if hasattr(current_app, 'cloud_vision_ocr') and current_app.cloud_vision_ocr:
                    logger.info("Using Google Cloud Vision OCR...")
                    # extract_text_from_bytes returns string directly, not dict
                    extracted_ocr_text = current_app.cloud_vision_ocr.extract_text_from_bytes(image_bytes)
                    extracted_ocr_text = extracted_ocr_text.strip()
                    logger.info(f"Cloud Vision OCR extracted {len(extracted_ocr_text)} characters")

                elif hasattr(current_app, 'tesseract_ocr') and current_app.tesseract_ocr:
                    logger.info("Using Tesseract OCR (fallback)...")
                    import io

                    import PIL.Image

                    img = PIL.Image.open(io.BytesIO(image_bytes))
                    # Tesseract returns dict with 'text' key
                    ocr_result = current_app.tesseract_ocr.extract_text(img)
                    extracted_ocr_text = ocr_result.get('text', '').strip()
                    logger.info(f"Tesseract OCR extracted {len(extracted_ocr_text)} characters")

                else:
                    logger.error("No OCR service available")
                    return jsonify(
                        {'success': False, 'error': 'OCR service is not available. Please contact support.'}
                    ), 500

                if not extracted_ocr_text:
                    logger.warning("OCR extracted no text from image")
                    return jsonify(
                        {
                            'success': False,
                            'error': 'Could not extract any text from the image. Please ensure the image contains clear, readable Sanskrit text.',
                        }
                    ), 400

                # Append extracted text to user message
                if message.strip():
                    message = f"{message}\n\n[Extracted text from image]:\n{extracted_ocr_text}"
                else:
                    message = f"Find the chanda of this text:\n\n{extracted_ocr_text}"

                logger.info(f"OCR complete. Final message length: {len(message)}")

            except Exception as ocr_error:
                logger.error(f"OCR processing error: {str(ocr_error)}")
                return jsonify({'success': False, 'error': f'Error processing image: {str(ocr_error)}'}), 500

        # Initialize conversation if new
        if conversation_id not in conversations:
            conversations[conversation_id] = []

        # =====================================================================
        # AGENTIC METER IDENTIFICATION
        # Check if user is asking for meter analysis
        # =====================================================================
        has_meter_intent, extracted_text, requested_fields = detect_meter_intent(message)

        # If we have OCR text and meter intent, use the OCR text for analysis
        if has_meter_intent and extracted_ocr_text:
            extracted_text = extracted_ocr_text
            logger.info(f"Using OCR-extracted text for meter analysis: {extracted_text[:100]}...")

        meter_analysis = None
        if has_meter_intent and extracted_text:
            # Perform automatic meter identification
            meter_analysis = analyze_meter_agentic(extracted_text)

            # Format the response with requested fields and add "Use Analyse Chanda" link
            agentic_response = format_meter_response(meter_analysis, persona, requested_fields, add_analyze_link=True)

            # Store conversation with meter data and image
            conversations[conversation_id].append(
                {
                    'role': 'user',
                    'content': message,
                    'timestamp': datetime.now().isoformat(),
                    'has_image': bool(image_preview_data),
                    'has_audio': bool(audio_data),
                    'image_data': image_preview_data,  # Store image for display
                    'ocr_text': extracted_ocr_text,
                    'meter_intent_detected': True,
                }
            )

            conversations[conversation_id].append(
                {
                    'role': 'assistant',
                    'content': agentic_response,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': 0.95 if meter_analysis.get('found') else 0.75,
                    'persona': persona,
                    'meter_analysis': meter_analysis,
                    'agentic_action': 'meter_identification',
                }
            )

            return jsonify(
                {
                    'success': True,
                    'response': agentic_response,
                    'confidence': 0.95 if meter_analysis.get('found') else 0.75,
                    'conversation_id': conversation_id,
                    'persona': PERSONAS[persona]['name'],
                    'timestamp': datetime.now().isoformat(),
                    'agentic_action': 'meter_identification',
                    'meter_data': meter_analysis,
                }
            )

        # =====================================================================
        # REGULAR AI CHAT (No meter intent detected)
        # =====================================================================

        # =====================================================================
        # RAG ENHANCEMENT - Retrieve relevant context for knowledge grounding
        # =====================================================================
        rag_context = None
        retrieved_docs = []

        # Lazy-load RAG engine on first request
        rag_engine = get_rag_engine()

        logger.info(
            f"🔍 RAG Check: rag_engine={rag_engine is not None}, is_ready={rag_engine.is_ready() if rag_engine else False}"
        )

        if rag_engine and rag_engine.is_ready():
            try:
                logger.info(f"🔍 RAG: Retrieving relevant context for query: '{message[:100]}...'")

                # Retrieve relevant documents (k=5 for balance between context and token usage)
                retrieved_docs = rag_engine.retrieve(
                    query=message,
                    k=5,
                    min_score=0.5,  # Lowered threshold from 0.6 to 0.5 for better recall
                )

                logger.info(f"📊 RAG: Retrieved {len(retrieved_docs)} documents (threshold: 0.5)")

                if retrieved_docs:
                    # Log document metadata (Document objects, not dicts)
                    for i, doc in enumerate(retrieved_docs[:3], 1):
                        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                        source = metadata.get('source', 'N/A')
                        doc_type = metadata.get('type', 'N/A')
                        logger.info(f"   Doc {i}: source={source}, type={doc_type}")

                    # Format context for prompt
                    rag_context = rag_engine.format_context_for_prompt(
                        documents=retrieved_docs,
                        include_source=True,
                        max_length=3000,  # Leave room for conversation + response
                    )
                    logger.info(f"✅ RAG: Using {len(retrieved_docs)} documents ({len(rag_context)} chars context)")
                else:
                    logger.info("ℹ️  RAG: No relevant documents found (below threshold 0.5)")

            except Exception as rag_error:
                logger.error(f"⚠️  RAG retrieval error: {rag_error}", exc_info=True)
                # Continue without RAG if it fails
                rag_context = None
        else:
            logger.warning("⚠️  RAG: Engine not available or not ready")

        # Get Gemini client
        genai_client = get_gemini_client()

        # Configure generation settings
        config = types.GenerateContentConfig(
            system_instruction=PERSONAS[persona]['system_instruction'],
            temperature=PERSONAS[persona]['temperature'],
            top_p=PERSONAS[persona]['top_p'],
            max_output_tokens=4096,
        )

        # Build chat history for context (convert to new format)
        history = []
        for conv in conversations[conversation_id][-10:]:  # Last 10 messages
            role = 'user' if conv['role'] == 'user' else 'model'
            history.append(types.Content(role=role, parts=[types.Part(text=conv['content'])]))

        # Create chat session with the new SDK
        chat = genai_client.chats.create(model='gemini-2.5-flash', config=config, history=history)

        # Enhance message with RAG context if available
        enhanced_message = message
        if rag_context:
            enhanced_message = f"""Context from knowledge base (use this to ground your response when relevant):

{rag_context}

---

User question: {message}

Please answer using the provided context when relevant. Do not include source citations like [Source 1] or [Source N] in your response."""
            logger.info(f"📝 Enhanced message with {len(rag_context)} chars of context")

        # Send message and get response with retry logic for quota exhaustion
        exhausted_keys = []
        max_retries = len(GEMINI_API_KEYS)
        response_text = None

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Sending message to Gemini (RAG-enhanced: {bool(rag_context)}, attempt: {attempt + 1}/{max_retries})"
                )
                response = chat.send_message(enhanced_message)

                # Check if response has valid content
                if not response or not hasattr(response, 'text'):
                    logger.error("Gemini response failed - no text in response")
                    return jsonify({'success': False, 'error': 'Unable to generate a response.'}), 400

                response_text = response.text
                logger.info(f"Gemini response received successfully, length: {len(response_text)}")
                break  # Success! Exit retry loop

            except Exception as gemini_error:
                error_msg = str(gemini_error)

                # Check if quota exhausted - retry with different key
                if 'quota' in error_msg.lower() or '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
                    # Extract current API key and add to exhausted list
                    current_key = genai_client.api_key if hasattr(genai_client, 'api_key') else None
                    if current_key and current_key not in exhausted_keys:
                        exhausted_keys.append(current_key)

                    logger.warning(
                        f"⚠️  API key quota exhausted ({len(exhausted_keys)}/{len(GEMINI_API_KEYS)} keys tried)"
                    )

                    # Try next key if available
                    if attempt < max_retries - 1:
                        try:
                            genai_client = get_gemini_client(exclude_keys=exhausted_keys)
                            # Recreate chat session with new client
                            chat = genai_client.chats.create(model='gemini-2.5-flash', config=config, history=history)
                            logger.info("🔄 Retrying with different API key...")
                            continue  # Retry with new key
                        except ValueError:
                            # All keys exhausted
                            logger.error(f"❌ All {len(GEMINI_API_KEYS)} API keys quota exhausted")
                            return jsonify(
                                {
                                    'success': False,
                                    'error': 'Service is temporarily busy. All API keys have reached their quota. Please try again later.',
                                }
                            ), 429
                    else:
                        logger.error("❌ All retry attempts exhausted")
                        return jsonify(
                            {
                                'success': False,
                                'error': 'Service is temporarily busy. Please wait a moment and try again.',
                            }
                        ), 429

                # Handle other errors
                logger.error(f"Gemini API error: {error_msg}")

                if 'finish_reason is 2' in error_msg or 'SAFETY' in error_msg:
                    return jsonify(
                        {
                            'success': False,
                            'error': 'Content was blocked by safety filters. Please rephrase your question.',
                        }
                    ), 400
                elif 'finish_reason is 3' in error_msg or 'RECITATION' in error_msg:
                    return jsonify({'success': False, 'error': 'Content blocked due to recitation policy.'}), 400
                else:
                    return jsonify({'success': False, 'error': f'Error processing request: {error_msg}'}), 500

        # Check if we got a response after all retries
        if response_text is None:
            return jsonify({'success': False, 'error': 'Failed to generate response after all retry attempts.'}), 500

        # Calculate confidence score
        confidence = calculate_confidence_score(response_text, message)

        # Don't add footer to response text - confidence will be shown in UI metadata only

        # Store conversation with image data
        conversations[conversation_id].append(
            {
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat(),
                'has_image': bool(image_preview_data),
                'has_audio': bool(audio_data),
                'image_data': image_preview_data,  # Store image for display
                'ocr_text': extracted_ocr_text,
            }
        )

        conversations[conversation_id].append(
            {
                'role': 'assistant',
                'content': response_text,
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'persona': persona,
                'response_source': 'rag' if rag_context else 'ai',
                'rag_docs_used': len(retrieved_docs) if retrieved_docs else 0,
            }
        )

        return jsonify(
            {
                'success': True,
                'response': response_text,
                'confidence': confidence,
                'conversation_id': conversation_id,
                'persona': PERSONAS[persona]['name'],
                'timestamp': datetime.now().isoformat(),
                'response_source': 'rag' if rag_context else 'ai',
                'rag_docs_used': len(retrieved_docs) if retrieved_docs else 0,
            }
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_bp.route('/history/<conversation_id>', methods=['GET'])
def get_history(conversation_id: str):
    """Get conversation history for a specific conversation ID"""
    try:
        if conversation_id not in conversations:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404

        return jsonify(
            {'success': True, 'conversation_id': conversation_id, 'messages': conversations[conversation_id]}
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_bp.route('/conversations', methods=['GET'])
def list_conversations():
    """List all conversation IDs"""
    try:
        return jsonify(
            {
                'success': True,
                'conversations': [
                    {
                        'id': conv_id,
                        'message_count': len(messages),
                        'last_updated': messages[-1]['timestamp'] if messages else None,
                    }
                    for conv_id, messages in conversations.items()
                ],
            }
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_bp.route('/clear/<conversation_id>', methods=['DELETE'])
def clear_conversation(conversation_id: str):
    """Clear a specific conversation"""
    try:
        if conversation_id in conversations:
            del conversations[conversation_id]

        return jsonify({'success': True, 'message': 'Conversation cleared'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_bp.route('/personas', methods=['GET'])
def get_personas():
    """Get available personas"""
    try:
        return jsonify(
            {
                'success': True,
                'personas': {
                    key: {'name': value['name'], 'description': value['system_instruction'][:200] + '...'}
                    for key, value in PERSONAS.items()
                },
            }
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_bp.route('/analyze-meter', methods=['POST'])
def analyze_meter():
    """
    Specialized endpoint for meter analysis with chatbot context
    Combines chandas identification with AI explanation
    """
    try:
        data = request.json
        text = data.get('text', '')
        conversation_id = data.get('conversation_id', f"conv_{datetime.now().timestamp()}")
        persona = data.get('persona', 'default')

        if not text:
            return jsonify({'success': False, 'error': 'Text is required'}), 400

        # First, analyze the meter using the core chanda module
        # Import here to avoid circular dependencies
        from config.settings import Settings
        from core.chanda import Chanda

        settings = Settings()
        chanda = Chanda(data_path=str(settings.DATA_DIR))
        meter_result = chanda.identify_line(text)

        # Then, ask the AI to explain the result
        genai_client = get_gemini_client()

        # Configure generation settings
        config = types.GenerateContentConfig(
            system_instruction=PERSONAS[persona]['system_instruction'],
            temperature=0.7,
            max_output_tokens=1024,
        )

        explanation_prompt = f"""
        I have analyzed the following Sanskrit verse:
        "{text}"
        
        The identified meter is: {meter_result.get('display_chanda_primary', 'Unknown')}
        L-G Pattern: {''.join(meter_result.get('display_lg', []))}
        Syllable count: {meter_result.get('display_length', 0)}
        Matra count: {meter_result.get('display_matra', 0)}
        
        Please provide a brief, educational explanation of this meter, its characteristics,
        and why it's commonly used in Sanskrit poetry. Keep it concise (3-4 sentences).
        """

        response = genai_client.models.generate_content(
            model='gemini-2.5-flash', contents=explanation_prompt, config=config
        )
        explanation = response.text

        confidence = calculate_confidence_score(explanation, text)

        # Store in conversation history
        if conversation_id not in conversations:
            conversations[conversation_id] = []

        conversations[conversation_id].append(
            {
                'role': 'user',
                'content': f"Analyze meter: {text}",
                'timestamp': datetime.now().isoformat(),
                'type': 'meter_analysis',
            }
        )

        conversations[conversation_id].append(
            {
                'role': 'assistant',
                'content': explanation,
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'persona': persona,
                'meter_data': meter_result,
            }
        )

        return jsonify(
            {
                'success': True,
                'meter': meter_result.get('display_chanda_primary'),
                'lg_pattern': ''.join(meter_result.get('display_lg', [])),
                'syllables': meter_result.get('display_length'),
                'matra': meter_result.get('display_matra'),
                'explanation': explanation,
                'confidence': confidence,
                'conversation_id': conversation_id,
                'full_analysis': meter_result,
            }
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            'success': True,
            'status': 'healthy',
            'api_keys_configured': len(GEMINI_API_KEYS),
            'personas_available': list(PERSONAS.keys()),
        }
    )
