"""
Embeddings Utility Module for RAG System
Provides helper functions for embedding generation and management

Author: Meru Coders (SIH 2025)
Date: December 9, 2025
"""

from typing import List, Dict, Any
import logging

from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


# Supported embedding models (multilingual for Sanskrit support)
EMBEDDING_MODELS = {
    "default": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "large": "intfloat/multilingual-e5-large",
    "small": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "indic": "l3cube-pune/indic-sentence-bert-nli"
}


def get_embedding_model(
    model_name: str = "default",
    device: str = "cpu",
    normalize: bool = True
) -> HuggingFaceEmbeddings:
    """
    Get an embedding model instance
    
    Args:
        model_name: Model identifier (default, large, small, indic) or full HF model path
        device: Device to run on ('cpu' or 'cuda')
        normalize: Whether to normalize embeddings
    
    Returns:
        HuggingFaceEmbeddings instance
    """
    # Resolve model name
    if model_name in EMBEDDING_MODELS:
        full_model_name = EMBEDDING_MODELS[model_name]
    else:
        full_model_name = model_name
    
    logger.info(f"📦 Loading embedding model: {full_model_name}")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=full_model_name,
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': normalize}
    )
    
    return embeddings


def get_embedding_dimensions(model_name: str = "default") -> int:
    """
    Get the embedding dimensions for a model
    
    Args:
        model_name: Model identifier
    
    Returns:
        Number of dimensions in embeddings
    """
    dimensions = {
        "default": 768,  # mpnet-base
        "large": 1024,   # e5-large
        "small": 384,    # MiniLM
        "indic": 768     # indic-bert
    }
    
    return dimensions.get(model_name, 768)


def batch_embed_texts(
    texts: List[str],
    model_name: str = "default",
    batch_size: int = 32,
    device: str = "cpu"
) -> List[List[float]]:
    """
    Embed a batch of texts
    
    Args:
        texts: List of texts to embed
        model_name: Embedding model to use
        batch_size: Batch size for processing
        device: Device to run on
    
    Returns:
        List of embedding vectors
    """
    embeddings_model = get_embedding_model(model_name, device)
    
    # Embed in batches
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = embeddings_model.embed_documents(batch)
        all_embeddings.extend(batch_embeddings)
        
        if (i + batch_size) % 100 == 0:
            logger.info(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)} texts")
    
    return all_embeddings


def compute_similarity(
    text1: str,
    text2: str,
    model_name: str = "default",
    device: str = "cpu"
) -> float:
    """
    Compute cosine similarity between two texts
    
    Args:
        text1: First text
        text2: Second text
        model_name: Embedding model to use
        device: Device to run on
    
    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    import numpy as np
    
    embeddings_model = get_embedding_model(model_name, device)
    
    # Get embeddings
    emb1 = embeddings_model.embed_query(text1)
    emb2 = embeddings_model.embed_query(text2)
    
    # Compute cosine similarity
    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    return float(similarity)


def preprocess_text_for_embedding(text: str) -> str:
    """
    Preprocess text before embedding
    
    Args:
        text: Raw text
    
    Returns:
        Preprocessed text
    """
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long (most models have 512 token limit)
    max_chars = 2000  # Rough approximation
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
    
    return text


# Test function
def test_embeddings():
    """Test embedding functionality"""
    print("🧪 Testing Embeddings Module\n")
    
    # Test texts (Sanskrit prosody related)
    test_texts = [
        "अनुष्टुभ् छन्द में प्रत्येक पाद में आठ अक्षर होते हैं",
        "Anushtubh meter has 8 syllables per pada",
        "गायत्री वैदिक छन्द है जिसमें तीन पाद होते हैं"
    ]
    
    # Get embedding model
    model = get_embedding_model("default", "cpu")
    
    # Test single embedding
    print("📝 Testing single text embedding:")
    emb = model.embed_query(test_texts[0])
    print(f"   Text: {test_texts[0][:50]}...")
    print(f"   Embedding dimensions: {len(emb)}")
    print(f"   First 5 values: {emb[:5]}\n")
    
    # Test batch embedding
    print("📝 Testing batch embedding:")
    embeddings = model.embed_documents(test_texts)
    print(f"   Number of texts: {len(test_texts)}")
    print(f"   Embeddings shape: {len(embeddings)} x {len(embeddings[0])}\n")
    
    # Test similarity
    print("📝 Testing similarity computation:")
    sim = compute_similarity(test_texts[0], test_texts[1], "default", "cpu")
    print(f"   Text 1: {test_texts[0][:40]}...")
    print(f"   Text 2: {test_texts[1][:40]}...")
    print(f"   Similarity: {sim:.4f}\n")
    
    print("✅ All tests passed!")


if __name__ == "__main__":
    test_embeddings()
