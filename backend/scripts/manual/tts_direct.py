#!/usr/bin/env python3
"""
Direct test for TTS functionality
"""

import json

import requests


# Test the TTS endpoint
def test_tts():
    url = "http://localhost:5000/api/tts/generate"

    payload = {"text": "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः", "voice": "male"}

    print("🧪 Testing TTS generation...")
    print(f"📝 Text: {payload['text']}")
    print(f"🎤 Voice: {payload['voice']}")
    print()

    try:
        response = requests.post(url, json=payload)
        print(f"📡 Status Code: {response.status_code}")
        print("📦 Response:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("\n✅ TTS generation successful!")
                print(f"🔊 Audio URL: {data.get('audio_url')}")
                print(f"📄 Filename: {data.get('filename')}")

                # Try to access the audio file
                audio_url = f"http://localhost:5000{data.get('audio_url')}"
                print(f"\n🌐 Full URL: {audio_url}")

                audio_response = requests.get(audio_url)
                print(f"📥 Audio fetch status: {audio_response.status_code}")
                print(f"📊 Audio size: {len(audio_response.content)} bytes")

                if len(audio_response.content) > 0:
                    print("\n✅ Audio file is valid and has content!")
                else:
                    print("\n❌ Audio file is empty!")
            else:
                print("\n❌ TTS generation failed!")
                print(f"Error: {data.get('error')}")
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_tts()
