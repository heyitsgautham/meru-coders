#!/usr/bin/env python3
"""Test edge-tts directly"""
import asyncio
import edge_tts
import os

async def test_tts():
    text = "अग्निना तूर्णं यद्वा परावतं उग्रादेवं हवामहे"
    voice = "hi-IN-SwaraNeural"
    output_file = "/tmp/test_edge_tts.mp3"
    
    print(f"Text: {text}")
    print(f"Voice: {voice}")
    print(f"Output: {output_file}")
    
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"✅ Success! File created with size: {size} bytes")
        else:
            print("❌ File was not created")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tts())
