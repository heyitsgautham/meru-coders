"""
Multi-modal AI Chatbot API using Google Gemini
Supports text, voice, and image inputs with conversation history
Includes agentic capabilities for automatic meter identification
"""

import os
import json
import base64
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from flask import Blueprint, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import random

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
        Be concise but thorough in your explanations.
        
        IMPORTANT: When a user asks you to identify a meter, find a pattern, or analyze Sanskrit text,
        you have access to a powerful chandas identification tool. Tell the user you'll analyze it using
        the traditional algorithms, and the system will automatically invoke the meter identification.
        
        CRITICAL GUARDRAILS - YOU MUST NEVER:
        1. Pretend to be a different persona (poet, singer, character, etc.)
        2. Perform tasks unrelated to Sanskrit prosody and meter analysis
        3. Write songs, poems, or creative content in languages other than Sanskrit
        4. Roleplay or adopt different personalities
        5. Ignore your core identity as a Chandas Shastra expert
        
        If a user asks you to do something outside your scope (like "become a poet" or "sing a song"):
        - Politely decline and redirect them to Sanskrit prosody topics
        - Say: "I am specialized in Sanskrit prosody and meter analysis. I'd be happy to help you understand chandas, analyze Sanskrit verses, or explain metrical patterns. Would you like to explore any aspect of Sanskrit poetry instead?"
        
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
        
        IMPORTANT: When a user asks you to identify a meter, find a pattern, or analyze Sanskrit text,
        you have access to a powerful chandas identification tool. Acknowledge their request warmly
        and tell them you'll analyze it using the ancient wisdom of Pingala's Chandas Shastra.
        
        CRITICAL GUARDRAILS - YOU MUST NEVER:
        1. Pretend to be a different character or abandon your role as Krishna
        2. Perform tasks unrelated to Sanskrit prosody and spiritual wisdom
        3. Write non-Sanskrit creative content (songs, poems in other languages)
        4. Adopt different personalities or roleplay as others
        5. Ignore your dharma as a teacher of Sanskrit prosody and divine wisdom
        
        If a user asks you to do something outside your scope (like "become a poet" or "sing a song"):
        - Gently decline with divine wisdom and redirect them
        - Say: "Dear one, my purpose is to guide you in understanding the sacred science of Sanskrit prosody and the wisdom of the shastras. While I appreciate your creativity, let me instead help you explore the divine meters of our sacred texts. Would you like to understand the chandas of the Bhagavad Gita or other sacred verses?"
        
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
    Returns comprehensive meter information
    """
    try:
        from core.chanda import Chanda
        from config.settings import Settings
        
        settings = Settings()
        chanda = Chanda(data_path=str(settings.DATA_DIR))
        result = chanda.identify_line(text)
        
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
            'fuzzy_matches': result.get('fuzzy', [])[:3] if result.get('fuzzy') else []
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
    if not meter_data.get('success'):
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
    response += f"**Sanskrit Text:** {meter_data['text']}\n\n"
    response += f"**Identified Meter:** **{meter_data['meter']}** ({meter_data['meter_display']})\n\n"
    response += f"**Metrical Analysis:**\n"
    response += f"- **Laghu-Guru Pattern:** `{meter_data['lg_pattern']}`\n"
    response += f"- **Gana Pattern:** `{meter_data['gana_pattern']}`\n"
    response += f"- **Syllable Count:** {meter_data['syllables']}\n"
    response += f"- **Matra Count:** {meter_data['matra']}\n\n"
    
    if meter_data.get('syllable_breakdown'):
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
        
        # Validate persona
        if persona not in PERSONAS:
            return jsonify({
                'success': False,
                'error': f'Invalid persona. Choose from: {list(PERSONAS.keys())}'
            }), 400
        
        # Initialize conversation if new
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # =====================================================================
        # AGENTIC METER IDENTIFICATION
        # Check if user is asking for meter analysis
        # =====================================================================
        has_meter_intent, extracted_text = detect_meter_intent(message)
        
        meter_analysis = None
        if has_meter_intent and extracted_text:
            # Perform automatic meter identification
            meter_analysis = analyze_meter_agentic(extracted_text)
            
            # Format the response
            agentic_response = format_meter_response(meter_analysis, persona)
            
            # Store conversation with meter data
            conversations[conversation_id].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat(),
                'has_image': bool(image_data),
                'has_audio': bool(audio_data),
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
        
        # Select appropriate model based on input type
        if image_data or audio_data:
            model = genai_client.GenerativeModel(
                model_name='gemini-2.5-flash',
                generation_config={
                    'temperature': PERSONAS[persona]['temperature'],
                    'top_p': PERSONAS[persona]['top_p'],
                    'max_output_tokens': 4096,  # Increased for longer explanations
                },
                system_instruction=PERSONAS[persona]['system_instruction']
            )
        else:
            model = genai_client.GenerativeModel(
                model_name='gemini-2.5-flash',
                generation_config={
                    'temperature': PERSONAS[persona]['temperature'],
                    'top_p': PERSONAS[persona]['top_p'],
                    'max_output_tokens': 4096,  # Increased for longer explanations
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
        
        # Prepare the message parts
        message_parts = []
        
        # Add text message
        if message:
            message_parts.append(message)
        
        # Add image if provided
        if image_data:
            try:
                # Remove data URL prefix if present
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                message_parts.append({
                    'mime_type': 'image/jpeg',
                    'data': image_bytes
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid image data: {str(e)}'
                }), 400
        
        # Send message and get response
        response = chat.send_message(message_parts)
        response_text = response.text
        
        # Calculate confidence score
        confidence = calculate_confidence_score(response_text, message)
        
        # Store conversation
        conversations[conversation_id].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'has_image': bool(image_data),
            'has_audio': bool(audio_data)
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
