#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Multi-modal AI Chatbot API

Tests all chatbot endpoints including text, image, and persona switching.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


import requests

# Configuration
API_BASE_URL = "http://localhost:5000"
CHATBOT_API = f"{API_BASE_URL}/api/chatbot"

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test(name):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Testing: {name}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")


def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    print(f"{RED}✗ {message}{RESET}")


def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")


def test_health_check():
    """Test chatbot health endpoint"""
    print_test("Health Check")

    try:
        response = requests.get(f"{CHATBOT_API}/health")
        data = response.json()

        assert response.status_code == 200, "Status code should be 200"
        assert data['success'] == True, "Should be successful"
        assert data['status'] == 'healthy', "Should be healthy"
        assert data['api_keys_configured'] > 0, "Should have API keys configured"

        print_success("Health check passed")
        print_info(f"API keys configured: {data['api_keys_configured']}")
        print_info(f"Personas available: {', '.join(data['personas_available'])}")

        return True
    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        return False


def test_get_personas():
    """Test getting available personas"""
    print_test("Get Personas")

    try:
        response = requests.get(f"{CHATBOT_API}/personas")
        data = response.json()

        assert response.status_code == 200, "Status code should be 200"
        assert data['success'] == True, "Should be successful"
        assert 'default' in data['personas'], "Should have default persona"
        assert 'krishna' in data['personas'], "Should have krishna persona"

        print_success("Personas retrieved successfully")
        for key, value in data['personas'].items():
            print_info(f"{key}: {value['name']}")

        return True
    except Exception as e:
        print_error(f"Get personas failed: {str(e)}")
        return False


def test_simple_chat():
    """Test simple text chat"""
    print_test("Simple Text Chat")

    try:
        message = "What is Anushtubh meter?"

        response = requests.post(f"{CHATBOT_API}/chat", json={
            "message": message,
            "persona": "default"
        })
        data = response.json()

        assert response.status_code == 200, "Status code should be 200"
        assert data['success'] == True, "Should be successful"
        assert 'response' in data, "Should have response"
        assert 'confidence' in data, "Should have confidence score"
        assert 'conversation_id' in data, "Should have conversation ID"

        print_success("Simple chat successful")
        print_info(f"User: {message}")
        print_info(f"Assistant: {data['response'][:100]}...")
        print_info(f"Confidence: {data['confidence']:.2%}")
        print_info(f"Conversation ID: {data['conversation_id']}")

        return data['conversation_id']
    except Exception as e:
        print_error(f"Simple chat failed: {str(e)}")
        return None


def test_conversation_continuity(conversation_id):
    """Test conversation continuity"""
    print_test("Conversation Continuity")

    if not conversation_id:
        print_error("No conversation ID provided")
        return False

    try:
        message = "Can you give me an example?"

        response = requests.post(f"{CHATBOT_API}/chat", json={
            "message": message,
            "conversation_id": conversation_id,
            "persona": "default"
        })
        data = response.json()

        assert response.status_code == 200, "Status code should be 200"
        assert data['success'] == True, "Should be successful"
        assert data['conversation_id'] == conversation_id, "Should maintain conversation ID"

        print_success("Conversation continuity maintained")
        print_info(f"User: {message}")
        print_info(f"Assistant: {data['response'][:100]}...")

        return True
    except Exception as e:
        print_error(f"Conversation continuity failed: {str(e)}")
        return False


def test_persona_switching(conversation_id):
    """Test persona switching"""
    print_test("Persona Switching")

    if not conversation_id:
        print_error("No conversation ID provided")
        return False

    try:
        message = "Tell me about the beauty of Sanskrit poetry"

        # Test with Krishna persona
        response = requests.post(f"{CHATBOT_API}/chat", json={
            "message": message,
            "conversation_id": conversation_id,
            "persona": "krishna"
        })
        data = response.json()

        assert response.status_code == 200, "Status code should be 200"
        assert data['success'] == True, "Should be successful"
        assert data['persona'] == "Krishna", "Should be Krishna persona"

        print_success("Persona switching successful")
        print_info(f"Persona: {data['persona']}")
        print_info(f"Response: {data['response'][:100]}...")

        return True
    except Exception as e:
        print_error(f"Persona switching failed: {str(e)}")
        return False


def test_get_history(conversation_id):
    """Test getting conversation history"""
    print_test("Get Conversation History")

    if not conversation_id:
        print_error("No conversation ID provided")
        return False

    try:
        response = requests.get(f"{CHATBOT_API}/history/{conversation_id}")
        data = response.json()

        assert response.status_code == 200, "Status code should be 200"
        assert data['success'] == True, "Should be successful"
        assert 'messages' in data, "Should have messages"
        assert len(data['messages']) > 0, "Should have at least one message"

        print_success("History retrieved successfully")
        print_info(f"Total messages: {len(data['messages'])}")

        return True
    except Exception as e:
        print_error(f"Get history failed: {str(e)}")
        return False


def test_meter_analysis():
    """Test specialized meter analysis endpoint"""
    print_test("Meter Analysis with AI Explanation")

    try:
        text = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"

        response = requests.post(f"{CHATBOT_API}/analyze-meter", json={
            "text": text,
            "persona": "default"
        })
        data = response.json()

        assert response.status_code == 200, "Status code should be 200"
        assert data['success'] == True, "Should be successful"
        assert 'meter' in data, "Should have meter"
        assert 'explanation' in data, "Should have explanation"
        assert 'lg_pattern' in data, "Should have L-G pattern"

        print_success("Meter analysis successful")
        print_info(f"Text: {text}")
        print_info(f"Identified Meter: {data['meter']}")
        print_info(f"L-G Pattern: {data['lg_pattern']}")
        print_info(f"Syllables: {data['syllables']}")
        print_info(f"Explanation: {data['explanation'][:100]}...")

        return True
    except Exception as e:
        print_error(f"Meter analysis failed: {str(e)}")
        return False


def test_clear_conversation(conversation_id):
    """Test clearing conversation"""
    print_test("Clear Conversation")

    if not conversation_id:
        print_error("No conversation ID provided")
        return False

    try:
        response = requests.delete(f"{CHATBOT_API}/clear/{conversation_id}")
        data = response.json()

        assert response.status_code == 200, "Status code should be 200"
        assert data['success'] == True, "Should be successful"

        print_success("Conversation cleared successfully")

        return True
    except Exception as e:
        print_error(f"Clear conversation failed: {str(e)}")
        return False


def test_list_conversations():
    """Test listing all conversations"""
    print_test("List Conversations")

    try:
        response = requests.get(f"{CHATBOT_API}/conversations")
        data = response.json()

        assert response.status_code == 200, "Status code should be 200"
        assert data['success'] == True, "Should be successful"
        assert 'conversations' in data, "Should have conversations"

        print_success("Conversations listed successfully")
        print_info(f"Total conversations: {len(data['conversations'])}")

        return True
    except Exception as e:
        print_error(f"List conversations failed: {str(e)}")
        return False


def run_all_tests():
    """Run all chatbot tests"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Multi-modal AI Chatbot Test Suite{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{YELLOW}Testing against: {API_BASE_URL}{RESET}\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Health Check
    if test_health_check():
        tests_passed += 1
    else:
        tests_failed += 1
        print_error("Skipping remaining tests - health check failed")
        return

    # Test 2: Get Personas
    if test_get_personas():
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 3: Simple Chat
    conversation_id = test_simple_chat()
    if conversation_id:
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 4: Conversation Continuity
    if test_conversation_continuity(conversation_id):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 5: Persona Switching
    if test_persona_switching(conversation_id):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 6: Get History
    if test_get_history(conversation_id):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 7: Meter Analysis
    if test_meter_analysis():
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 8: List Conversations
    if test_list_conversations():
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 9: Clear Conversation
    if test_clear_conversation(conversation_id):
        tests_passed += 1
    else:
        tests_failed += 1

    # Summary
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{GREEN}Passed: {tests_passed}{RESET}")
    print(f"{RED}Failed: {tests_failed}{RESET}")
    print(f"{YELLOW}Total: {tests_passed + tests_failed}{RESET}")

    if tests_failed == 0:
        print(f"\n{GREEN}✓ All tests passed!{RESET}\n")
    else:
        print(f"\n{RED}✗ Some tests failed{RESET}\n")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Tests interrupted by user{RESET}\n")
    except Exception as e:
        print(f"\n{RED}Test suite error: {str(e)}{RESET}\n")
