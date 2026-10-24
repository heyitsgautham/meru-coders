#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test Script

Quick test to verify all major features work correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app import create_app
from backend.config import settings
from backend.core import Chanda


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_data_files():
    """Test that all required data files exist."""
    print_section("Testing Data Files")

    required_files = [
        'chanda_sama.csv',
        'chanda_ardhasama.csv',
        'chanda_vishama.csv',
        'chanda_matra.csv',
        'chanda_jaati.csv',
        'examples.json',
    ]

    all_present = True
    for filename in required_files:
        filepath = settings.DATA_DIR / filename
        if filepath.exists():
            print(f"✓ {filename} - Found")
        else:
            print(f"✗ {filename} - Missing")
            all_present = False

    return all_present


def test_chanda_initialization():
    """Test Chanda class initialization."""
    print_section("Testing Chanda Initialization")

    try:
        chanda = Chanda(data_path=str(settings.DATA_DIR))
        print("✓ Chanda initialized successfully")
        print(f"  - Data path: {settings.DATA_DIR}")
        return True, chanda
    except Exception as e:
        print(f"✗ Chanda initialization failed: {e}")
        return False, None


def test_meter_identification(chanda):
    """Test meter identification with sample text."""
    print_section("Testing Meter Identification")

    test_cases = [
        {'name': 'Simple Line', 'text': 'श्रीरामचन्द्रचरणौ मनसा स्मरामि', 'mode': 'line'},
        {
            'name': 'Complete Verse',
            'text': '''श्रीरामचन्द्रचरणौ मनसा स्मरामि
श्रीरामचन्द्रचरणौ वचसा गृणामि
श्रीरामचन्द्रचरणौ शिरसा नमामि
श्रीरामचन्द्रचरणौ शरणं प्रपद्ये''',
            'mode': 'verse',
        },
    ]

    all_passed = True
    for test in test_cases:
        try:
            result = chanda.identify_from_text(test['text'], verse=(test['mode'] == 'verse'), fuzzy=True)

            if result and 'result' in result:
                print(f"✓ {test['name']} - Success")
                print(f"  - Found {len(result['result'])} results")
            else:
                print(f"✗ {test['name']} - No results")
                all_passed = False
        except Exception as e:
            print(f"✗ {test['name']} - Error: {e}")
            all_passed = False

    return all_passed


def test_flask_app():
    """Test Flask application creation."""
    print_section("Testing Flask Application")

    try:
        app = create_app()
        print("✓ Flask app created successfully")

        # Test with test client
        with app.test_client() as client:
            # Health check
            response = client.get('/health')
            if response.status_code == 200:
                print("✓ Health endpoint working")
            else:
                print(f"✗ Health endpoint failed: {response.status_code}")
                return False

            # API info
            response = client.get('/api/info')
            if response.status_code == 200:
                data = response.get_json()
                print("✓ API info endpoint working")
                print(f"  - Version: {data.get('version', 'unknown')}")
                print(f"  - Tesseract available: {data['ocr_available']['tesseract']}")
                print(f"  - Google OCR available: {data['ocr_available']['google']}")
            else:
                print(f"✗ API info failed: {response.status_code}")
                return False

            # Test text identification endpoint
            response = client.post(
                '/api/identify/text', json={'text': 'श्रीरामचन्द्रचरणौ मनसा स्मरामि', 'text_mode': 'line'}
            )
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    print("✓ Text identification endpoint working")
                else:
                    print(f"✗ Text identification failed: {data.get('error', 'unknown')}")
                    return False
            else:
                print(f"✗ Text identification endpoint failed: {response.status_code}")
                return False

            # Test examples endpoint
            response = client.get('/api/examples')
            if response.status_code == 200:
                data = response.get_json()
                print(f"✓ Examples endpoint working ({len(data.get('examples', []))} examples)")
            else:
                print(f"✗ Examples endpoint failed: {response.status_code}")
                return False

            # Test schemes endpoint
            response = client.get('/api/schemes')
            if response.status_code == 200:
                data = response.get_json()
                print(f"✓ Schemes endpoint working ({len(data.get('schemes', []))} schemes)")
            else:
                print(f"✗ Schemes endpoint failed: {response.status_code}")
                return False

        return True
    except Exception as e:
        print(f"✗ Flask app creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ocr_availability():
    """Test OCR module availability."""
    print_section("Testing OCR Availability")

    # Test Tesseract
    try:
        from backend.ocr import TesseractOCR

        tesseract = TesseractOCR(languages=settings.TESSERACT_LANGUAGES)
        print("✓ Tesseract OCR available")
    except Exception as e:
        print(f"⚠ Tesseract OCR not available: {e}")

    # Test Google OCR
    try:
        from backend.ocr import GoogleOCR

        if settings.CLIENT_SECRET:
            google_ocr = GoogleOCR(credentials_path=settings.CLIENT_SECRET)
            print("✓ Google OCR available")
        else:
            print("⚠ Google OCR credentials not configured")
    except Exception as e:
        print(f"⚠ Google OCR not available: {e}")

    return True


def test_frontend_files():
    """Test that frontend files exist."""
    print_section("Testing Frontend Files")

    frontend_dir = Path(__file__).resolve().parent.parent.parent / 'frontend'

    required_files = ['index.html', 'src/app.js']

    all_present = True
    for filepath in required_files:
        full_path = frontend_dir / filepath
        if full_path.exists():
            print(f"✓ {filepath} - Found")
        else:
            print(f"✗ {filepath} - Missing")
            all_present = False

    return all_present


def main():
    """Run all integration tests."""
    print("\n" + "🚀" * 35)
    print("  CHANDAS-INTEGRATED - Integration Test Suite")
    print("🚀" * 35)

    results = {}

    # Run all tests
    results['data_files'] = test_data_files()

    success, chanda = test_chanda_initialization()
    results['chanda_init'] = success

    if success and chanda:
        results['meter_identification'] = test_meter_identification(chanda)
    else:
        results['meter_identification'] = False

    results['flask_app'] = test_flask_app()
    results['ocr'] = test_ocr_availability()
    results['frontend'] = test_frontend_files()

    # Summary
    print_section("Test Summary")

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 ALL TESTS PASSED!")
        print("  Your Chandas-Integrated system is ready to use!")
        print()
        print("  To start the backend server:")
        print("    cd backend")
        print("    python run.py")
        print()
        print("  Then open frontend/index.html in your browser")
    else:
        print("  ⚠ SOME TESTS FAILED")
        print("  Please review the errors above and fix any issues.")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
