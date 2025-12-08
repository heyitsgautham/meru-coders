#!/usr/bin/env python3
"""
Test script to verify the Analyse Chanda link generation
"""

import os
import sys
import base64
import re

# Test the encoding/decoding directly
test_verse = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"

print("=" * 80)
print("Testing Analyse Chanda Link Encoding/Decoding")
print("=" * 80)
print(f"\nOriginal verse: {test_verse}\n")

# Encode
encoded_text = base64.b64encode(test_verse.encode('utf-8')).decode('ascii')
print(f"Encoded (base64): {encoded_text}")

# Create the markdown link
markdown_link = f'[**Analyse Chanda**](#analyze:{encoded_text})'
print(f"\nMarkdown link: {markdown_link}")

# Decode it back
try:
    decoded_bytes = base64.b64decode(encoded_text)
    decoded_text = decoded_bytes.decode('utf-8')
    print(f"\nDecoded text: {decoded_text}")
    
    if decoded_text == test_verse:
        print("\n✅ Encoding/decoding works correctly!")
    else:
        print(f"\n❌ Decoded text doesn't match original!")
        print(f"   Expected: {test_verse}")
        print(f"   Got: {decoded_text}")
except Exception as e:
    print(f"\n❌ Decoding failed: {e}")

# Test the frontend decoding logic
print("\n" + "=" * 80)
print("Testing Frontend Decoding Logic")
print("=" * 80)

# Simulate what the frontend does
href = f"#analyze:{encoded_text}"
if href.startswith('#analyze:'):
    encodedText = href.replace('#analyze:', '')
    try:
        # JavaScript atob equivalent in Python
        decodedText = base64.b64decode(encodedText).decode('utf-8')
        print(f"\nFrontend would decode to: {decodedText}")
        
        if decodedText == test_verse:
            print("✅ Frontend decoding logic is correct!")
        else:
            print("❌ Frontend decoding would fail!")
    except Exception as e:
        print(f"❌ Frontend decoding error: {e}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
