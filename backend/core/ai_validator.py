"""
AI-Powered Shloka Validator using Google Gemini

This module provides an additional validation layer to check if input text
is a valid Sanskrit shloka/verse before passing it to the rule-based
meter identification engine.

Purpose:
- Prevent the rule-based model from predicting invalid chandas on non-verse text
- Detect prose, random text, mixed content that passes basic validation
- Provide early filtering before expensive meter pattern matching

Last Updated: 2025-12-09 - Updated to new google-genai SDK
"""

import os
import re
import json
import logging
from typing import Tuple, Dict, Any, Optional
from functools import lru_cache
import random

# Try to import Google GenAI (new SDK)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None

from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API keys for load balancing (same as chatbot.py)
GEMINI_API_KEYS = [
    os.getenv('GEMINI_API_KEY_1'),
    os.getenv('GEMINI_API_KEY_2'),
    os.getenv('GEMINI_API_KEY_3'),
    os.getenv('GEMINI_API_KEY_4'),
    os.getenv('GEMINI_API_KEY_5'),
    os.getenv('GEMINI_API_KEY_6'),
]
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

# Validation prompt for Gemini
SHLOKA_VALIDATION_PROMPT = """You are an expert in Sanskrit prosody (Chandas Shastra). 
Analyze the following text and determine if it is a valid Sanskrit verse (shloka/padya) suitable for chandas/meter identification.

Text to analyze:
```
{text}
```

Respond with a JSON object (and NOTHING else) with these fields:
{{
    "is_valid_shloka": true/false,
    "confidence": 0.0 to 1.0,
    "text_type": "verse" | "prose" | "mixed" | "non_sanskrit" | "gibberish" | "fragment",
    "reason": "Brief explanation in English",
    "suggested_action": "proceed" | "reject" | "warn"
}}

Classification criteria:
- "verse": Valid Sanskrit poetry with metrical structure (shloka, stotra, sutra with meter)
- "prose": Sanskrit prose (gadya) - grammatically correct but no metrical structure
- "mixed": Contains both verse and prose elements
- "non_sanskrit": Text in other languages (Hindi sentences, English, etc.)
- "gibberish": Random characters, keyboard mashing, meaningless text
- "fragment": Incomplete verse or partial pada

Only mark is_valid_shloka=true for:
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


def _rule_based_validation(text: str) -> Dict[str, Any]:
    """
    Fallback rule-based validation when AI is unavailable.
    Uses the same logic as chanda.py's is_valid_sanskrit_input.
    
    Args:
        text: Input text to validate
        
    Returns:
        Validation result dictionary
    """
    import re
    
    if not text or not text.strip():
        return {
            'is_valid': False,
            'confidence': 1.0,
            'text_type': 'gibberish',
            'reason': 'Empty input',
            'action': 'reject',
            'ai_validated': False
        }
    
    text = text.strip()
    
    # Common English words to reject
    COMMON_ENGLISH_WORDS = {
        'i', 'me', 'my', 'you', 'your', 'he', 'she', 'it', 'we', 'they', 'them',
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'am',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'hello', 'hi', 'hey', 'bye', 'goodbye', 'thanks', 'thank', 'please',
        'yes', 'no', 'ok', 'okay', 'sorry', 'welcome', 'good', 'bad', 'new', 'old',
        'test', 'testing', 'sample', 'example', 'demo', 'input', 'output',
        'aditya', 'rahul', 'priya', 'kumar', 'sharma', 'singh',  # Common names
        'pratap', 'vijay', 'ajay', 'sanjay', 'amit', 'sumit', 'rohit', 'mohit',  # More names
        'ram', 'shyam', 'gopal', 'krishna', 'ganesh', 'shiva', 'vishnu',  # Religious names (without diacritics = English)
        'name', 'word', 'text', 'data', 'file', 'code', 'type', 'value',  # Tech words
    }
    
    # Check for Devanagari characters
    devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    
    # Check for IAST diacritics
    iast_diacritics = set('āīūṛṝḷḹṃḥñṅṭḍṇśṣĀĪŪṚṜḶḸṂḤÑṄṬḌṆŚṢ')
    iast_chars = sum(1 for c in text if c in iast_diacritics)
    
    # If text has Devanagari, it's likely valid
    if devanagari_chars > 0:
        devanagari_ratio = devanagari_chars / len(text)
        if devanagari_ratio > 0.3:
            return {
                'is_valid': True,
                'confidence': 0.8,
                'text_type': 'verse',
                'reason': 'Devanagari script detected',
                'action': 'proceed',
                'ai_validated': False
            }
    
    # Pure ASCII without IAST diacritics - likely English
    if iast_chars == 0:
        text_lower = text.lower()
        words = re.findall(r'[a-z]+', text_lower)
        
        if words:
            english_word_count = sum(1 for word in words if word in COMMON_ENGLISH_WORDS)
            
            # If ANY common English word is found without diacritics, reject
            if english_word_count >= 1:
                return {
                    'is_valid': False,
                    'confidence': 0.9,
                    'text_type': 'non_sanskrit',
                    'reason': f'English text detected (no IAST diacritics). Found: {", ".join(w for w in words if w in COMMON_ENGLISH_WORDS)[:3]}',
                    'action': 'reject',
                    'ai_validated': False
                }
            
            # Check vowel ratio (Sanskrit has ~0.3-0.5)
            latin_chars = sum(1 for c in text if c.isalpha() and c.isascii())
            latin_vowels = sum(1 for c in text if c.lower() in 'aeiou')
            
            if latin_chars > 0:
                vowel_ratio = latin_vowels / latin_chars
                if vowel_ratio < 0.15:
                    return {
                        'is_valid': False,
                        'confidence': 0.8,
                        'text_type': 'gibberish',
                        'reason': 'Invalid text - vowel ratio too low',
                        'action': 'reject',
                        'ai_validated': False
                    }
    
    # Has IAST diacritics - likely valid romanized Sanskrit
    if iast_chars > 0:
        return {
            'is_valid': True,
            'confidence': 0.7,
            'text_type': 'verse',
            'reason': 'IAST transliteration detected',
            'action': 'proceed',
            'ai_validated': False
        }
    
    # CRITICAL: If we reach here, text has:
    # - No Devanagari (or very little)
    # - No IAST diacritics
    # - No common English words detected
    # This is likely gibberish or romanized text without proper diacritics
    # Valid Sanskrit MUST have either Devanagari OR IAST diacritics
    
    # Check if it's pure ASCII letters (no numbers, no special chars)
    ascii_letters = sum(1 for c in text if c.isalpha() and c.isascii())
    total_alpha = sum(1 for c in text if c.isalpha())
    
    if ascii_letters > 0 and total_alpha > 0:
        # If mostly ASCII letters with no Devanagari/IAST, reject
        if ascii_letters / total_alpha > 0.8:
            return {
                'is_valid': False,
                'confidence': 0.85,
                'text_type': 'non_sanskrit',
                'reason': 'Plain ASCII text without Sanskrit script or IAST diacritics',
                'action': 'reject',
                'ai_validated': False
            }
    
    # Default: uncertain, but proceed with warning (shouldn't reach here often)
    return {
        'is_valid': True,
        'confidence': 0.3,
        'text_type': 'unknown',
        'reason': 'Uncertain input - proceeding with caution',
        'action': 'warn',
        'ai_validated': False
    }


class AIShlokaValidator:
    """
    AI-powered validator to check if input text is a valid Sanskrit shloka
    before passing to the rule-based meter identification engine.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the AI validator.
        
        Args:
            enabled: Whether AI validation is enabled. If False, all inputs pass.
        """
        self.enabled = enabled and GENAI_AVAILABLE and len(GEMINI_API_KEYS) > 0
        self._client = None
        
        if not GENAI_AVAILABLE:
            logger.warning("google-genai not installed. AI validation disabled.")
        elif not GEMINI_API_KEYS:
            logger.warning("No Gemini API keys found. AI validation disabled.")
        else:
            logger.info(f"AI Shloka Validator initialized with {len(GEMINI_API_KEYS)} API keys")
    
    def _get_client(self):
        """Get a configured Gemini client with load-balanced API key."""
        if not self.enabled:
            return None
        
        # Select random API key for load balancing
        api_key = random.choice(GEMINI_API_KEYS)
        
        # Create client with the new SDK
        return genai.Client(api_key=api_key)
    
    def validate_shloka(self, text: str) -> Dict[str, Any]:
        """
        Validate if the input text is a valid Sanskrit shloka.
        
        Args:
            text: The input text to validate
            
        Returns:
            Dictionary with validation results:
            {
                'is_valid': bool,
                'confidence': float (0.0-1.0),
                'text_type': str,
                'reason': str,
                'action': str ('proceed', 'reject', 'warn'),
                'ai_validated': bool (True if AI was used, False if skipped)
            }
        """
        # Fallback result uses rule-based validation when AI is unavailable
        def get_fallback_result():
            return _rule_based_validation(text)
        
        if not self.enabled:
            logger.debug("AI validation disabled, using rule-based fallback")
            return get_fallback_result()
        
        if not text or not text.strip():
            return {
                'is_valid': False,
                'confidence': 1.0,
                'text_type': 'gibberish',
                'reason': 'Empty input',
                'action': 'reject',
                'ai_validated': True
            }
        
        # Skip AI for very long texts (batch mode efficiency)
        # AI validation is designed for single verse/line analysis
        if len(text) > 2000:
            logger.debug(f"Text too long ({len(text)} chars), using rule-based fallback")
            return get_fallback_result()
        
        try:
            client = self._get_client()
            if not client:
                logger.debug("No Gemini client available, using rule-based fallback")
                return get_fallback_result()
            
            # Generate validation prompt
            prompt = SHLOKA_VALIDATION_PROMPT.format(text=text)
            
            # Configure generation settings
            config = types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for consistent classification
                top_p=0.95,
                max_output_tokens=1024,  # Increased from 500 - Gemini uses ~500 tokens for "thinking"
            )
            
            # Call Gemini using new SDK
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config
            )
            
            # Handle response - check if text exists
            if not response or not response.text:
                logger.warning("Gemini returned empty response, using rule-based fallback")
                return get_fallback_result()
                
            response_text = response.text.strip()
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = re.sub(r'^```json?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
            
            # Debug: Log raw response for troubleshooting
            logger.debug(f"Gemini raw response: {response_text[:500]}")
            
            result = json.loads(response_text)
            
            return {
                'is_valid': result.get('is_valid_shloka', True),
                'confidence': result.get('confidence', 0.5),
                'text_type': result.get('text_type', 'unknown'),
                'reason': result.get('reason', 'AI analysis complete'),
                'action': result.get('suggested_action', 'proceed'),
                'ai_validated': True
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            logger.warning(f"Raw response was: {response_text[:300] if 'response_text' in dir() else 'N/A'}")
            # If JSON parsing fails, use rule-based validation as fallback
            return get_fallback_result()
            
        except Exception as e:
            logger.error(f"AI validation error: {e}, using rule-based fallback")
            # On any error, fall back to rule-based validation
            return get_fallback_result()
    
    def should_proceed_with_identification(self, validation_result: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Determine if meter identification should proceed based on validation result.
        
        Args:
            validation_result: Result from validate_shloka()
            
        Returns:
            Tuple of (should_proceed: bool, rejection_reason: Optional[str])
        """
        action = validation_result.get('action', 'proceed')
        
        if action == 'reject':
            reason = validation_result.get('reason', 'Invalid input')
            
            # Use consistent format matching chanda.py prose_message format
            # This ensures UI displays errors consistently
            rejection_msg = f"अमान्य आदान: {reason} (Invalid input: {reason})"
            
            return False, rejection_msg
        
        # 'proceed' or 'warn' - allow identification to continue
        return True, None


# Global singleton instance
_validator_instance: Optional[AIShlokaValidator] = None


def get_validator(enabled: bool = True) -> AIShlokaValidator:
    """
    Get the global AI validator instance.
    
    Args:
        enabled: Whether to enable AI validation
        
    Returns:
        AIShlokaValidator instance
    """
    global _validator_instance
    
    if _validator_instance is None:
        _validator_instance = AIShlokaValidator(enabled=enabled)
    
    return _validator_instance


def validate_shloka_input(text: str, skip_ai: bool = False) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Convenience function to validate shloka input.
    
    Args:
        text: Input text to validate
        skip_ai: If True, skip AI validation (for batch mode)
        
    Returns:
        Tuple of (should_proceed, rejection_reason, full_validation_result)
    """
    if skip_ai:
        return True, None, {'ai_validated': False, 'is_valid': True, 'action': 'proceed'}
    
    validator = get_validator()
    result = validator.validate_shloka(text)
    should_proceed, rejection_reason = validator.should_proceed_with_identification(result)
    
    return should_proceed, rejection_reason, result
