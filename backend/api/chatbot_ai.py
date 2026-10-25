"""Gemini key rotation, the lazily built RAG engine and response confidence scoring for the chatbot."""

import logging
import os
import random
from typing import List

from dotenv import load_dotenv
from google import genai

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


# --------------------------------------------------------------------------- #
# One chat turn: RAG context, then Gemini with key rotation on quota errors.

GEMINI_MODEL = 'gemini-2.5-flash'
RAG_MIN_SCORE = 0.5
RAG_DOCUMENTS = 5
RAG_CONTEXT_CHARS = 3000


class ChatReplyError(Exception):
    """Gemini could not answer; carries the user-facing message and HTTP status."""

    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.message = message
        self.status = status


def retrieve_rag_context(message: str):
    """(context text or None, retrieved documents) from the knowledge base for one question."""
    engine = get_rag_engine()
    logger.info(f"🔍 RAG Check: rag_engine={engine is not None}, is_ready={engine.is_ready() if engine else False}")
    if not (engine and engine.is_ready()):
        logger.warning("⚠️  RAG: Engine not available or not ready")
        return None, []
    try:
        logger.info(f"🔍 RAG: Retrieving relevant context for query: '{message[:100]}...'")
        documents = engine.retrieve(query=message, k=RAG_DOCUMENTS, min_score=RAG_MIN_SCORE)
        logger.info(f"📊 RAG: Retrieved {len(documents)} documents (threshold: {RAG_MIN_SCORE})")
        if not documents:
            logger.info(f"ℹ️  RAG: No relevant documents found (below threshold {RAG_MIN_SCORE})")
            return None, documents
        for i, doc in enumerate(documents[:3], 1):
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            logger.info(f"   Doc {i}: source={metadata.get('source', 'N/A')}, type={metadata.get('type', 'N/A')}")
        context = engine.format_context_for_prompt(
            documents=documents, include_source=True, max_length=RAG_CONTEXT_CHARS
        )
        logger.info(f"✅ RAG: Using {len(documents)} documents ({len(context)} chars context)")
        return context, documents
    except Exception as rag_error:
        logger.error(f"⚠️  RAG retrieval error: {rag_error}", exc_info=True)
        # Answer without RAG if retrieval fails; the documents found so far are still reported.
        return None, []


def ground_message(message: str, rag_context) -> str:
    """The prompt sent to Gemini: the question alone, or wrapped in the retrieved context."""
    if not rag_context:
        return message
    logger.info(f"📝 Enhanced message with {len(rag_context)} chars of context")
    return f"""Context from knowledge base (use this to ground your response when relevant):

{rag_context}

---

User question: {message}

Please answer using the provided context when relevant. Do not include source citations like [Source 1] or [Source N] in your response."""


def is_quota_error(error_msg: str) -> bool:
    return 'quota' in error_msg.lower() or '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg


def gemini_error_reply(error_msg: str) -> ChatReplyError:
    """The user-facing error for a Gemini failure that is not a quota error."""
    logger.error(f"Gemini API error: {error_msg}")
    if 'finish_reason is 2' in error_msg or 'SAFETY' in error_msg:
        return ChatReplyError('Content was blocked by safety filters. Please rephrase your question.', 400)
    if 'finish_reason is 3' in error_msg or 'RECITATION' in error_msg:
        return ChatReplyError('Content blocked due to recitation policy.', 400)
    return ChatReplyError(f'Error processing request: {error_msg}', 500)


def generate_reply(persona: dict, turns: list, prompt: str, rag_used: bool) -> str:
    """Send one prompt with the last turns as history, rotating API keys when a key's quota runs out."""
    from google.genai import types

    config = types.GenerateContentConfig(
        system_instruction=persona['system_instruction'],
        temperature=persona['temperature'],
        top_p=persona['top_p'],
        max_output_tokens=4096,
    )
    history = [
        types.Content(role='user' if turn['role'] == 'user' else 'model', parts=[types.Part(text=turn['content'])])
        for turn in turns
    ]
    client = get_gemini_client()
    chat = client.chats.create(model=GEMINI_MODEL, config=config, history=history)

    exhausted_keys = []
    max_retries = len(GEMINI_API_KEYS)
    for attempt in range(max_retries):
        try:
            logger.info(f"Sending message to Gemini (RAG-enhanced: {rag_used}, attempt: {attempt + 1}/{max_retries})")
            response = chat.send_message(prompt)
        except Exception as gemini_error:
            error_msg = str(gemini_error)
            if not is_quota_error(error_msg):
                raise gemini_error_reply(error_msg) from gemini_error

            current_key = client.api_key if hasattr(client, 'api_key') else None
            if current_key and current_key not in exhausted_keys:
                exhausted_keys.append(current_key)
            logger.warning(f"⚠️  API key quota exhausted ({len(exhausted_keys)}/{len(GEMINI_API_KEYS)} keys tried)")

            if attempt >= max_retries - 1:
                logger.error("❌ All retry attempts exhausted")
                raise ChatReplyError(
                    'Service is temporarily busy. Please wait a moment and try again.', 429
                ) from gemini_error
            try:
                client = get_gemini_client(exclude_keys=exhausted_keys)
                chat = client.chats.create(model=GEMINI_MODEL, config=config, history=history)
            except ValueError:
                logger.error(f"❌ All {len(GEMINI_API_KEYS)} API keys quota exhausted")
                raise ChatReplyError(
                    'Service is temporarily busy. All API keys have reached their quota. Please try again later.', 429
                ) from gemini_error
            logger.info("🔄 Retrying with different API key...")
            continue

        if not response or not hasattr(response, 'text'):
            logger.error("Gemini response failed - no text in response")
            raise ChatReplyError('Unable to generate a response.', 400)
        logger.info(f"Gemini response received successfully, length: {len(response.text)}")
        return response.text

    raise ChatReplyError('Failed to generate response after all retry attempts.', 500)
