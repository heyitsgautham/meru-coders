#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM-based Chanda Prediction Test Script

This script uses Google's Gemini API to predict Sanskrit meter (Chanda) names
from verses and compares the predictions against expected results.

Tests the hypothesis: Can an LLM correctly identify Sanskrit prosodic meters?

Usage:
    python tests/test_llm_chanda_prediction.py           # Run with default settings
    python tests/test_llm_chanda_prediction.py -n 20    # Test 20 verses
    python tests/test_llm_chanda_prediction.py -v       # Verbose mode
    python tests/test_llm_chanda_prediction.py --all    # Test all verses in dataset
"""

import csv
import os
import sys
import time
import json
import unicodedata
import argparse
import random
from typing import Optional, List, Dict, Tuple

# Load environment variables from .env file manually (handles non-standard format)
def load_api_keys_from_env():
    """Load API keys from .env file with custom parsing for non-standard format."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    keys = []
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('GEMINI_API_KEY_'):
                    # Parse: GEMINI_API_KEY_1='value'// comment
                    # or: GEMINI_API_KEY_1='value' // comment
                    if '=' in line:
                        key_part = line.split('=', 1)[1]
                        # Remove comments (// ...)
                        if '//' in key_part:
                            key_part = key_part.split('//')[0]
                        # Clean up quotes and whitespace
                        key_part = key_part.strip().strip("'").strip('"').strip()
                        if key_part:
                            keys.append(key_part)
    return keys

# Gemini API setup - using new google-genai SDK
from google import genai
from google.genai import types

# API key rotation for rate limiting
API_KEYS = load_api_keys_from_env()

current_api_key_index = 0
exhausted_keys = set()  # Track which keys are exhausted


def get_next_api_key():
    """Rotate through API keys to avoid rate limiting."""
    global current_api_key_index
    if not API_KEYS:
        raise ValueError("No Gemini API keys found in .env file!")
    
    # Check if all keys are exhausted
    if len(exhausted_keys) >= len(API_KEYS):
        raise ValueError("🚨 All API keys are exhausted! Please wait or add more keys.")
    
    # Find next non-exhausted key
    attempts = 0
    while attempts < len(API_KEYS):
        key = API_KEYS[current_api_key_index]
        key_index = current_api_key_index
        current_api_key_index = (current_api_key_index + 1) % len(API_KEYS)
        
        if key_index not in exhausted_keys:
            return key, key_index
        attempts += 1
    
    raise ValueError("🚨 All API keys are exhausted! Please wait or add more keys.")


def mark_key_exhausted(key_index: int):
    """Mark an API key as exhausted."""
    exhausted_keys.add(key_index)
    remaining = len(API_KEYS) - len(exhausted_keys)
    print(f"  ⚠️ API key #{key_index + 1} exhausted. {remaining} keys remaining.")


# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


def to_iast(text: str) -> str:
    """Convert Devanagari to IAST."""
    try:
        return transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
    except:
        return text


def normalize(name: str) -> str:
    """Normalize meter name for comparison."""
    if not name:
        return ""
    name = name.lower().strip()
    name = to_iast(name)
    name = unicodedata.normalize('NFD', name)
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))
    # Remove common suffixes and variations
    for suffix in ['m', 'h', 'am', 'a', 'ā']:
        if name.endswith(suffix) and len(name) > len(suffix) + 2:
            name = name[:-len(suffix)]
            break
    return name.strip()


# Meter family mappings for flexible matching
METER_FAMILIES = {
    # Anuṣṭup family
    'anustup': 'anustubh', 'anustubh': 'anustubh', 'sloka': 'anustubh',
    
    # Śārdūlavikrīḍita family
    'sardulavkridita': 'sardula', 'sardulavikriditam': 'sardula',
    'sardulavikridita': 'sardula', 'sardula': 'sardula',
    'shardulavikridita': 'sardula', 'saardulavikriidita': 'sardula',
    
    # Mandākrāntā family
    'mandakranta': 'mandakranta', 'mandaakraantaa': 'mandakranta',
    
    # Vasantatilakā family
    'vasantatilaka': 'vasantatilaka', 'vasantatilakam': 'vasantatilaka',
    
    # Bhujangaprayāta family
    'bhujangaprayata': 'bhujangaprayata', 'bhujangaprayatam': 'bhujangaprayata',
    
    # Upajāti family
    'upajati': 'upajati', 'upajatih': 'upajati',
    'indravajra': 'upajati', 'upendravajra': 'upajati',
    
    # Drutavilaṃbita family
    'drutavilambita': 'drutavilambita', 'drutavilambitam': 'drutavilambita',
    
    # Sragdharā family
    'sragdhara': 'sragdhara', 'sragdharaa': 'sragdhara',
    
    # Śikhariṇī family
    'sikharini': 'sikharini', 'sikharina': 'sikharini',
    
    # Mālinī family
    'malini': 'malini', 'maalini': 'malini',
}


def get_family(name: str) -> str:
    """Get the meter family for flexible matching."""
    normalized = normalize(name)
    return METER_FAMILIES.get(normalized, normalized)


def create_gemini_client():
    """Create and configure a Gemini client instance."""
    api_key, key_index = get_next_api_key()
    
    # Create client with new SDK
    client = genai.Client(api_key=api_key)
    return client, key_index


def predict_chanda_with_llm(verse: str, client, key_index: int, max_retries: int = 3) -> Optional[str]:
    """
    Use Gemini LLM to predict the Chanda (meter) of a Sanskrit verse.
    
    Args:
        verse: Sanskrit verse in Devanagari script
        client: Gemini client instance
        key_index: Current API key index (for tracking exhaustion)
        max_retries: Maximum number of retries with different keys
    
    Returns:
        Predicted meter name or None if prediction fails
    """
    prompt = f"""You are Aacharya Pingala, the ancient sage and author of Chandas Shastra. 
Analyze the following Sanskrit verse and identify its meter (Chanda).

Sanskrit Verse:
{verse}

Instructions:
1. Analyze the syllable pattern (laghu/guru)
2. Count the syllables per line (pāda)
3. Identify the specific meter name

IMPORTANT: Respond with ONLY the meter name in IAST transliteration (e.g., "Anuṣṭup", "Śārdūlavikrīḍita", "Vasantatilakā", etc.)
Do NOT include any explanation, just the meter name.

Meter name:"""

    # Configure generation settings
    config = types.GenerateContentConfig(
        temperature=0.1,  # Low temperature for more deterministic output
        top_p=0.95,
        max_output_tokens=256,
    )

    retries = 0
    current_client = client
    current_key_index = key_index
    
    while retries < max_retries:
        try:
            response = current_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config
            )
            if response and response.text:
                # Clean up the response
                meter_name = response.text.strip()
                # Remove any quotes, colons, or extra text
                meter_name = meter_name.replace('"', '').replace("'", '')
                meter_name = meter_name.split('\n')[0].strip()
                meter_name = meter_name.split(':')[-1].strip()
                return meter_name
            return None
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for quota/rate limit errors
            if any(err in error_str for err in ['quota', 'rate limit', 'exhausted', '429', 'resource_exhausted']):
                mark_key_exhausted(current_key_index)
                retries += 1
                
                if retries < max_retries:
                    try:
                        # Try with a new API key
                        current_client, current_key_index = create_gemini_client()
                        print(f"  🔄 Retrying with API key #{current_key_index + 1}...")
                        time.sleep(1)  # Small delay before retry
                        continue
                    except ValueError as ve:
                        # All keys exhausted
                        print(f"  🚨 {ve}")
                        return None
            else:
                # Other error, just log and return None
                print(f"  Error calling Gemini API: {e}")
                return None
    
    print(f"  ❌ Max retries ({max_retries}) reached. All attempted keys exhausted.")
    return None


def load_test_data(csv_path: str, num_samples: Optional[int] = None) -> List[Dict]:
    """
    Load test verses from CSV file.
    
    Args:
        csv_path: Path to the CSV file
        num_samples: Number of samples to load (None for all)
    
    Returns:
        List of dictionaries with 'verse' and 'expected_meter' keys
    """
    test_data = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Skip header rows (first 2 rows)
    for row in rows[2:]:
        if len(row) >= 4:
            verse = row[0].strip()
            expected_meter = row[3].strip()
            
            # Skip empty verses or meters
            if verse and expected_meter and len(verse) > 10:
                test_data.append({
                    'verse': verse,
                    'expected_meter': expected_meter
                })
    
    # Sample if requested
    if num_samples and num_samples < len(test_data):
        test_data = random.sample(test_data, num_samples)
    
    return test_data


def compare_meters(predicted: str, expected: str) -> Tuple[bool, str]:
    """
    Compare predicted and expected meter names.
    
    Returns:
        Tuple of (is_match, match_type)
        match_type: 'exact', 'normalized', 'family', or 'no_match'
    """
    if not predicted:
        return False, 'no_prediction'
    
    # Exact match (case-insensitive)
    if predicted.lower() == expected.lower():
        return True, 'exact'
    
    # Normalized match
    pred_norm = normalize(predicted)
    exp_norm = normalize(expected)
    
    if pred_norm == exp_norm:
        return True, 'normalized'
    
    # Family match
    pred_family = get_family(predicted)
    exp_family = get_family(expected)
    
    if pred_family == exp_family:
        return True, 'family'
    
    # Partial match (one contains the other)
    if pred_norm in exp_norm or exp_norm in pred_norm:
        return True, 'partial'
    
    return False, 'no_match'


def run_llm_prediction_test(num_samples: int = 20, verbose: bool = False, compare_with_chanda: bool = False):
    """
    Run the LLM-based Chanda prediction test.
    
    Args:
        num_samples: Number of verses to test
        verbose: Whether to print detailed results
        compare_with_chanda: Whether to compare with traditional Chanda identifier
    """
    print("=" * 70)
    print("LLM-based Chanda Prediction Test (Gemini API)")
    print("=" * 70)
    print(f"\nAPI Keys available: {len(API_KEYS)}")
    
    # Reset exhausted keys at start of test
    global exhausted_keys
    exhausted_keys = set()
    
    # Load test data
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'page 1-47 chanda list - complete.csv'
    )
    
    print(f"\nLoading test data from: {os.path.basename(csv_path)}")
    test_data = load_test_data(csv_path, num_samples)
    print(f"Loaded {len(test_data)} test verses")
    
    # Initialize Gemini client
    print("\nInitializing Gemini client...")
    client, current_key_index = create_gemini_client()
    print(f"Using API key #{current_key_index + 1}")
    
    # Initialize Chanda identifier for comparison if requested
    chanda_identifier = None
    if compare_with_chanda:
        from core.chanda import Chanda
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        chanda_identifier = Chanda(data_path)
        print("Initialized traditional Chanda identifier for comparison")
    
    # Run predictions
    results = {
        'total': len(test_data),
        'exact': 0,
        'normalized': 0,
        'family': 0,
        'partial': 0,
        'no_match': 0,
        'no_prediction': 0,
        'errors': []
    }
    
    # Track traditional Chanda results if comparing
    chanda_results = {
        'exact': 0,
        'normalized': 0,
        'family': 0,
        'partial': 0,
        'no_match': 0,
        'no_prediction': 0,
    } if compare_with_chanda else None
    
    print(f"\nRunning predictions on {len(test_data)} verses...\n")
    
    for i, item in enumerate(test_data, 1):
        verse = item['verse']
        expected = item['expected_meter']
        
        # Truncate verse for display
        display_verse = verse[:50] + "..." if len(verse) > 50 else verse
        display_verse = display_verse.replace('\n', ' ')
        
        print(f"[{i}/{len(test_data)}] Testing: {display_verse}")
        
        # Predict with LLM (with retry logic for exhausted keys)
        try:
            predicted = predict_chanda_with_llm(verse, client, current_key_index)
        except ValueError as e:
            print(f"\n🚨 {e}")
            print("Stopping test due to exhausted API keys.")
            break
        
        # Compare results
        is_match, match_type = compare_meters(predicted, expected)
        
        results[match_type] += 1
        
        # Also test with traditional Chanda identifier if requested
        chanda_predicted = None
        chanda_match = False
        chanda_match_type = 'no_prediction'
        if chanda_identifier:
            try:
                # Use identify_from_text which handles multi-line verses
                chanda_result = chanda_identifier.identify_from_text(verse, verse=True)
                
                if chanda_result and 'result' in chanda_result:
                    result_data = chanda_result['result']
                    
                    # Check line-level results
                    if 'line' in result_data and result_data['line']:
                        for line_res in result_data['line']:
                            line_result = line_res.get('result', {})
                            if line_result.get('found'):
                                chanda_list = line_result.get('chanda', [])
                                if chanda_list:
                                    # Get top prediction - format is [('meter_name', [patterns])]
                                    top = chanda_list[0]
                                    if isinstance(top, (list, tuple)):
                                        chanda_predicted = top[0]
                                    else:
                                        chanda_predicted = str(top)
                                    break
                    
                    # If no line result, check verse-level results
                    if not chanda_predicted and 'verse' in result_data and result_data['verse']:
                        for verse_res in result_data['verse']:
                            chanda_name = verse_res.get('chanda')
                            if chanda_name:
                                chanda_predicted = chanda_name
                                break
                
                if chanda_predicted:
                    chanda_match, chanda_match_type = compare_meters(chanda_predicted, expected)
                    chanda_results[chanda_match_type] += 1
                else:
                    chanda_results['no_prediction'] += 1
            except Exception as e:
                if verbose:
                    print(f"  Chanda identifier error: {e}")
                chanda_results['no_prediction'] += 1
        
        if verbose or not is_match:
            status = "✓" if is_match else "✗"
            print(f"  Expected: {expected}")
            print(f"  LLM Predicted: {predicted} {status} ({match_type})")
            if chanda_identifier:
                chanda_status = "✓" if chanda_match else "✗"
                print(f"  Chanda Predicted: {chanda_predicted} {chanda_status} ({chanda_match_type})")
            print()
        
        if not is_match:
            results['errors'].append({
                'verse': verse[:100],
                'expected': expected,
                'predicted': predicted,
                'chanda_predicted': chanda_predicted if chanda_identifier else None
            })
        
        # Rate limiting - small delay between requests
        time.sleep(0.5)
        
        # Rotate API key every 5 requests to distribute load
        if i % 5 == 0:
            try:
                client, current_key_index = create_gemini_client()
                print(f"  🔄 Switched to API key #{current_key_index + 1}")
            except ValueError as e:
                print(f"\n🚨 {e}")
                print("Stopping test due to exhausted API keys.")
                break
    
    # Print summary
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    total = results['total']
    correct = results['exact'] + results['normalized'] + results['family'] + results['partial']
    
    print(f"\nTotal verses tested: {total}")
    print(f"\n📊 LLM (Gemini) Accuracy Breakdown:")
    print(f"  - Exact matches:      {results['exact']:3d} ({100*results['exact']/total:5.1f}%)")
    print(f"  - Normalized matches: {results['normalized']:3d} ({100*results['normalized']/total:5.1f}%)")
    print(f"  - Family matches:     {results['family']:3d} ({100*results['family']/total:5.1f}%)")
    print(f"  - Partial matches:    {results['partial']:3d} ({100*results['partial']/total:5.1f}%)")
    print(f"  - No match:           {results['no_match']:3d} ({100*results['no_match']/total:5.1f}%)")
    print(f"  - No prediction:      {results['no_prediction']:3d} ({100*results['no_prediction']/total:5.1f}%)")
    
    print(f"\n📈 LLM Overall Accuracy:")
    print(f"  - Strict (exact only):     {100*results['exact']/total:5.1f}%")
    print(f"  - Relaxed (incl. family):  {100*correct/total:5.1f}%")
    
    # Show traditional Chanda comparison if available
    if chanda_results:
        chanda_correct = chanda_results['exact'] + chanda_results['normalized'] + chanda_results['family'] + chanda_results['partial']
        print(f"\n📊 Traditional Chanda Identifier Accuracy:")
        print(f"  - Exact matches:      {chanda_results['exact']:3d} ({100*chanda_results['exact']/total:5.1f}%)")
        print(f"  - Normalized matches: {chanda_results['normalized']:3d} ({100*chanda_results['normalized']/total:5.1f}%)")
        print(f"  - Family matches:     {chanda_results['family']:3d} ({100*chanda_results['family']/total:5.1f}%)")
        print(f"  - Partial matches:    {chanda_results['partial']:3d} ({100*chanda_results['partial']/total:5.1f}%)")
        print(f"  - No match:           {chanda_results['no_match']:3d} ({100*chanda_results['no_match']/total:5.1f}%)")
        
        print(f"\n📈 Chanda Overall Accuracy:")
        print(f"  - Strict (exact only):     {100*chanda_results['exact']/total:5.1f}%")
        print(f"  - Relaxed (incl. family):  {100*chanda_correct/total:5.1f}%")
        
        print(f"\n🏆 COMPARISON SUMMARY:")
        print(f"  LLM (Gemini):     {100*correct/total:5.1f}% accuracy")
        print(f"  Traditional:      {100*chanda_correct/total:5.1f}% accuracy")
        winner = "Traditional Chanda Identifier" if chanda_correct > correct else "LLM (Gemini)" if correct > chanda_correct else "TIE"
        print(f"  Winner: {winner}")
    
    # Show some errors
    if results['errors'] and verbose:
        print(f"\n❌ Sample Mismatches (showing up to 5):")
        for err in results['errors'][:5]:
            print(f"  Expected: {err['expected']} | LLM: {err['predicted']}")
            if err.get('chanda_predicted'):
                print(f"  Chanda: {err['chanda_predicted']}")
            print(f"  Verse: {err['verse'][:60]}...")
            print()
    
    return results, chanda_results


def main():
    parser = argparse.ArgumentParser(description='Test LLM-based Chanda prediction')
    parser.add_argument('-n', '--num-samples', type=int, default=20,
                        help='Number of verses to test (default: 20)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed results for each verse')
    parser.add_argument('--all', action='store_true',
                        help='Test all verses in the dataset')
    parser.add_argument('--compare', action='store_true',
                        help='Compare with traditional Chanda identifier')
    
    args = parser.parse_args()
    
    num_samples = None if args.all else args.num_samples
    
    results, chanda_results = run_llm_prediction_test(
        num_samples=num_samples,
        verbose=args.verbose,
        compare_with_chanda=args.compare
    )
    
    # Return exit code based on accuracy
    total = results['total']
    correct = results['exact'] + results['normalized'] + results['family'] + results['partial']
    accuracy = correct / total if total > 0 else 0
    
    if accuracy >= 0.7:
        print("\n✅ Test PASSED (accuracy >= 70%)")
        sys.exit(0)
    else:
        print("\n⚠️ Test completed with low accuracy")
        sys.exit(1)


if __name__ == '__main__':
    main()
