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
