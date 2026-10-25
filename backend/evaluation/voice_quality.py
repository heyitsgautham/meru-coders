#!/usr/bin/env python3
"""
Test voice quality of Sanskrit TTS
This script helps you test the TTS system and hear sample outputs
"""

import importlib.util
import sys
from pathlib import Path


def check_dependencies():
    """Names of the required packages that are not installed."""
    required = ("torch", "parler_tts", "transformers", "soundfile")
    return [name for name in required if importlib.util.find_spec(name) is None]


def show_installation_guide():
    """Show quick installation guide"""
    print("\n" + "=" * 70)
    print("QUICK INSTALLATION")
    print("=" * 70)
    print("\nRun these commands to install dependencies:\n")
    print("# Option 1: Use the installation script")
    print("bash backend/scripts/install_tts.sh\n")
    print("# Option 2: Manual installation")
    print("pip install torch torchvision torchaudio")
    print("pip install transformers accelerate soundfile")
    print("pip install git+https://github.com/huggingface/parler-tts.git\n")
    print("=" * 70)


def generate_test_samples():
    """Generate test audio samples to evaluate voice quality"""
    from backend.experimental.sanskrit_tts import SanskritTTS

    print("\n" + "=" * 70)
    print("GENERATING SANSKRIT TTS TEST SAMPLES")
    print("=" * 70)
    print("\nModel: ai4bharat/indic-parler-tts")
    print("Speaker: Aryan (optimized for Sanskrit)")
    print("Expected quality: 99.79% accuracy\n")

    # Initialize TTS
    print("Initializing TTS system...")
    tts = SanskritTTS()

    # Test samples with different characteristics
    test_samples = [
        {
            "name": "Basic Mantra",
            "text": "ॐ नमः शिवाय",
            "description": "Short sacred mantra - tests clarity and pronunciation",
        },
        {
            "name": "Gayatri Mantra (excerpt)",
            "text": "ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यम्",
            "description": "Vedic mantra - tests prosody and rhythm",
        },
        {
            "name": "Bhagavad Gita Verse",
            "text": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन",
            "description": "Classical shloka - tests longer phrases",
        },
        {
            "name": "Simple Sentence",
            "text": "संस्कृतम् एकः प्राचीनः भाषा अस्ति",
            "description": "Prose sentence - tests natural speech",
        },
        {"name": "Greeting", "text": "नमस्ते भारत", "description": "Simple greeting - tests basic clarity"},
    ]

    results = []
    output_dir = Path("./test_outputs")
    output_dir.mkdir(exist_ok=True)

    print(f"\nGenerating {len(test_samples)} test samples...\n")

    for i, sample in enumerate(test_samples, 1):
        print(f"[{i}/{len(test_samples)}] {sample['name']}")
        print(f"   Text: {sample['text']}")
        print(f"   Testing: {sample['description']}")

        try:
            result = tts.synthesize(
                sample['text'],
                output_filename=f"test_{i}_{sample['name'].lower().replace(' ', '_')}",
                generate_spectrogram=True,
            )
            results.append(
                {
                    "name": sample['name'],
                    "text": sample['text'],
                    "audio": result['audio'],
                    "spectrogram": result['spectrogram'],
                    "success": True,
                }
            )
            print(f"   ✓ Generated: {result['audio'].name}")
            if result['spectrogram']:
                print(f"   ✓ Spectrogram: {result['spectrogram'].name}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            results.append({"name": sample['name'], "text": sample['text'], "success": False, "error": str(e)})

        print()

    return results


def print_results(results):
    """Print summary of generated samples"""
    print("=" * 70)
    print("TEST RESULTS")
    print("=" * 70)

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    print(f"\n✓ Successfully generated: {len(successful)}/{len(results)} samples\n")

    if successful:
        print("Generated Audio Files:")
        print("-" * 70)
        for result in successful:
            print(f"\n{result['name']}")
            print(f"  Text: {result['text']}")
            print(f"  Audio: {result['audio']}")
            if result.get('spectrogram'):
                print(f"  Spectrogram: {result['spectrogram']}")

    if failed:
        print("\n\nFailed Samples:")
        print("-" * 70)
        for result in failed:
            print(f"\n{result['name']}: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 70)
    print("HOW TO LISTEN")
    print("=" * 70)
    print("\n1. Find the audio files in the ./outputs/ directory")
    print("2. Play them with any audio player:")
    print("   - macOS: open outputs/test_*.wav")
    print("   - Linux: aplay outputs/test_*.wav")
    print("   - Windows: start outputs/test_*.wav")
    print("\n3. Compare voice quality:")
    print("   - Clarity of pronunciation")
    print("   - Natural rhythm and prosody")
    print("   - Accuracy of Sanskrit sounds")
    print("   - Overall naturalness")
    print("\n4. View spectrograms to see acoustic patterns")
    print("=" * 70)


def main():
    """Main function"""
    print("Sanskrit TTS Voice Quality Test")
    print("=" * 70)

    # Check dependencies
    print("\nChecking dependencies...")
    missing = check_dependencies()

    if missing:
        print(f"\n✗ Missing dependencies: {', '.join(missing)}")
        show_installation_guide()

        response = input("\nWould you like to see sample info without generating? [y/N]: ")
        if response.lower() == 'y':
            print("\n" + "=" * 70)
            print("MODEL INFORMATION")
            print("=" * 70)
            print("\nModel: ai4bharat/indic-parler-tts")
            print("Accuracy for Sanskrit: 99.79% (native speaker evaluation)")
            print("Speaker: Aryan (recommended for Sanskrit)")
            print("Sample Rate: 24kHz")
            print("Quality: High-fidelity, studio quality")
            print("\nTo hear actual samples, install dependencies and run again.")
            print("=" * 70)

        return 1

    print("✓ All dependencies installed")

    # Generate samples
    try:
        results = generate_test_samples()
        print_results(results)

        # Offer to play first sample
        successful = [r for r in results if r.get('success')]
        if successful and sys.platform == 'darwin':  # macOS
            response = input("\nWould you like to play the first sample now? [y/N]: ")
            if response.lower() == 'y':
                import subprocess

                audio_file = successful[0]['audio']
                subprocess.run(['open', str(audio_file)])
                print(f"Playing: {audio_file}")

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
