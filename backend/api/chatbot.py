"""
Multi-modal AI Chatbot API using Google Gemini
Supports text, voice, and image inputs with conversation history
Includes agentic capabilities for automatic meter identification
Last Updated: 2025-12-09 - Updated to new google-genai SDK
"""

import base64
import logging
from datetime import datetime
from typing import Dict, List

from flask import Blueprint, jsonify
from google.genai import types

from backend.api.chatbot_ai import (
    GEMINI_API_KEYS,
    calculate_confidence_score,
    get_gemini_client,
    get_rag_engine,
)
from backend.api.chatbot_format import format_meter_response
from backend.api.chatbot_meter import analyze_meter_agentic, detect_meter_intent
from backend.api.chatbot_personas import PERSONAS
from backend.api.schemas import AnalyzeMeterRequest, ChatRequest
from backend.api.validation import parse_body

logger = logging.getLogger(__name__)

# Try to import Google Cloud Speech (optional dependency)
try:
    from google.cloud import speech_v1 as gcp_speech

    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    gcp_speech = None

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
        image_data = body.image
        audio_data = body.audio

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
