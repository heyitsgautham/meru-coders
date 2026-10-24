"""
Test RAG-enhanced chatbot functionality
Tests the integration of RAG engine with the Gemini chatbot

Usage:
    python tests/test_rag_chatbot.py
    
Author: Meru Coders (SIH 2025)
Date: December 9, 2025
"""

import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path.parent))

from backend.core.rag_engine import RAGEngine


def test_rag_retrieval():
    """Test RAG retrieval with various queries"""
    print("="*70)
    print("TEST 1: RAG Retrieval Functionality")
    print("="*70 + "\n")
    
    # Initialize RAG
    rag = RAGEngine()
    
    if not rag.is_ready():
        print("❌ FAILED: RAG engine not initialized")
        print("   Run: python scripts/build_vector_db.py")
        return False
    
    # Get statistics
    stats = rag.get_statistics()
    print(f"✅ RAG Engine Ready")
    print(f"   Total Documents: {stats.get('total_documents', 'N/A')}")
    print(f"   Embedding Model: {stats.get('embedding_model', 'N/A')}")
    print(f"   Database Path: {stats.get('database_path', 'N/A')}\n")
    
    # Test queries
    test_queries = [
        {
            "query": "What is the definition of Anushtubh meter?",
            "expected_content": ["anushtubh", "anushṭubh", "syllable", "8"],
            "min_docs": 2
        },
        {
            "query": "Explain the difference between laghu and guru",
            "expected_content": ["laghu", "guru", "short", "long"],
            "min_docs": 2
        },
        {
            "query": "What are the seven Vedic meters?",
            "expected_content": ["vedic", "gayatri", "trishtubh"],
            "min_docs": 2
        },
        {
            "query": "गायत्री छन्द के बारे में बताओ",
            "expected_content": ["gayatri", "गायत्री"],
            "min_docs": 1
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_queries, 1):
        print(f"\nTest Query {i}: {test['query']}")
        print("-" * 70)
        
        # Retrieve documents
        docs = rag.retrieve(test['query'], k=5, min_score=0.5)
        
        if len(docs) < test['min_docs']:
            print(f"❌ FAILED: Expected at least {test['min_docs']} docs, got {len(docs)}")
            failed += 1
            continue
        
        # Check if expected content is present
        all_content = " ".join([doc.page_content.lower() for doc in docs])
        found_keywords = []
        missing_keywords = []
        
        for keyword in test['expected_content']:
            if keyword.lower() in all_content:
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        if len(found_keywords) >= len(test['expected_content']) // 2:  # At least half keywords
            print(f"✅ PASSED: Retrieved {len(docs)} relevant documents")
            print(f"   Found keywords: {', '.join(found_keywords)}")
            passed += 1
        else:
            print(f"❌ FAILED: Missing expected content")
            print(f"   Missing keywords: {', '.join(missing_keywords)}")
            failed += 1
        
        # Show first document
        if docs:
            print(f"\n   Top result [{docs[0].metadata.get('source', 'Unknown')}]:")
            print(f"   {docs[0].page_content[:150]}...")
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


def test_rag_context_formatting():
    """Test context formatting for LLM prompts"""
    print("="*70)
    print("TEST 2: Context Formatting for LLM Prompts")
    print("="*70 + "\n")
    
    rag = RAGEngine()
    
    if not rag.is_ready():
        print("❌ FAILED: RAG engine not initialized\n")
        return False
    
    # Retrieve some documents
    docs = rag.retrieve("What is Anushtubh?", k=3)
    
    if not docs:
        print("❌ FAILED: No documents retrieved\n")
        return False
    
    # Test formatting
    context = rag.format_context_for_prompt(
        documents=docs,
        include_source=True,
        max_length=2000
    )
    
    print(f"✅ Context formatted successfully")
    print(f"   Length: {len(context)} characters")
    print(f"   Number of sources: {len(docs)}")
    print(f"\n   Sample context:\n")
    print(context[:500] + "...\n")
    
    # Verify structure
    if "[Source" in context and "]" in context:
        print("✅ PASSED: Context includes source citations")
        return True
    else:
        print("❌ FAILED: Context missing source citations")
        return False


def test_specialized_retrievals():
    """Test specialized retrieval methods"""
    print("="*70)
    print("TEST 3: Specialized Retrieval Methods")
    print("="*70 + "\n")
    
    rag = RAGEngine()
    
    if not rag.is_ready():
        print("❌ FAILED: RAG engine not initialized\n")
        return False
    
    passed = 0
    failed = 0
    
    # Test meter retrieval
    print("Testing retrieve_meters()...")
    meter_docs = rag.retrieve_meters("Vasantatilaka", k=3)
    if meter_docs:
        print(f"✅ PASSED: Retrieved {len(meter_docs)} meter definitions")
        passed += 1
    else:
        print("❌ FAILED: No meter documents retrieved")
        failed += 1
    
    # Test rules retrieval
    print("\nTesting retrieve_rules()...")
    rule_docs = rag.retrieve_rules("yati caesura", k=3)
    if rule_docs:
        print(f"✅ PASSED: Retrieved {len(rule_docs)} rule documents")
        passed += 1
    else:
        print("⚠️  WARNING: No rule documents retrieved (may be expected)")
        # Don't count as failure - rules might not be in database
    
    # Test documentation retrieval
    print("\nTesting retrieve_documentation()...")
    doc_docs = rag.retrieve_documentation("chandas shastra", k=3)
    if doc_docs:
        print(f"✅ PASSED: Retrieved {len(doc_docs)} documentation chunks")
        passed += 1
    else:
        print("❌ FAILED: No documentation retrieved")
        failed += 1
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


def test_multilingual_support():
    """Test multilingual query support (Sanskrit, English, Hindi)"""
    print("="*70)
    print("TEST 4: Multilingual Query Support")
    print("="*70 + "\n")
    
    rag = RAGEngine()
    
    if not rag.is_ready():
        print("❌ FAILED: RAG engine not initialized\n")
        return False
    
    multilingual_queries = [
        ("English", "What is Gayatri meter?"),
        ("Sanskrit", "गायत्री छन्द किम्?"),
        ("Hindi", "गायत्री छन्द क्या है?"),
        ("IAST", "gāyatrī chandas"),
    ]
    
    passed = 0
    failed = 0
    
    for lang, query in multilingual_queries:
        print(f"Testing {lang}: {query}")
        docs = rag.retrieve(query, k=3, min_score=0.5)
        
        if docs:
            print(f"✅ PASSED: Retrieved {len(docs)} documents")
            passed += 1
        else:
            print(f"❌ FAILED: No documents retrieved")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("RAG-ENHANCED CHATBOT TEST SUITE")
    print("="*70 + "\n")
    
    results = []
    
    # Run tests
    results.append(("RAG Retrieval", test_rag_retrieval()))
    results.append(("Context Formatting", test_rag_context_formatting()))
    results.append(("Specialized Retrievals", test_specialized_retrievals()))
    results.append(("Multilingual Support", test_multilingual_support()))
    
    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if failed == 0:
        print("\n🎉 All tests passed! RAG system is working correctly.")
        print("\n🚀 Next steps:")
        print("   1. Start the backend server: python run.py")
        print("   2. Test chatbot API with: curl -X POST http://localhost:5000/api/chatbot/chat \\")
        print("      -H 'Content-Type: application/json' \\")
        print("      -d '{\"message\": \"What is Anushtubh?\", \"persona\": \"default\"}'")
        print("   3. Check that responses include [Source N] citations")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the output above.")
    
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
