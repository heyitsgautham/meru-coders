#!/usr/bin/env python3
"""Test Google Cloud TTS with male and female voices"""

import os

from google.cloud import texttospeech


def test_google_tts():
    text = "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम्"

    try:
        client = texttospeech.TextToSpeechClient()

        voice_configs = {
            "male": {
                "language_code": "hi-IN",
                "name": "hi-IN-Wavenet-B",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE,
            },
            "female": {
                "language_code": "hi-IN",
                "name": "hi-IN-Wavenet-A",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE,
            },
        }

        for voice_type, voice_config in voice_configs.items():
            print(f"\nTesting {voice_type} voice: {voice_config['name']}")

            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config["language_code"],
                name=voice_config["name"],
                ssml_gender=voice_config["ssml_gender"],
            )
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

            output_file = f"/tmp/test_google_tts_{voice_type}.mp3"
            with open(output_file, 'wb') as out:
                out.write(response.audio_content)

            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"✅ Success! File: {output_file} ({size} bytes)")
            else:
                print("❌ File was not created")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_google_tts()
