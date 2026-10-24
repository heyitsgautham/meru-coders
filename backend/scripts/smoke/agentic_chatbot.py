#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Tests for Agentic Chatbot with Meter Identification
Tests the automatic meter detection and analysis capabilities
"""


import requests
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

BASE_URL = "http://localhost:5000/api/chatbot"

def print_header(text):
    """Print a colored header"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}{text:^70}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

def print_success(text):
    """Print success message"""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text):
    """Print error message"""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_info(text):
    """Print info message"""
    print(f"{Fore.YELLOW}ℹ {text}{Style.RESET_ALL}")

def print_meter_data(meter_data):
    """Pretty print meter analysis data"""
    if not meter_data:
        return

    print(f"\n{Fore.MAGENTA}📊 Meter Analysis Data:{Style.RESET_ALL}")
    print(f"  Text: {Fore.CYAN}{meter_data.get('text', 'N/A')}{Style.RESET_ALL}")
    print(f"  Meter: {Fore.GREEN}{meter_data.get('meter', 'N/A')}{Style.RESET_ALL}")
    print(f"  L-G Pattern: {Fore.YELLOW}{meter_data.get('lg_pattern', 'N/A')}{Style.RESET_ALL}")
    print(f"  Gana Pattern: {Fore.YELLOW}{meter_data.get('gana_pattern', 'N/A')}{Style.RESET_ALL}")
    print(f"  Syllables: {meter_data.get('syllables', 0)}")
    print(f"  Matra: {meter_data.get('matra', 0)}")
    print(f"  Found: {Fore.GREEN if meter_data.get('found') else Fore.RED}{meter_data.get('found', False)}{Style.RESET_ALL}")

def test_agentic_detection_with_devanagari():
    """Test 1: Agentic detection with Devanagari text"""
    print_header("TEST 1: Agentic Detection with Devanagari Text")

    test_cases = [
        {
            "message": "Can you identify the meter of this verse: धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
            "expected_meter": "अनुष्टुभ्",
            "description": "Anushtubh meter (Bhagavad Gita)"
        },
        {
            "message": "What is the chandas of: वसुदेवसुतं देवं कंसचाणूरमर्दनम्",
            "expected_meter": "अनुष्टुभ्",
            "description": "Anushtubh meter (Krishna Ashtakam)"
        },
        {
            "message": "Find the meter: यदा यदा हि धर्मस्य ग्लानिर्भवति भारत",
            "expected_meter": "अनुष्टुभ्",
            "description": "Anushtubh meter (Bhagavad Gita 4.7)"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{Fore.BLUE}Test Case {i}: {test['description']}{Style.RESET_ALL}")
        print(f"Message: {test['message']}")

        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                json={
                    "message": test["message"],
                    "persona": "default"
                }
            )

            data = response.json()

            if data.get("success"):
                print_success("API call successful")

                # Check for agentic action
                if data.get("agentic_action") == "meter_identification":
                    print_success("Agentic meter identification triggered!")

                    meter_data = data.get("meter_data")
                    if meter_data:
                        print_meter_data(meter_data)

                        # Validate meter
                        if meter_data.get("meter") == test["expected_meter"]:
                            print_success(f"Correct meter identified: {test['expected_meter']}")
                        else:
                            print_error(f"Expected {test['expected_meter']}, got {meter_data.get('meter')}")
                    else:
                        print_error("No meter data in response")
                else:
                    print_error("Agentic action not triggered")
                    print_info(f"Response: {data.get('response', '')[:200]}...")
            else:
                print_error(f"API call failed: {data.get('error')}")

        except Exception as e:
            print_error(f"Exception: {str(e)}")

def test_agentic_detection_with_keywords():
    """Test 2: Various keyword triggers for agentic detection"""
    print_header("TEST 2: Keyword Trigger Detection")

    keywords = [
        "identify the chandas",
        "find the meter",
        "what is the L-G pattern",
        "analyze this verse",
        "detect the chanda",
        "scan this shloka",
        "what meter is this"
    ]

    sanskrit_text = "त्वमेव माता च पिता त्वमेव त्वमेव बन्धुश्च सखा त्वमेव"

    for keyword in keywords:
        print(f"\n{Fore.BLUE}Testing keyword: '{keyword}'{Style.RESET_ALL}")
        message = f"{keyword}: {sanskrit_text}"

        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                json={"message": message, "persona": "default"}
            )

            data = response.json()

            if data.get("agentic_action") == "meter_identification":
                print_success("Agentic action triggered")
            else:
                print_error("Agentic action NOT triggered")

        except Exception as e:
            print_error(f"Exception: {str(e)}")

def test_krishna_persona_agentic():
    """Test 3: Agentic detection with Krishna persona"""
    print_header("TEST 3: Agentic Detection with Krishna Persona")

    message = "O Krishna, please identify the meter of: कर्मण्येवाधिकारस्ते मा फलेषु कदाचन"

    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": message,
                "persona": "krishna"
            }
        )

        data = response.json()

        if data.get("success"):
            print_success("API call successful")
            print(f"\nPersona: {Fore.MAGENTA}{data.get('persona')}{Style.RESET_ALL}")

            if data.get("agentic_action") == "meter_identification":
                print_success("Agentic meter identification triggered with Krishna persona!")
                print_meter_data(data.get("meter_data"))

                # Check if response has Krishna's style
                response_text = data.get("response", "")
                if "🕉️" in response_text or "Arjuna" in response_text or "dear one" in response_text.lower():
                    print_success("Response has Krishna's divine style")

                print(f"\n{Fore.CYAN}Response Preview:{Style.RESET_ALL}")
                print(response_text[:300] + "...")
            else:
                print_error("Agentic action not triggered")
        else:
            print_error(f"API call failed: {data.get('error')}")

    except Exception as e:
        print_error(f"Exception: {str(e)}")

def test_conversation_context():
    """Test 4: Multi-turn conversation with agentic detection"""
    print_header("TEST 4: Multi-turn Conversation with Context")

    conversation_id = None

    # Turn 1: Ask about a meter
    print(f"\n{Fore.BLUE}Turn 1: Ask about a meter{Style.RESET_ALL}")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": "What is Anushtubh meter?",
                "persona": "default"
            }
        )
        data = response.json()
        conversation_id = data.get("conversation_id")
        print_success(f"Turn 1 successful. Conversation ID: {conversation_id}")

    except Exception as e:
        print_error(f"Turn 1 failed: {str(e)}")
        return

    # Turn 2: Ask to identify a verse
    print(f"\n{Fore.BLUE}Turn 2: Ask to identify a verse{Style.RESET_ALL}")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": "Can you identify this verse: राम राम महाबाहो शरण्ये त्वां प्रपद्यते",
                "conversation_id": conversation_id,
                "persona": "default"
            }
        )
        data = response.json()

        if data.get("agentic_action") == "meter_identification":
            print_success("Agentic action triggered in Turn 2")
            print_meter_data(data.get("meter_data"))
        else:
            print_error("Agentic action not triggered in Turn 2")

    except Exception as e:
        print_error(f"Turn 2 failed: {str(e)}")

    # Turn 3: Ask follow-up question
    print(f"\n{Fore.BLUE}Turn 3: Ask follow-up about the same meter{Style.RESET_ALL}")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": "Tell me more about the characteristics of this meter",
                "conversation_id": conversation_id,
                "persona": "default"
            }
        )
        data = response.json()

        if data.get("success"):
            print_success("Turn 3 successful")
            print(f"\n{Fore.CYAN}Response:{Style.RESET_ALL}")
            print(data.get("response", "")[:200] + "...")

    except Exception as e:
        print_error(f"Turn 3 failed: {str(e)}")

def test_edge_cases():
    """Test 5: Edge cases and error handling"""
    print_header("TEST 5: Edge Cases and Error Handling")

    test_cases = [
        {
            "message": "identify the meter",  # No Sanskrit text
            "description": "Request without Sanskrit text"
        },
        {
            "message": "find pattern in: random english text here",  # English text
            "description": "Request with English instead of Sanskrit"
        },
        {
            "message": "what is the chandas of: अ",  # Single character
            "description": "Single character Sanskrit"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{Fore.BLUE}Edge Case {i}: {test['description']}{Style.RESET_ALL}")

        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                json={
                    "message": test["message"],
                    "persona": "default"
                }
            )

            data = response.json()

            if data.get("success"):
                print_success("API handled gracefully")

                if data.get("agentic_action"):
                    print_info(f"Agentic action: {data.get('agentic_action')}")
                    meter_data = data.get("meter_data")
                    if meter_data:
                        print_info(f"Meter found: {meter_data.get('found')}")
                else:
                    print_info("Regular AI response (no agentic action)")
            else:
                print_error(f"API returned error: {data.get('error')}")

        except Exception as e:
            print_error(f"Exception: {str(e)}")

def test_confidence_scores():
    """Test 6: Confidence scores for agentic responses"""
    print_header("TEST 6: Confidence Scores")

    message = "Identify the meter: ओं भूर्भुवः स्वः तत्सवितुर्वरेण्यम्"

    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": message,
                "persona": "default"
            }
        )

        data = response.json()

        if data.get("success"):
            confidence = data.get("confidence", 0)
            print(f"Confidence Score: {Fore.GREEN}{confidence * 100:.1f}%{Style.RESET_ALL}")

            if data.get("agentic_action"):
                meter_data = data.get("meter_data")
                if meter_data and meter_data.get("found"):
                    if confidence >= 0.9:
                        print_success("High confidence (≥90%)")
                    elif confidence >= 0.7:
                        print_success("Good confidence (≥70%)")
                    else:
                        print_info("Lower confidence (<70%)")

    except Exception as e:
        print_error(f"Exception: {str(e)}")

def main():
    """Run all tests"""
    print_header("AGENTIC CHATBOT COMPREHENSIVE TEST SUITE")
    print(f"{Fore.YELLOW}Testing endpoint: {BASE_URL}{Style.RESET_ALL}")

    # Check health first
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_success("Backend is healthy")
        else:
            print_error("Backend health check failed")
            return
    except Exception as e:
        print_error(f"Cannot connect to backend: {str(e)}")
        print_info("Please ensure the backend is running: cd backend && python run.py")
        return

    # Run all tests
    test_agentic_detection_with_devanagari()
    test_agentic_detection_with_keywords()
    test_krishna_persona_agentic()
    test_conversation_context()
    test_edge_cases()
    test_confidence_scores()

    print_header("ALL TESTS COMPLETED")
    print(f"\n{Fore.GREEN}✨ Agentic Chatbot Testing Complete! ✨{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main()
