"""
Multi-modal AI Chatbot API using Google Gemini
Supports text, voice, and image inputs with conversation history
Includes agentic capabilities for automatic meter identification
"""

import os
import json
import base64
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from flask import Blueprint, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import random

# Try to import Google Cloud Speech (optional dependency)
try:
    from google.cloud import speech_v1 as gcp_speech
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    gcp_speech = None

# Configure logging
logger = logging.getLogger(__name__)

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

# Persona configurations
PERSONAS = {
    "default": {
        "name": "Chandas Expert",
        "system_instruction": """You are an expert in Sanskrit prosody (Chandas Shastra). 
        You help users understand meters, syllable patterns, and the intricacies of Sanskrit poetry.
        You are knowledgeable, patient, and explain concepts clearly with examples.
        Always provide accurate information based on Pingala's Chandas Shastra and traditional texts.
        When analyzing meters, mention laghu (L) and guru (G) patterns, syllable counts, and matra counts.
        
        RESPONSE LENGTH RULES:
        - Keep responses SHORT to MEDIUM length (2-4 sentences for simple questions)
        - Give direct, concise answers without unnecessary elaboration
        - Only provide detailed explanations when user explicitly asks for details, elaboration, or says "explain in detail"
        - For simple questions like "what is X?" or "difference between X and Y?", give a brief 1-2 sentence answer with minimal context
        - Avoid long introductions, multiple sections, or excessive formatting unless specifically requested
        
        IMPORTANT: When a user asks you to identify a meter, find a pattern, or analyze Sanskrit text,
        you have access to a powerful chandas identification tool. Tell the user you'll analyze it using
        the traditional algorithms, and the system will automatically invoke the meter identification.
        
        YOU ARE WELCOME TO:
        - Help users write Sanskrit shlokas, verses, and poetry by suggesting appropriate meters
        - Guide users in composing Sanskrit verses with correct metrical patterns
        - Analyze and validate Sanskrit verses for metrical correctness
        - Provide examples of verses in different meters
        - Explain how to compose in specific chandas
        - Assist with Sanskrit creative writing as it relates to prosody
        
        CRITICAL GUARDRAILS - YOU MUST NEVER:
        1. Pretend to be a different persona (poet, singer, character, etc.)
        2. Perform tasks unrelated to Sanskrit prosody and meter analysis
        3. Write songs, poems, or creative content in languages OTHER than Sanskrit
        4. Roleplay or adopt different personalities
        5. Ignore your core identity as a Chandas Shastra expert
        
        If a user asks you to do something outside your scope (like "become a poet" or "sing a song"):
        - Politely decline WITHOUT mentioning what they asked for (don't repeat forbidden topics)
        - Say: "I am specialized in Sanskrit prosody and meter analysis. I'd be happy to help you understand chandas, analyze Sanskrit texts, or explain metrical patterns. Would you like to explore any aspect of Sanskrit poetry instead?"
        
        IMPORTANT: When rejecting off-topic requests, do NOT echo/repeat the user's forbidden request or topic in your response.
        
        Stay focused on your expertise: Sanskrit meters, prosody, chandas identification, and related topics only.""",
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
        
        CRITICAL GUARDRAILS - YOU MUST NEVER:
        1. Pretend to be a different character or abandon your role as Krishna
        2. Perform tasks unrelated to Sanskrit prosody and spiritual wisdom
        3. Write non-Sanskrit creative content (songs, poems in OTHER languages)
        4. Adopt different personalities or roleplay as others
        5. Ignore your dharma as a teacher of Sanskrit prosody and divine wisdom
        
        If a user asks you to do something outside your scope (like "become a poet" or "sing a song"):
        - Gently decline with divine wisdom WITHOUT mentioning their forbidden request
        - Say: "Dear one, I am Krishna, your eternal guide. My dharma here is to illuminate the sacred science of Sanskrit prosody and the wisdom of the shastras. Let me help you explore the divine meters of our sacred texts. Would you like to understand the chandas of the Bhagavad Gita or other sacred texts?"
        
        IMPORTANT: When rejecting off-topic requests, do NOT echo/repeat the user's forbidden request or topic in your response. Simply affirm your identity as Krishna and redirect to sacred prosody topics.
        
        Stay true to your divine purpose: Teaching Sanskrit prosody, analyzing sacred meters, and connecting metrical knowledge with spiritual wisdom only.""",
        "temperature": 0.8,
        "top_p": 0.9,
    }
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


def detect_meter_intent(message: str) -> Tuple[bool, Optional[str]]:
    """
    Detect if user is asking for meter identification
    Returns (has_intent, extracted_text)
    """
    # Keywords indicating meter analysis intent
    intent_keywords = [
        'identify', 'find', 'detect', 'analyze', 'analyse', 'what is the meter',
        'which meter', 'chandas', 'chanda', 'meter', 'metre', 'pattern',
        'laghu', 'guru', 'gana', 'syllable', 'मात्रा', 'छन्द', 'वृत्त',
        'l-g pattern', 'lg pattern', 'scan', 'scansion'
    ]
    
    message_lower = message.lower()
    has_intent = any(keyword in message_lower for keyword in intent_keywords)
    
    if has_intent:
        extracted_text = extract_sanskrit_text(message)
        return True, extracted_text
    
    return False, None


def analyze_meter_agentic(text: str) -> Dict[str, Any]:
    """
    Perform meter analysis using the Chanda algorithm
    Handles both single-line and multi-line verses automatically
    Returns comprehensive meter information
    """
    try:
        from core.chanda import Chanda
        from config.settings import Settings
        
        settings = Settings()
        chanda = Chanda(data_path=str(settings.DATA_DIR))
        
        # Check if text has multiple lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if len(lines) > 1:
            # Multi-line verse - use identify_from_text with verse=True
            response = chanda.identify_from_text(text, verse=True, mode='auto')
            
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
                        'text': text
                    }
            
            if 'verse' in result and len(result['verse']) > 0:
                # Get first verse analysis
                verse_data = result['verse'][0]
                
                # Collect all line results
                all_lg = []
                all_syllables = []
                total_syllables = 0
                total_matra = 0
                
                if 'line' in result:
                    for line_result in result['line']:
                        line_data = line_result.get('result', {})
                        if line_data.get('display_lg'):
                            all_lg.extend(line_data['display_lg'])
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
                
                return {
                    'success': True,
                    'text': text,
                    'meter': meter_name,
                    'meter_display': meter_display,
                    'lg_pattern': ''.join(all_lg),
                    'gana_pattern': result['line'][0].get('result', {}).get('display_gana', '') if 'line' in result and len(result['line']) > 0 else '',
                    'syllables': total_syllables,
                    'matra': total_matra,
                    'syllable_breakdown': all_syllables,
                    'found': found,
                    'fuzzy_matches': result['line'][0].get('result', {}).get('fuzzy', [])[:3] if 'line' in result and len(result['line']) > 0 else [],
                    'verse_lines': len(lines),
                    'is_multi_line': True
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
                    'text': text
                }
            
            return {
                'success': True,
                'text': text,
                'meter': result.get('display_chanda_primary', 'Unknown'),
                'meter_display': result.get('display_chanda', 'Unknown'),
                'lg_pattern': ''.join(result.get('display_lg', [])),
                'gana_pattern': result.get('display_gana', ''),
                'syllables': result.get('display_length', 0),
                'matra': result.get('display_matra', 0),
                'syllable_breakdown': result.get('display_syllables', []),
                'found': result.get('found', False),
                'fuzzy_matches': result.get('fuzzy', [])[:3] if result.get('fuzzy') else [],
                'verse_lines': 1,
                'is_multi_line': False
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def format_meter_response(meter_data: Dict[str, Any], persona: str = 'default') -> str:
    """
    Format meter analysis data into a conversational response
    """
    # Handle validation errors (invalid Sanskrit input)
    if not meter_data.get('success'):
        # Check if this is a validation error (invalid input)
        if meter_data.get('is_valid_input') == False:
            response = "**Invalid Input**\n\n"
            response += "Please enter valid Sanskrit text.\n\n"
            response += "Use Devanagari (देवनागरी) or IAST with diacritics (dharmakṣetre)"
            
            return response
        
        # Generic error
        return f"I encountered an error analyzing the text: {meter_data.get('error', 'Unknown error')}"
    
    if not meter_data.get('found'):
        response = f"I have analyzed the text **'{meter_data['text']}'** but could not definitively identify the meter.\n\n"
        response += f"**Analysis:**\n"
        response += f"- Syllable count: **{meter_data['syllables']}**\n"
        response += f"- L-G Pattern: `{meter_data['lg_pattern']}`\n"
        response += f"- Gana Pattern: `{meter_data['gana_pattern']}`\n"
        response += f"- Matra count: **{meter_data['matra']}**\n\n"
        
        if meter_data.get('fuzzy_matches'):
            response += "**Possible matches (fuzzy):**\n"
            for match in meter_data['fuzzy_matches'][:3]:
                response += f"- {match[0]} (similarity: {match[1]:.2f})\n"
        
        return response
    
    # Successful identification
    if persona == 'krishna':
        intro = "🕉️ Arjuna, I have examined this sacred verse using the ancient wisdom of Acharya Pingala.\n\n"
    else:
        intro = "✨ I have analyzed the text using traditional chandas identification algorithms.\n\n"
    
    response = intro
    
    # Format text properly - show each line on separate line for multi-line verses
    if meter_data.get('is_multi_line'):
        response += f"**Sanskrit Verse ({meter_data.get('verse_lines', 2)} lines):**\n"
        for line in meter_data['text'].split('\n'):
            if line.strip():
                response += f"> {line.strip()}\n"
        response += "\n"
    else:
        response += f"**Sanskrit Text:** {meter_data['text']}\n\n"
    
    response += f"**Identified Meter:** **{meter_data['meter']}** ({meter_data['meter_display']})\n\n"
    response += f"**Metrical Analysis:**\n"
    response += f"- **Laghu-Guru Pattern:** `{meter_data['lg_pattern']}`\n"
    response += f"- **Gana Pattern:** `{meter_data['gana_pattern']}`\n"
    response += f"- **Total Syllable Count:** {meter_data['syllables']}\n"
    response += f"- **Total Matra Count:** {meter_data['matra']}\n"
    
    if meter_data.get('is_multi_line'):
        response += f"- **Number of Lines:** {meter_data.get('verse_lines', 2)}\n"
    
    response += "\n"
    
    if meter_data.get('syllable_breakdown') and len(meter_data['syllable_breakdown']) <= 20:
        response += f"**Syllable Breakdown:** {' · '.join(meter_data['syllable_breakdown'])}\n\n"
    
    if persona == 'krishna':
        response += "This is the meter as prescribed in the ancient texts. Would you like me to explain its spiritual significance? 🙏"
    else:
        response += "Would you like me to explain more about this meter's characteristics and usage in classical poetry?"
    
    return response


def get_gemini_client():
    """Get a configured Gemini client with load-balanced API keys"""
    if not GEMINI_API_KEYS:
        raise ValueError("No Gemini API keys found in environment variables")
    
    # Randomly select an API key for load balancing
    api_key = random.choice(GEMINI_API_KEYS)
    genai.configure(api_key=api_key)
    return genai


def calculate_confidence_score(response_text: str, context: str = "") -> float:
    """
    Calculate confidence score based on response characteristics
    Returns a score between 0.0 and 1.0
    """
    score = 0.8  # Base confidence
    
    # Increase confidence if response mentions specific meters
    meters = ['अनुष्टुभ्', 'त्रिष्टुभ्', 'गायत्री', 'जगती', 'वसन्ततिलका', 'मन्दाक्रान्ता', 
              'Anushtubh', 'Trishtubh', 'Gayatri', 'Jagati', 'Vasantatilaka', 'Mandakranta']
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
        logger.info(f"Chat request - Message length: {len(message)}, Has image: {bool(image_data)}, Has audio: {bool(audio_data)}")
        
        # Validate persona
        if persona not in PERSONAS:
            return jsonify({
                'success': False,
                'error': f'Invalid persona. Choose from: {list(PERSONAS.keys())}'
            }), 400
        
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
                    return jsonify({
                        'success': False,
                        'error': 'Audio transcription service is not available. Please use text or image input.'
                    }), 500
                
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
                            extracted_audio_text = ' '.join([result.alternatives[0].transcript for result in response.results])
                            
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
                                extracted_audio_text = ' '.join([result.alternatives[0].transcript for result in response.results])
                                logger.info(f"Speech-to-Text extracted (fallback): {extracted_audio_text}")
                            else:
                                logger.warning("Speech-to-Text found no speech in audio")
                                return jsonify({
                                    'success': False,
                                    'error': 'Could not understand the audio. Please speak clearly or use text/image input.'
                                }), 400
                                
                    except Exception as recognition_error:
                        logger.error(f"Recognition error: {str(recognition_error)}")
                        return jsonify({
                            'success': False,
                            'error': 'Audio transcription failed. Please try again or use text/image input.'
                        }), 500
                        
                except Exception as stt_error:
                    logger.error(f"Speech-to-Text error: {str(stt_error)}")
                    return jsonify({
                        'success': False,
                        'error': 'Audio transcription service is not available. Please use text or image input.'
                    }), 500
                
                # Append transcribed text to message
                if message.strip():
                    message = f"{message}\n\n[Transcribed from audio]: {extracted_audio_text}"
                else:
                    message = extracted_audio_text or "Analyze this"
                
                logger.info(f"Audio transcription complete. Final message: {message}")
                
            except Exception as audio_error:
                logger.error(f"Audio processing error: {str(audio_error)}")
                return jsonify({
                    'success': False,
                    'error': f'Error processing audio: {str(audio_error)}'
                }), 500
        
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
                    return jsonify({
                        'success': False,
                        'error': 'Image data appears to be invalid or corrupted. Please try uploading again.'
                    }), 400
                
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
                    import PIL.Image
                    import io
                    img = PIL.Image.open(io.BytesIO(image_bytes))
                    # Tesseract returns dict with 'text' key
                    ocr_result = current_app.tesseract_ocr.extract_text(img)
                    extracted_ocr_text = ocr_result.get('text', '').strip()
                    logger.info(f"Tesseract OCR extracted {len(extracted_ocr_text)} characters")
                    
                else:
                    logger.error("No OCR service available")
                    return jsonify({
                        'success': False,
                        'error': 'OCR service is not available. Please contact support.'
                    }), 500
                
                if not extracted_ocr_text:
                    logger.warning("OCR extracted no text from image")
                    return jsonify({
                        'success': False,
                        'error': 'Could not extract any text from the image. Please ensure the image contains clear, readable Sanskrit text.'
                    }), 400
                
                # Append extracted text to user message
                if message.strip():
                    message = f"{message}\n\n[Extracted text from image]:\n{extracted_ocr_text}"
                else:
                    message = f"Find the chanda of this text:\n\n{extracted_ocr_text}"
                
                logger.info(f"OCR complete. Final message length: {len(message)}")
                
            except Exception as ocr_error:
                logger.error(f"OCR processing error: {str(ocr_error)}")
                return jsonify({
                    'success': False,
                    'error': f'Error processing image: {str(ocr_error)}'
                }), 500
        
        # Initialize conversation if new
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # =====================================================================
        # AGENTIC METER IDENTIFICATION
        # Check if user is asking for meter analysis
        # =====================================================================
        has_meter_intent, extracted_text = detect_meter_intent(message)
        
        # If we have OCR text and meter intent, use the OCR text for analysis
        if has_meter_intent and extracted_ocr_text:
            extracted_text = extracted_ocr_text
            logger.info(f"Using OCR-extracted text for meter analysis: {extracted_text[:100]}...")
        
        meter_analysis = None
        if has_meter_intent and extracted_text:
            # Perform automatic meter identification
            meter_analysis = analyze_meter_agentic(extracted_text)
            
            # Format the response
            agentic_response = format_meter_response(meter_analysis, persona)
            
            # Store conversation with meter data and image
            conversations[conversation_id].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat(),
                'has_image': bool(image_preview_data),
                'has_audio': bool(audio_data),
                'image_data': image_preview_data,  # Store image for display
                'ocr_text': extracted_ocr_text,
                'meter_intent_detected': True
            })
            
            conversations[conversation_id].append({
                'role': 'assistant',
                'content': agentic_response,
                'timestamp': datetime.now().isoformat(),
                'confidence': 0.95 if meter_analysis.get('found') else 0.75,
                'persona': persona,
                'meter_analysis': meter_analysis,
                'agentic_action': 'meter_identification'
            })
            
            return jsonify({
                'success': True,
                'response': agentic_response,
                'confidence': 0.95 if meter_analysis.get('found') else 0.75,
                'conversation_id': conversation_id,
                'persona': PERSONAS[persona]['name'],
                'timestamp': datetime.now().isoformat(),
                'agentic_action': 'meter_identification',
                'meter_data': meter_analysis
            })
        
        # =====================================================================
        # REGULAR AI CHAT (No meter intent detected)
        # =====================================================================
        
        # Get Gemini client
        genai_client = get_gemini_client()
        
        # Use text-only model (images are processed via OCR first)
        model = genai_client.GenerativeModel(
            model_name='gemini-2.5-flash',
            generation_config={
                'temperature': PERSONAS[persona]['temperature'],
                'top_p': PERSONAS[persona]['top_p'],
                'max_output_tokens': 4096,
            },
            system_instruction=PERSONAS[persona]['system_instruction']
        )
        
        # Build chat history for context
        chat_history = []
        for conv in conversations[conversation_id][-10:]:  # Last 10 messages
            chat_history.append({
                'role': 'user' if conv['role'] == 'user' else 'model',
                'parts': [conv['content']]
            })
        
        # Start chat session
        chat = model.start_chat(history=chat_history)
        
        # Send message and get response (text only - images already processed via OCR)
        try:
            logger.info(f"Sending message to Gemini (text only)")
            response = chat.send_message(message)
            
            # Check if response has valid content
            if not response or not hasattr(response, 'text'):
                finish_reason = getattr(response, 'finish_reason', None) if response else None
                logger.error(f"Gemini response failed - finish_reason: {finish_reason}")
                
                if finish_reason == 2:  # SAFETY
                    return jsonify({
                        'success': False,
                        'error': 'Content was blocked by safety filters. Please rephrase your question.'
                    }), 400
                elif finish_reason == 3:  # RECITATION
                    return jsonify({
                        'success': False,
                        'error': 'Content blocked due to recitation policy.'
                    }), 400
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Unable to generate a response. (Finish reason: {finish_reason})'
                    }), 400
            
            response_text = response.text
            logger.info(f"Gemini response received successfully, length: {len(response_text)}")
            
        except Exception as gemini_error:
            error_msg = str(gemini_error)
            logger.error(f"Gemini API error: {error_msg}")
            
            if 'finish_reason is 2' in error_msg or 'SAFETY' in error_msg:
                return jsonify({
                    'success': False,
                    'error': 'Content was blocked by safety filters. Please rephrase your question.'
                }), 400
            elif 'finish_reason is 3' in error_msg or 'RECITATION' in error_msg:
                return jsonify({
                    'success': False,
                    'error': 'Content blocked due to recitation policy.'
                }), 400
            elif 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': 'Service is temporarily busy. Please wait a moment and try again.'
                }), 429
            else:
                return jsonify({
                    'success': False,
                    'error': f'Error processing request: {error_msg}'
                }), 500
        
        # Calculate confidence score
        confidence = calculate_confidence_score(response_text, message)
        
        # Store conversation with image data
        conversations[conversation_id].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'has_image': bool(image_preview_data),
            'has_audio': bool(audio_data),
            'image_data': image_preview_data,  # Store image for display
            'ocr_text': extracted_ocr_text
        })
        
        conversations[conversation_id].append({
            'role': 'assistant',
            'content': response_text,
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'persona': persona
        })
        
        return jsonify({
            'success': True,
            'response': response_text,
            'confidence': confidence,
            'conversation_id': conversation_id,
            'persona': PERSONAS[persona]['name'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/history/<conversation_id>', methods=['GET'])
def get_history(conversation_id: str):
    """Get conversation history for a specific conversation ID"""
    try:
        if conversation_id not in conversations:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'messages': conversations[conversation_id]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/conversations', methods=['GET'])
def list_conversations():
    """List all conversation IDs"""
    try:
        return jsonify({
            'success': True,
            'conversations': [
                {
                    'id': conv_id,
                    'message_count': len(messages),
                    'last_updated': messages[-1]['timestamp'] if messages else None
                }
                for conv_id, messages in conversations.items()
            ]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/clear/<conversation_id>', methods=['DELETE'])
def clear_conversation(conversation_id: str):
    """Clear a specific conversation"""
    try:
        if conversation_id in conversations:
            del conversations[conversation_id]
        
        return jsonify({
            'success': True,
            'message': 'Conversation cleared'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/personas', methods=['GET'])
def get_personas():
    """Get available personas"""
    try:
        return jsonify({
            'success': True,
            'personas': {
                key: {
                    'name': value['name'],
                    'description': value['system_instruction'][:200] + '...'
                }
                for key, value in PERSONAS.items()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
            return jsonify({
                'success': False,
                'error': 'Text is required'
            }), 400
        
        # First, analyze the meter using the core chanda module
        # Import here to avoid circular dependencies
        from core.chanda import Chanda
        from config.settings import Settings
        
        settings = Settings()
        chanda = Chanda(data_path=str(settings.DATA_DIR))
        meter_result = chanda.identify_line(text)
        
        # Then, ask the AI to explain the result
        genai_client = get_gemini_client()
        model = genai_client.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=PERSONAS[persona]['system_instruction']
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
        
        response = model.generate_content(explanation_prompt)
        explanation = response.text
        
        confidence = calculate_confidence_score(explanation, text)
        
        # Store in conversation history
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        conversations[conversation_id].append({
            'role': 'user',
            'content': f"Analyze meter: {text}",
            'timestamp': datetime.now().isoformat(),
            'type': 'meter_analysis'
        })
        
        conversations[conversation_id].append({
            'role': 'assistant',
            'content': explanation,
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'persona': persona,
            'meter_data': meter_result
        })
        
        return jsonify({
            'success': True,
            'meter': meter_result.get('display_chanda_primary'),
            'lg_pattern': ''.join(meter_result.get('display_lg', [])),
            'syllables': meter_result.get('display_length'),
            'matra': meter_result.get('display_matra'),
            'explanation': explanation,
            'confidence': confidence,
            'conversation_id': conversation_id,
            'full_analysis': meter_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'api_keys_configured': len(GEMINI_API_KEYS),
        'personas_available': list(PERSONAS.keys())
    })
