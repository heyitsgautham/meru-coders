#!/usr/bin/env python3
"""Test TTS API with male and female voices"""
import json

import requests

api_url = "http://localhost:5000/api/tts/generate"
text = "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम्"

# Test male voice
print("Testing MALE voice...")
response = requests.post(api_url, json={"text": text, "voice": "male"})
print(f"Status: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2))

if result.get('success'):
    print("\n✅ Male voice SUCCESS!")
    print(f"   Audio URL: {result['audio_url']}")
else:
    print(f"\n❌ Male voice FAILED: {result.get('error')}")

print("\n" + "="*60 + "\n")

# Test female voice
print("Testing FEMALE voice...")
response = requests.post(api_url, json={"text": text, "voice": "female"})
print(f"Status: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2))

if result.get('success'):
    print("\n✅ Female voice SUCCESS!")
    print(f"   Audio URL: {result['audio_url']}")
else:
    print(f"\n❌ Female voice FAILED: {result.get('error')}")
