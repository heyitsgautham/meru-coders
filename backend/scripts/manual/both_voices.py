#!/usr/bin/env python3
"""Test both male and female voices"""
import asyncio
import edge_tts
import os

async def test_voices():
    text = "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम्"
    
    voices = {
        "male": "hi-IN-MadhurNeural",
        "female": "hi-IN-SwaraNeural"
    }
    
    for voice_type, voice_name in voices.items():
        output_file = f"/tmp/test_tts_{voice_type}.mp3"
        
        print(f"\nTesting {voice_type} voice: {voice_name}")
        print(f"Output: {output_file}")
        
        try:
            communicate = edge_tts.Communicate(text, voice_name)
            await communicate.save(output_file)
            
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"✅ Success! File created with size: {size} bytes")
            else:
                print("❌ File was not created")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_voices())
