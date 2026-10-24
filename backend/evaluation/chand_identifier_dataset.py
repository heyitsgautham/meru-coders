#!/usr/bin/env python3
"""
Test Chandojñānam against Chand-Identifier dataset (279 verses)

This test validates our meter identification against the labeled dataset
from the Chand-Identifier repository, which includes:
- Classical Sanskrit verses
- 50+ Rigveda verses with Vedic accent marks
- Bhagavad Gita verses
- Common shlokas

We test:
1. Syllabification accuracy
2. L-G pattern classification
3. Meter identification accuracy
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.chanda import Chanda

# Initialize Chanda with data path
DATA_PATH = Path(__file__).parent.parent / "data"
chanda = Chanda(str(DATA_PATH))


def load_dataset():
    """Load the Chand-Identifier silver dataset"""
    dataset_path = Path(__file__).parent.parent / "repos" / "Chand-Identifier" / "train" / "hf_silver.jsonl"
    
    if not dataset_path.exists():
        print(f"❌ Dataset not found at: {dataset_path}")
        return []
    
    verses = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            verses.append(json.loads(line.strip()))
    
    return verses


def compare_syllables(expected, actual):
    """Compare syllable lists (allowing for slight variations in splitting)"""
    # Normalize by removing spaces and combining marks for comparison
    def normalize(sylls):
        return ''.join(sylls).replace(' ', '').replace('\u0951', '').replace('\u0952', '')
    
    exp_norm = normalize(expected)
    act_norm = normalize(actual)
    
    return exp_norm == act_norm


def compare_lg_patterns(expected, actual):
    """Compare L-G patterns"""
    if len(expected) != len(actual):
        return False, f"Length mismatch: {len(expected)} vs {len(actual)}"
    
    mismatches = []
    for i, (e, a) in enumerate(zip(expected, actual)):
        if e != a:
            mismatches.append(f"pos {i}: expected {e}, got {a}")
    
    if mismatches:
        return False, "; ".join(mismatches[:3])  # Show first 3 mismatches
    
    return True, ""


def test_single_verse(verse_data, verbose=False):
    """Test a single verse"""
    verse_id = verse_data['id']
    text = verse_data['text']
    expected_syllables = verse_data['syllables']
    expected_labels = verse_data['labels']
    
    # Run identification
    try:
        result = chanda.identify_line(text)
        
        if not result:
            return {
                'id': verse_id,
                'text': text,
                'status': 'FAIL',
                'error': 'No result returned',
                'syllables_match': False,
                'lg_match': False
            }
        
        # Get actual syllables and pattern
        actual_syllables = result.get('syllables', [])
        # Use display_lg which is in output scheme, or convert lg from Devanagari
        actual_pattern_raw = result.get('display_lg', '') or result.get('lg', '')
        
        # Convert Devanagari L-G to Latin if needed
        if isinstance(actual_pattern_raw, list):
            # It's a list, convert each element
            actual_pattern = ''.join(actual_pattern_raw).replace('ग', 'G').replace('ल', 'L').replace('', '')
        else:
            # It's a string
            actual_pattern = str(actual_pattern_raw).replace('ग', 'G').replace('ल', 'L')
        
        # Compare syllables (normalized)
        syllables_match = compare_syllables(expected_syllables, actual_syllables)
        
        # Compare L-G patterns
        lg_match, lg_error = compare_lg_patterns(expected_labels, list(actual_pattern))
        
        # Get top meter from chanda list
        chanda_list = result.get('chanda', [])
        if chanda_list:
            top_meter_tuple = chanda_list[0]
            if isinstance(top_meter_tuple, tuple):
                top_meter_name = top_meter_tuple[0]
            else:
                top_meter_name = str(top_meter_tuple)
            # Get confidence if available
            confidence_scores = result.get('confidence_scores', {})
            confidence = confidence_scores.get(top_meter_name, (0.0, ''))[0] if confidence_scores else 0.0
            top_meter = {'name': top_meter_name, 'confidence': confidence}
        else:
            top_meter = None
        
        test_result = {
            'id': verse_id,
            'text': text[:50] + '...' if len(text) > 50 else text,
            'status': 'PASS' if (syllables_match and lg_match) else 'PARTIAL' if syllables_match or lg_match else 'FAIL',
            'syllables_match': syllables_match,
            'lg_match': lg_match,
            'lg_error': lg_error if not lg_match else '',
            'expected_syllables': len(expected_syllables),
            'actual_syllables': len(actual_syllables),
            'expected_pattern': ''.join(expected_labels),
            'actual_pattern': actual_pattern,
            'top_meter': top_meter['name'] if top_meter else 'None',
            'confidence': top_meter['confidence'] if top_meter else 0.0
        }
        
        if verbose and test_result['status'] != 'PASS':
            print(f"\n{'='*80}")
            print(f"Verse {verse_id}: {text[:60]}...")
            print(f"Status: {test_result['status']}")
            print(f"Syllables: {test_result['expected_syllables']} expected, {test_result['actual_syllables']} actual")
            print(f"Expected pattern: {test_result['expected_pattern']}")
            print(f"Actual pattern:   {test_result['actual_pattern']}")
            if not lg_match:
                print(f"L-G Error: {lg_error}")
            print(f"Top meter: {test_result['top_meter']} (confidence: {test_result['confidence']:.2f})")
        
        return test_result
        
    except Exception as e:
        return {
            'id': verse_id,
            'text': text,
            'status': 'ERROR',
            'error': str(e),
            'syllables_match': False,
            'lg_match': False
        }


def run_tests(verbose=False, limit=None):
    """Run all tests"""
    print("="*80)
    print("Testing Chandojñānam against Chand-Identifier Dataset")
    print("="*80)
    
    verses = load_dataset()
    
    if not verses:
        print("❌ No verses loaded from dataset")
        return
    
    total = len(verses)
    if limit:
        verses = verses[:limit]
        print(f"\n📊 Testing first {limit} of {total} verses...")
    else:
        print(f"\n📊 Testing all {total} verses...")
    
    results = []
    for verse in verses:
        result = test_single_verse(verse, verbose=verbose)
        results.append(result)
    
    # Calculate statistics
    pass_count = sum(1 for r in results if r['status'] == 'PASS')
    partial_count = sum(1 for r in results if r['status'] == 'PARTIAL')
    fail_count = sum(1 for r in results if r['status'] == 'FAIL')
    error_count = sum(1 for r in results if r['status'] == 'ERROR')
    
    syllables_correct = sum(1 for r in results if r.get('syllables_match', False))
    lg_correct = sum(1 for r in results if r.get('lg_match', False))
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    print(f"Total verses tested: {len(results)}")
    print(f"\nOverall Status:")
    print(f"  ✅ PASS (both syllables & L-G correct): {pass_count} ({pass_count/len(results)*100:.1f}%)")
    print(f"  ⚠️  PARTIAL (one component correct): {partial_count} ({partial_count/len(results)*100:.1f}%)")
    print(f"  ❌ FAIL (both incorrect): {fail_count} ({fail_count/len(results)*100:.1f}%)")
    print(f"  🔥 ERROR (exception): {error_count} ({error_count/len(results)*100:.1f}%)")
    
    print(f"\nComponent Accuracy:")
    print(f"  Syllabification: {syllables_correct}/{len(results)} ({syllables_correct/len(results)*100:.1f}%)")
    print(f"  L-G Pattern:     {lg_correct}/{len(results)} ({lg_correct/len(results)*100:.1f}%)")
    
    # Categorize by verse type
    vedic_verses = [r for r in results if any(c in r['text'] for c in ['\u0951', '\u0952', '\u1CD0', '\u1CD1', '\u1CD2'])]
    classical_verses = [r for r in results if r not in vedic_verses]
    
    if vedic_verses:
        vedic_pass = sum(1 for r in vedic_verses if r['status'] == 'PASS')
        print(f"\nVedic verses: {vedic_pass}/{len(vedic_verses)} pass ({vedic_pass/len(vedic_verses)*100:.1f}%)")
    
    if classical_verses:
        classical_pass = sum(1 for r in classical_verses if r['status'] == 'PASS')
        print(f"Classical verses: {classical_pass}/{len(classical_verses)} pass ({classical_pass/len(classical_verses)*100:.1f}%)")
    
    # Show sample failures
    failures = [r for r in results if r['status'] in ['FAIL', 'ERROR']]
    if failures and not verbose:
        print(f"\n⚠️  Sample failures (showing first 5 of {len(failures)}):")
        for r in failures[:5]:
            print(f"\nVerse {r['id']}: {r['text'][:60]}...")
            if 'error' in r:
                print(f"  Error: {r['error']}")
            else:
                print(f"  Expected: {r.get('expected_pattern', 'N/A')}")
                print(f"  Actual:   {r.get('actual_pattern', 'N/A')}")
                if r.get('lg_error'):
                    print(f"  Issue: {r['lg_error']}")
    
    print("\n" + "="*80)
    
    # Return results for further analysis
    return results


def analyze_meter_detection(results):
    """Analyze which meters were detected"""
    meter_counts = {}
    for r in results:
        if r['status'] in ['PASS', 'PARTIAL'] and 'top_meter' in r:
            meter = r['top_meter']
            meter_counts[meter] = meter_counts.get(meter, 0) + 1
    
    print("\n" + "="*80)
    print("METER DETECTION ANALYSIS")
    print("="*80)
    print("Top 10 detected meters:")
    for meter, count in sorted(meter_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {meter}: {count} verses")
    
    return meter_counts


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Chandojñānam against Chand-Identifier dataset')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output for failures')
    parser.add_argument('-l', '--limit', type=int, help='Limit number of verses to test')
    parser.add_argument('-m', '--meters', action='store_true', help='Show meter detection analysis')
    
    args = parser.parse_args()
    
    results = run_tests(verbose=args.verbose, limit=args.limit)
    
    if results and args.meters:
        analyze_meter_detection(results)
