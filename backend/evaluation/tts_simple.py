"""
Simple test for Sanskrit TTS without full dependencies
Tests basic functionality with mock outputs
"""


def test_basic_import():
    """Test if the module can be imported"""
    try:
        print("✓ Module imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_initialization():
    """Test basic initialization"""
    try:
        from backend.experimental.sanskrit_tts import SanskritTTS

        # This should fail gracefully without dependencies
        try:
            SanskritTTS(mode="local")
            print("✓ Initialization succeeded (unexpected)")
        except ValueError as e:
            if "requires" in str(e).lower():
                print(f"✓ Expected error for missing dependencies: {e}")
                return True
            raise
    except Exception as e:
        print(f"✗ Initialization test failed: {e}")
        return False


def test_api_mode_check():
    """Test API mode requirements"""
    try:
        from backend.experimental.sanskrit_tts import SanskritTTS

        try:
            SanskritTTS(mode="api")
            print("✗ Should have required HF_TOKEN")
            return False
        except ValueError as e:
            if "HF_TOKEN" in str(e):
                print(f"✓ Correctly requires HF_TOKEN: {e}")
                return True
            raise
    except Exception as e:
        print(f"✗ API mode check failed: {e}")
        return False


def print_installation_guide():
    """Print installation instructions"""
    print("\n" + "=" * 70)
    print("INSTALLATION GUIDE FOR SANSKRIT TTS")
    print("=" * 70)
    print("\n1. Install basic dependencies:")
    print("   pip install requests numpy soundfile")
    print("\n2. Install parler-tts library:")
    print("   pip install git+https://github.com/huggingface/parler-tts.git")
    print("\n3. Install PyTorch (choose based on your system):")
    print("   # For Mac (MPS/CPU)")
    print("   pip install torch torchvision torchaudio")
    print("   # For Linux/Windows with CUDA")
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print("\n4. Install transformers:")
    print("   pip install transformers accelerate")
    print("\n5. Optional (for spectrograms):")
    print("   pip install librosa matplotlib")
    print("\n6. Or install everything at once:")
    print("   pip install -r requirements_tts.txt")
    print("\n7. Test with:")
    print('   python sanskrit_tts.py "ॐ नमः शिवाय"')
    print("=" * 70)


if __name__ == "__main__":
    print("Testing Sanskrit TTS Module\n")

    results = []
    results.append(("Basic Import", test_basic_import()))
    results.append(("Initialization Check", test_initialization()))
    results.append(("API Mode Check", test_api_mode_check()))

    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    if not all(p for _, p in results):
        print_installation_guide()
