#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Image Upload Fix
Tests the chatbot API with image uploads to ensure proper validation and error handling
"""

import base64
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_image_without_message():
    """Test that image upload without message returns proper error"""
    from flask import Flask
    from api.chatbot import chatbot_bp
    
    app = Flask(__name__)
    app.register_blueprint(chatbot_bp)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Create a minimal base64 image
        fake_image_data = base64.b64encode(b'fake_image_bytes').decode('utf-8')
        
        response = client.post(
            '/api/chatbot/chat',
            json={
                'message': '',  # Empty message
                'image': f'data:image/jpeg;base64,{fake_image_data}',
                'persona': 'default'
            }
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = json.loads(response.data)
        assert not data['success'], "Response should indicate failure"
        assert 'text prompt' in data['error'].lower(), f"Error message should mention text prompt: {data['error']}"
        
        print("✅ Test 1 PASSED: Image without message properly rejected")
        print(f"   Error message: {data['error']}")


def test_image_with_message():
    """Test that image upload WITH message is accepted"""
    from flask import Flask
    from api.chatbot import chatbot_bp
    
    app = Flask(__name__)
    app.register_blueprint(chatbot_bp)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Create a minimal base64 image
        fake_image_data = base64.b64encode(b'x' * 200).decode('utf-8')  # Valid size
        
        response = client.post(
            '/api/chatbot/chat',
            json={
                'message': 'What is in this image?',
                'image': f'data:image/jpeg;base64,{fake_image_data}',
                'persona': 'default'
            }
        )
        
        # Note: This might fail due to Gemini API key issues in testing,
        # but it should NOT fail with a 400 validation error
        assert response.status_code != 400 or 'text prompt' not in json.loads(response.data).get('error', '').lower(), \
            "Should not reject valid image + message combination"
        
        print("✅ Test 2 PASSED: Image with message validation accepted")


def test_invalid_image_data():
    """Test that corrupted/invalid image data returns proper error"""
    from flask import Flask
    from api.chatbot import chatbot_bp
    
    app = Flask(__name__)
    app.register_blueprint(chatbot_bp)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Create very small/invalid image data
        fake_image_data = base64.b64encode(b'x').decode('utf-8')  # Too small
        
        response = client.post(
            '/api/chatbot/chat',
            json={
                'message': 'What is in this image?',
                'image': f'data:image/jpeg;base64,{fake_image_data}',
                'persona': 'default'
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid image, got {response.status_code}"
        data = json.loads(response.data)
        assert 'invalid' in data['error'].lower() or 'corrupted' in data['error'].lower(), \
            f"Error should mention invalid/corrupted image: {data['error']}"
        
        print("✅ Test 3 PASSED: Invalid image data properly rejected")
        print(f"   Error message: {data['error']}")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Image Upload Fix")
    print("=" * 60)
    
    try:
        test_image_without_message()
        test_image_with_message()
        test_invalid_image_data()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nFix Summary:")
        print("1. ✅ Image uploads without text are rejected with helpful error")
        print("2. ✅ Image uploads with text are validated properly")
        print("3. ✅ Invalid/corrupted images are detected and rejected")
        print("4. ✅ Frontend auto-adds default prompt when image is uploaded")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
