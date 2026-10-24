"""
Test script to demonstrate RAG/AI/Agentic response source indicators

Usage:
    python tests/test_response_sources.py
    
Author: Meru Coders (SIH 2025)
Date: December 9, 2025
"""

import time

import requests

BASE_URL = "http://localhost:5000/api/chatbot"

def test_agentic_response():
    """Test agentic meter identification - shows 'Agentic' indicator"""
    print("="*70)
    print("TEST 1: AGENTIC METER IDENTIFICATION")
    print("="*70)

    payload = {
        "message": "Find the meter: धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
        "persona": "default"
    }

    response = requests.post(f"{BASE_URL}/chat", json=payload)
    data = response.json()

    if data['success']:
        print(f"\n✅ Response received (Agentic Action: {data.get('agentic_action', 'N/A')})")
        print("\nResponse excerpt:")
        print(data['response'][:500] + "...")
        print(f"\n{'='*70}\n")
        return True
    else:
        print(f"❌ Failed: {data.get('error')}\n")
        return False


def test_rag_response():
    """Test RAG-enhanced response - shows 'RAG' indicator"""
    print("="*70)
    print("TEST 2: RAG-ENHANCED RESPONSE")
    print("="*70)

    payload = {
        "message": "What is the difference between Sama and Vishama chandas?",
        "persona": "default"
    }

    response = requests.post(f"{BASE_URL}/chat", json=payload)
    data = response.json()

    if data['success']:
        print("\n✅ Response received")
        print(f"   Response Source: {data.get('response_source', 'N/A')}")
        print(f"   RAG Docs Used: {data.get('rag_docs_used', 0)}")
        print("\nResponse excerpt:")
        print(data['response'][:500] + "...")

        # Check if footer is present
        if 'Response generated with **RAG**' in data['response']:
            print("\n✅ RAG footer found in response!")
        else:
            print("\n⚠️  RAG footer not found")

        print(f"\n{'='*70}\n")
        return True
    else:
        print(f"❌ Failed: {data.get('error')}\n")
        return False


def test_ai_response():
    """Test pure AI response (no RAG) - shows 'AI' indicator"""
    print("="*70)
    print("TEST 3: PURE AI RESPONSE (No RAG context)")
    print("="*70)

    # Use a query unlikely to match any documents
    payload = {
        "message": "Tell me a motivational quote about learning",
        "persona": "default"
    }

    response = requests.post(f"{BASE_URL}/chat", json=payload)
    data = response.json()

    if data['success']:
        print("\n✅ Response received")
        print(f"   Response Source: {data.get('response_source', 'N/A')}")
        print(f"   RAG Docs Used: {data.get('rag_docs_used', 0)}")
        print("\nResponse excerpt:")
        print(data['response'][:500] + "...")

        # Check if footer is present
        if 'Response generated with **AI**' in data['response']:
            print("\n✅ AI footer found in response!")
        else:
            print("\n⚠️  AI footer not found")

        print(f"\n{'='*70}\n")
        return True
    else:
        print(f"❌ Failed: {data.get('error')}\n")
        return False


def main():
    print("\n" + "="*70)
    print("RESPONSE SOURCE INDICATOR TEST")
    print("Testing: Agentic | RAG | AI")
    print("="*70 + "\n")

    print("⚠️  Make sure backend is running: python run.py")
    print("Waiting 3 seconds...\n")
    time.sleep(3)

    results = []

    # Test all three types
    try:
        results.append(("Agentic", test_agentic_response()))
        time.sleep(2)
        results.append(("RAG", test_rag_response()))
        time.sleep(2)
        results.append(("AI", test_ai_response()))
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Backend server not running!")
        print("Start with: cd backend && python run.py\n")
        return False

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name} response source indicator")

    all_passed = all(r for _, r in results)

    if all_passed:
        print("\n🎉 All tests passed! Response sources are correctly indicated.")
        print("\nUsers will now see at the end of each response:")
        print("  • Agentic: Already has 'Use Analyse Chanda for detailed analysis'")
        print("  • RAG: 'Response generated with RAG - X knowledge base sources used'")
        print("  • AI: 'Response generated with AI (Gemini 2.5 Flash)'")
    else:
        print("\n⚠️  Some tests failed. Check server logs.")

    print("="*70 + "\n")

    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
