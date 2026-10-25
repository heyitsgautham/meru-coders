"""
Multi-modal AI Chatbot API using Google Gemini
Supports text, voice, and image inputs with conversation history
Includes agentic capabilities for automatic meter identification
Last Updated: 2025-12-09 - Updated to new google-genai SDK
"""

import logging
from datetime import datetime
from typing import Dict, List

from flask import Blueprint, current_app, jsonify
from google.genai import types

from backend.api.chatbot_ai import (
    GEMINI_API_KEYS,
    ChatReplyError,
    calculate_confidence_score,
    generate_reply,
    get_gemini_client,
    ground_message,
    retrieve_rag_context,
)
from backend.api.chatbot_format import format_meter_response
from backend.api.chatbot_media import ChatInputError, extract_image_text, transcribe_audio
from backend.api.chatbot_meter import analyze_meter_agentic, detect_meter_intent
from backend.api.chatbot_personas import PERSONAS
from backend.api.schemas import AnalyzeMeterRequest, ChatRequest
from backend.api.validation import parse_body

logger = logging.getLogger(__name__)

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

# In-memory conversation storage (replace with database in production)
conversations: Dict[str, List[Dict]] = {}


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
    body = parse_body(ChatRequest)
    try:
        message = body.message
        conversation_id = body.conversation_id or f"conv_{datetime.now().timestamp()}"
        persona = body.persona
        logger.info(
            f"Chat request - Message length: {len(message)}, Has image: {bool(body.image)}, Has audio: {bool(body.audio)}"
        )
        if persona not in PERSONAS:
            return jsonify({'success': False, 'error': f'Invalid persona. Choose from: {list(PERSONAS.keys())}'}), 400

        try:
            if body.audio:
                transcript = transcribe_audio(body.audio)
                message = f"{message}\n\n[Transcribed from audio]: {transcript}" if message.strip() else transcript
                logger.info(f"Audio transcription complete. Final message: {message}")
            ocr_text = None
            if body.image:
                ocr_text = extract_image_text(body.image, current_app)
                if message.strip():
                    message = f"{message}\n\n[Extracted text from image]:\n{ocr_text}"
                else:
                    message = f"Find the chanda of this text:\n\n{ocr_text}"
                logger.info(f"OCR complete. Final message length: {len(message)}")
        except ChatInputError as error:
            return jsonify({'success': False, 'error': error.message}), error.status

        history = conversations.setdefault(conversation_id, [])
        user_turn = {
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'has_image': bool(body.image),
            'has_audio': bool(body.audio),
            'image_data': body.image,  # Store image for display
            'ocr_text': ocr_text,
        }

        # A request to identify a meter is answered by the engine, not by Gemini.
        has_meter_intent, meter_text, requested_fields = detect_meter_intent(message)
        if has_meter_intent and ocr_text:
            meter_text = ocr_text
            logger.info(f"Using OCR-extracted text for meter analysis: {meter_text[:100]}...")
        if has_meter_intent and meter_text:
            return _reply_with_meter_analysis(
                history, user_turn, meter_text, persona, requested_fields, conversation_id
            )

        rag_context, retrieved_docs = retrieve_rag_context(message)
        try:
            response_text = generate_reply(
                PERSONAS[persona], history[-10:], ground_message(message, rag_context), bool(rag_context)
            )
        except ChatReplyError as error:
            return jsonify({'success': False, 'error': error.message}), error.status

        confidence = calculate_confidence_score(response_text, message)
        source = 'rag' if rag_context else 'ai'
        docs_used = len(retrieved_docs) if retrieved_docs else 0
        history.append(user_turn)
        history.append(
            {
                'role': 'assistant',
                'content': response_text,
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'persona': persona,
                'response_source': source,
                'rag_docs_used': docs_used,
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
                'response_source': source,
                'rag_docs_used': docs_used,
            }
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _reply_with_meter_analysis(history, user_turn, meter_text, persona, requested_fields, conversation_id):
    """Identify the meter of meter_text, store both turns, and answer with the formatted analysis."""
    meter_analysis = analyze_meter_agentic(meter_text)
    reply = format_meter_response(meter_analysis, persona, requested_fields, add_analyze_link=True)
    confidence = 0.95 if meter_analysis.get('found') else 0.75
    history.append({**user_turn, 'meter_intent_detected': True})
    history.append(
        {
            'role': 'assistant',
            'content': reply,
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'persona': persona,
            'meter_analysis': meter_analysis,
            'agentic_action': 'meter_identification',
        }
    )
    return jsonify(
        {
            'success': True,
            'response': reply,
            'confidence': confidence,
            'conversation_id': conversation_id,
            'persona': PERSONAS[persona]['name'],
            'timestamp': datetime.now().isoformat(),
            'agentic_action': 'meter_identification',
            'meter_data': meter_analysis,
        }
    )


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
    body = parse_body(AnalyzeMeterRequest)
    try:
        text = body.text
        conversation_id = body.conversation_id or f"conv_{datetime.now().timestamp()}"
        persona = body.persona

        if not text:
            return jsonify({'success': False, 'error': 'Text is required'}), 400

        # First, analyze the meter using the core chanda module
        # Import here to avoid circular dependencies
        from backend.core.engine import get_engine

        meter_result = get_engine().identify_line(text)

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
