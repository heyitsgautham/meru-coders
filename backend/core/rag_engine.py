"""
RAG (Retrieval-Augmented Generation) Engine for Sanskrit Prosody Chatbot
Provides semantic search and context retrieval for knowledge-grounded responses

Features:
- Semantic search across 1,920+ meters, documentation, and examples
- Multi-source retrieval (meters, rules, sacred texts)
- Confidence-based ranking and filtering
- Citation formatting for source attribution

Author: Meru Coders (SIH 2025)
Date: December 9, 2025
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for chandas knowledge base
    
    Provides semantic search capabilities across:
    - Meter definitions (1,920+ entries)
    - Sanskrit prosody rules
    - Example verses
    - Documentation and tutorials
    """
    
    def __init__(
        self,
        chroma_path: str = "data/chroma_db",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        device: str = "cpu"
    ):
        """
        Initialize the RAG engine
        
        Args:
            chroma_path: Path to ChromaDB directory (relative to backend/)
            embedding_model: HuggingFace model name for embeddings
            device: Device to run embeddings on ('cpu' or 'cuda')
        """
        self.chroma_path = Path(__file__).parent.parent / chroma_path
        self.embedding_model = embedding_model
        self.device = device
        
        logger.info(f"🔧 Initializing RAG Engine")
        logger.info(f"   ChromaDB: {self.chroma_path}")
        logger.info(f"   Embedding Model: {embedding_model}")
        
        # Check if database exists
        if not self.chroma_path.exists():
            logger.warning(f"⚠️  ChromaDB not found at {self.chroma_path}")
            logger.warning(f"   Run: python scripts/build_vector_db.py")
            self.vectorstore = None
            return
        
        # Initialize embeddings
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': device},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            # Load vector store
            self.vectorstore = Chroma(
                persist_directory=str(self.chroma_path),
                embedding_function=self.embeddings,
                collection_name="chandas_knowledge"
            )
            
            # Get collection stats
            count = self.vectorstore._collection.count()
            logger.info(f"✅ RAG Engine initialized with {count} documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Engine: {e}")
            self.vectorstore = None
    
    def is_ready(self) -> bool:
        """Check if RAG engine is ready to use"""
        return self.vectorstore is not None
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: float = 0.5
    ) -> List[Document]:
        """
        Retrieve top-k relevant documents for a query
        
        Args:
            query: User's question or search query
            k: Number of documents to retrieve
            filter_metadata: Metadata filters (e.g., {"type": "meter_definition"})
            min_score: Minimum relevance score (0.0 to 1.0)
        
        Returns:
            List of Document objects with page_content and metadata
        """
        if not self.is_ready():
            logger.warning("⚠️  RAG Engine not initialized, returning empty results")
            return []
        
        try:
            # Perform semantic search with scores
            docs_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
                query=query,
                k=k * 2,  # Retrieve extra for filtering
                filter=filter_metadata
            )
            
            # Filter by minimum score and limit to k
            filtered_docs = [
                doc for doc, score in docs_with_scores
                if score >= min_score
            ][:k]
            
            logger.info(f"🔍 Retrieved {len(filtered_docs)}/{k} documents for query: '{query[:50]}...'")
            
            return filtered_docs
            
        except Exception as e:
            logger.error(f"❌ Retrieval failed: {e}")
            return []
    
    def retrieve_with_scores(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        Retrieve documents with relevance scores
        
        Args:
            query: User's question
            k: Number of documents to retrieve
            filter_metadata: Metadata filters
        
        Returns:
            List of (Document, score) tuples, sorted by score descending
        """
        if not self.is_ready():
            return []
        
        try:
            docs_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
                query=query,
                k=k,
                filter=filter_metadata
            )
            
            logger.info(f"🔍 Retrieved {len(docs_with_scores)} documents with scores")
            
            return docs_with_scores
            
        except Exception as e:
            logger.error(f"❌ Retrieval with scores failed: {e}")
            return []
    
    def retrieve_meters(
        self,
        query: str,
        k: int = 5,
        category: Optional[str] = None
    ) -> List[Document]:
        """
        Retrieve meter definitions specifically
        
        Args:
            query: Meter name, pattern, or description
            k: Number of meters to retrieve
            category: Filter by category (sama, vishama, vedic, etc.)
        
        Returns:
            List of meter definition documents
        """
        filter_dict = {"type": "meter_definition"}
        if category:
            filter_dict["category"] = category
        
        return self.retrieve(query, k=k, filter_metadata=filter_dict)
    
    def retrieve_examples(
        self,
        meter_name: str,
        k: int = 3
    ) -> List[Document]:
        """
        Retrieve example verses for a specific meter
        
        Args:
            meter_name: Name of the meter (Sanskrit or IAST)
            k: Number of examples to retrieve
        
        Returns:
            List of example verse documents
        """
        filter_dict = {"type": "example_verse"}
        query = f"Example verses for {meter_name} meter"
        
        return self.retrieve(query, k=k, filter_metadata=filter_dict)
    
    def retrieve_rules(
        self,
        topic: str,
        k: int = 5
    ) -> List[Document]:
        """
        Retrieve prosody rules and guidelines
        
        Args:
            topic: Rule topic (e.g., "laghu guru", "yati", "gana")
            k: Number of rule documents to retrieve
        
        Returns:
            List of rule documents
        """
        filter_dict = {"type": "rules"}
        
        return self.retrieve(topic, k=k, filter_metadata=filter_dict)
    
    def retrieve_documentation(
        self,
        query: str,
        k: int = 5
    ) -> List[Document]:
        """
        Retrieve general documentation and tutorials
        
        Args:
            query: Documentation search query
            k: Number of documents to retrieve
        
        Returns:
            List of documentation chunks
        """
        filter_dict = {"type": "documentation"}
        
        return self.retrieve(query, k=k, filter_metadata=filter_dict)
    
    def format_context_for_prompt(
        self,
        documents: List[Document],
        include_source: bool = True,
        max_length: int = 3000
    ) -> str:
        """
        Format retrieved documents into context string for LLM prompt
        
        Args:
            documents: Retrieved documents
            include_source: Whether to include source citations
            max_length: Maximum length of formatted context
        
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(documents):
            # Extract metadata
            source = doc.metadata.get('source', 'Unknown')
            doc_type = doc.metadata.get('type', 'document')
            meter_name = doc.metadata.get('meter_name', '')
            
            # Format document
            if include_source:
                header = f"[Source {i+1}: {source}]"
                if meter_name:
                    header += f" - {meter_name}"
                formatted = f"{header}\n{doc.page_content}\n"
            else:
                formatted = f"{doc.page_content}\n"
            
            # Check length limit
            if current_length + len(formatted) > max_length:
                break
            
            context_parts.append(formatted)
            current_length += len(formatted)
        
        return "\n".join(context_parts)
    
    def hybrid_retrieve(
        self,
        query: str,
        k: int = 5,
        alpha: float = 0.7
    ) -> List[Document]:
        """
        Hybrid retrieval combining semantic search with keyword matching
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            alpha: Weight for semantic search (1-alpha for keyword)
        
        Returns:
            List of documents ranked by hybrid score
        """
        # For now, just use semantic search
        # TODO: Implement keyword search and score fusion
        return self.retrieve(query, k=k)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database
        
        Returns:
            Dictionary with database statistics
        """
        if not self.is_ready():
            return {"status": "not_initialized"}
        
        try:
            total_docs = self.vectorstore._collection.count()
            
            # Get document type counts
            # Note: This is a simplified version; actual implementation
            # would need to query metadata efficiently
            
            return {
                "status": "ready",
                "total_documents": total_docs,
                "embedding_model": self.embedding_model,
                "database_path": str(self.chroma_path),
                "embedding_dimensions": 768  # For mpnet-base
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {"status": "error", "error": str(e)}


# Test function for standalone usage
def test_rag_engine():
    """Test the RAG engine with sample queries"""
    print("🧪 Testing RAG Engine\n")
    
    # Initialize
    rag = RAGEngine()
    
    if not rag.is_ready():
        print("❌ RAG Engine not ready. Build vector database first:")
        print("   python scripts/build_vector_db.py")
        return
    
    # Test queries
    test_queries = [
        "What is Anushtubh meter?",
        "Explain laghu and guru syllables",
        "Show me examples of Vasantatilaka",
        "What are the Vedic meters?",
        "गायत्री छन्द"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        # Retrieve documents
        docs = rag.retrieve(query, k=3)
        
        if docs:
            print(f"\n✅ Found {len(docs)} relevant documents:\n")
            for i, doc in enumerate(docs, 1):
                print(f"{i}. [{doc.metadata.get('source', 'Unknown')}]")
                print(f"   Type: {doc.metadata.get('type', 'N/A')}")
                print(f"   Content: {doc.page_content[:150]}...")
                print()
        else:
            print("❌ No documents found\n")
    
    # Print statistics
    print(f"\n{'='*60}")
    print("📊 Database Statistics")
    print('='*60)
    stats = rag.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    test_rag_engine()
