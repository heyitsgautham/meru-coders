#!/bin/bash
# Quick Start Script for RAG-Enhanced Chatbot
# Meru Coders - SIH 2025

echo "=========================================="
echo "RAG-Enhanced Chatbot Quick Start"
echo "=========================================="
echo ""

# Navigate to backend
cd "$(dirname "$0")"
cd backend

echo "Step 1: Checking dependencies..."
if ! python -c "import langchain, chromadb, sentence_transformers" 2>/dev/null; then
    echo "❌ RAG dependencies not installed"
    echo "Installing now..."
    pip install langchain langchain-google-genai langchain-community chromadb sentence-transformers tiktoken
else
    echo "✅ Dependencies installed"
fi

echo ""
echo "Step 2: Checking vector database..."
if [ -d "data/chroma_db" ] && [ "$(ls -A data/chroma_db)" ]; then
    echo "✅ Vector database exists"
    echo "   Location: data/chroma_db"
    echo "   To rebuild: python scripts/build_vector_db.py --rebuild"
else
    echo "⚠️  Vector database not found"
    echo "Building now (this will take ~5 minutes)..."
    python scripts/build_vector_db.py --rebuild
    
    if [ $? -eq 0 ]; then
        echo "✅ Vector database built successfully"
    else
        echo "❌ Failed to build vector database"
        exit 1
    fi
fi

echo ""
echo "Step 3: Testing RAG engine..."
python -c "
import sys
sys.path.insert(0, '..')
from backend.core.rag_engine import RAGEngine

rag = RAGEngine()
if rag.is_ready():
    stats = rag.get_statistics()
    print(f'✅ RAG engine ready with {stats[\"total_documents\"]} documents')
else:
    print('❌ RAG engine not ready')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ RAG engine test failed"
    exit 1
fi

echo ""
echo "Step 4: Starting backend server..."
echo "=========================================="
echo ""
echo "🚀 Backend server starting with RAG enabled..."
echo ""
echo "Once started, test with:"
echo ""
echo "curl -X POST http://localhost:5000/api/chatbot/chat \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"message\": \"What is Anushtubh meter?\", \"persona\": \"default\"}'"
echo ""
echo "Look for [Source: ...] citations in the response!"
echo ""
echo "=========================================="
echo ""

# Start server
python run.py
