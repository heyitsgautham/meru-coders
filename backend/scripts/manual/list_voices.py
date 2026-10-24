#!/usr/bin/env python3
"""List available Hindi/Sanskrit voices in edge-tts"""
import asyncio

import edge_tts


async def list_hindi_voices():
    voices = await edge_tts.list_voices()

    print(f"Total voices found: {len(voices)}\n")
    print("Available Hindi/Indian voices:\n")

    # Debug: print first voice structure
    if voices:
        print("Sample voice structure:", voices[0].keys())
        print()

    hindi_voices = [v for v in voices if 'hi-IN' in v.get('Locale', '')]

    if not hindi_voices:
        print("No hi-IN voices found. Checking all Asian voices...")
        hindi_voices = [v for v in voices if any(x in v.get('Locale', '') for x in ['hi-', 'mr-', 'ta-', 'te-', 'kn-', 'gu-', 'bn-', 'pa-'])]

    for voice in hindi_voices:
        print(f"Name: {voice.get('ShortName', 'N/A')}")
        print(f"  Locale: {voice.get('Locale', 'N/A')}")
        print(f"  Gender: {voice.get('Gender', 'N/A')}")
        print()

if __name__ == "__main__":
    asyncio.run(list_hindi_voices())
