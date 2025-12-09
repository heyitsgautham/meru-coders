#!/usr/bin/env python3
"""Test pyttsx3 with different voices"""
import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

print(f"Found {len(voices)} voices:\n")
for i, voice in enumerate(voices):
    print(f"{i+1}. ID: {voice.id}")
    print(f"   Name: {voice.name}")
    print(f"   Languages: {voice.languages}")
    print(f"   Gender: {voice.gender}")
    print()

# Test with first 2 voices if available
text = "अग्निमीळे पुरोहितं यज्ञस्य"
for i in range(min(2, len(voices))):
    print(f"Testing voice {i+1}: {voices[i].name}")
    engine.setProperty('voice', voices[i].id)
    engine.save_to_file(text, f'/tmp/test_pyttsx3_voice_{i+1}.mp3')

engine.runAndWait()
print("\n✅ Audio files generated!")
