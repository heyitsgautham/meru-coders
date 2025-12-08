#!/usr/bin/env python3
"""
Quick test to verify chatbot formatting changes are live
"""

import requests
import json

API_URL = "http://localhost:5000/api/chatbot/chat"

# Test 1: Ask for chanda name only
print("=" * 70)
print("TEST 1: Ask for chanda name only")
print("=" * 70)

payload1 = {
    "message": "What is the chanda name of धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
    "persona": "default"
}

response1 = requests.post(API_URL, json=payload1)
if response1.status_code == 200:
    result = response1.json()
    print("\n✅ SUCCESS")
    print("\nResponse:")
    print(result['response'])
else:
    print(f"\n❌ ERROR: {response1.status_code}")
    print(response1.text)

print("\n" + "=" * 70)

# Test 2: Ask for LG pattern
print("TEST 2: Ask for LG pattern")
print("=" * 70)

payload2 = {
    "message": "Show me the LG pattern of धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
    "persona": "default"
}

response2 = requests.post(API_URL, json=payload2)
if response2.status_code == 200:
    result = response2.json()
    print("\n✅ SUCCESS")
    print("\nResponse:")
    print(result['response'])
else:
    print(f"\n❌ ERROR: {response2.status_code}")
    print(response2.text)

print("\n" + "=" * 70)

# Test 3: Full analysis
print("TEST 3: Full analysis")
print("=" * 70)

payload3 = {
    "message": "Analyze धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
    "persona": "default"
}

response3 = requests.post(API_URL, json=payload3)
if response3.status_code == 200:
    result = response3.json()
    print("\n✅ SUCCESS")
    print("\nResponse:")
    print(result['response'])
    
    # Check for key improvements
    print("\n" + "=" * 70)
    print("VERIFICATION:")
    print("=" * 70)
    response_text = result['response']
    
    checks = {
        "✓ Confidence label (not numeric score)": "Confidence:" in response_text and "[10.0]" not in response_text,
        "✓ Pada-split LG pattern": "by Pada" in response_text or "|" in response_text,
        "✓ Shows tip at end": "Use the **Analyse Chanda** page" in response_text,
        "✓ No 'Metrical Analysis' header": "Metrical Analysis" not in response_text,
        "✓ Clean meter display": "Chanda:" in response_text
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    if all(checks.values()):
        print("\n🎉 ALL FORMATTING IMPROVEMENTS ARE LIVE!")
    else:
        print("\n⚠️  Some formatting improvements may not be working")
    
else:
    print(f"\n❌ ERROR: {response3.status_code}")
    print(response3.text)

print("\n" + "=" * 70)
