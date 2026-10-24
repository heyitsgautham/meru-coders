#!/usr/bin/env python3
"""Test gTTS as a fallback"""
from gtts import gTTS
import os

def test_gtts():
    text = "अग्निना तूर्णं यद्वा परावतं उग्रादेवं हवामहे"
    output_file = "/tmp/test_gtts.mp3"
    
    print(f"Text: {text}")
    print(f"Output: {output_file}")
    
    try:
        tts = gTTS(text=text, lang='hi', slow=False)
        tts.save(output_file)
        
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"✅ Success! File created with size: {size} bytes")
            return True
        else:
            print("❌ File was not created")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gtts()
