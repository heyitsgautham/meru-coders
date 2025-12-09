#!/usr/bin/env python3
"""Debug script to see what Gemini returns for invalid input."""

import sys
import json
import re
import os
sys.path.insert(0, '/home/harevasu/Projects/meru-coders/backend')

from dotenv import load_dotenv
load_dotenv('/home/harevasu/Projects/meru-coders/backend/.env')

from google import genai
from google.genai import types

# Get API keys from environment (same way ai_validator.py does it)
GEMINI_API_KEYS = [
    os.environ.get('GEMINI_API_KEY_1', ''),
    os.environ.get('GEMINI_API_KEY_2', ''),
    os.environ.get('GEMINI_API_KEY_3', ''),
    os.environ.get('GEMINI_API_KEY_4', ''),
    os.environ.get('GEMINI_API_KEY_5', ''),
    os.environ.get('GEMINI_API_KEY_6', ''),
]
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

# Get first API key
api_key = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else None
if not api_key:
    print("ERROR: No Gemini API key found!")
    sys.exit(1)

print(f"Using API key: {api_key[:10]}...")

# Create client
client = genai.Client(api_key=api_key)

# The prompt we use
PROMPT = """You are Aacharya Pingala, the ancient sage and author of Chandas Shastra. Analyze if the following text is a valid Sanskrit shloka or verse that can be analyzed for its meter (chandas).

Text to analyze:
---
pratap pratap
---

Return ONLY a JSON object with these fields:
{
  "is_valid_shloka": boolean,
  "confidence": float (0.0 to 1.0),
  "text_type": "verse" | "prose" | "fragment" | "non_sanskrit" | "gibberish",
  "reason": "brief explanation",
  "suggested_action": "proceed" | "reject" | "warn"
}

Mark is_valid_shloka=true for:
1. Complete Sanskrit verses with clear metrical structure
2. Single padas (quarter verses) that are metrically valid
3. Vedic mantras and hymns
4. Classical Sanskrit poetry (kavya)

Mark is_valid_shloka=false for:
1. Plain Sanskrit prose sentences
2. Random Devanagari characters without meaning
3. Non-Sanskrit text (Hindi, English, etc.)
4. Incomplete fragments that can't be analyzed
5. Mixed language content

Return ONLY the JSON object, no markdown formatting or explanation."""

print("\n" + "="*60)
print("Sending request to Gemini...")
print("="*60)

try:
    config = types.GenerateContentConfig(
        temperature=0.1,
        top_p=0.95,
        max_output_tokens=1024,  # Increased from 500!
    )
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=PROMPT,
        config=config
    )
    
    print("\n--- RAW RESPONSE ---")
    print(f"response.text exists: {hasattr(response, 'text')}")
    
    if response and response.text:
        raw_text = response.text
        print(f"Length: {len(raw_text)} chars")
        print(f"Content:\n{raw_text}")
        print("--- END RAW RESPONSE ---\n")
        
        # Try to parse
        response_text = raw_text.strip()
        if response_text.startswith('```'):
            response_text = re.sub(r'^```json?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            print(f"After removing markdown:\n{response_text}")
        
        try:
            result = json.loads(response_text)
            print(f"\n✓ JSON parsed successfully!")
            print(f"Result: {json.dumps(result, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"\n✗ JSON parse error: {e}")
            print(f"Error position: char {e.pos}")
            print(f"Around error: ...{response_text[max(0,e.pos-20):e.pos+20]}...")
    else:
        print("Response was empty or None!")
        print(f"Full response object: {response}")
        
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
