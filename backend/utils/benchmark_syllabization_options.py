#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benchmark script to compare syllabization options
Tests Option 1 (Boundary-Preserving) vs Option 2 (Enhanced ICU) vs Original
"""

import time
import sys
from collections import defaultdict

# Import all three versions
import chanda as original_chanda
import chanda_option1_boundary_fix as option1_chanda
try:
    import chanda_option2_icu_enhanced as option2_chanda
    ICU_AVAILABLE = True
except ImportError:
    ICU_AVAILABLE = False
    option2_chanda = None

###############################################################################
# TEST CASES
###############################################################################

TEST_CASES = [
    {
        'name': 'Gayatri Mantra (24 syllables)',
        'text': 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्',
        'expected_syllables': 24,
        'expected_meter': 'गायत्री',
        'weight': 10  # Critical test
    },
    {
        'name': 'Anushtubh Line 1 (BG 2.47)',
        'text': 'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन',
        'expected_syllables': 16,
        'expected_meter': 'अनुष्टुभ्',
        'weight': 5
    },
    {
        'name': 'Anushtubh Line 1 (BG 1.1)',
        'text': 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः',
        'expected_syllables': 16,
        'expected_meter': 'अनुष्टुभ्',
        'weight': 5
    },
    {
        'name': 'Anushtubh Line 1 (BG 4.7)',
        'text': 'यदा यदा हि धर्मस्य ग्लानिर्भवति भारत',
        'expected_syllables': 16,
        'expected_meter': 'अनुष्टुभ्',
        'weight': 5
    },
    {
        'name': 'Compound word test',
        'text': 'कर्मण्येवाधिकारस्ते',
        'expected_syllables': 9,
        'expected_meter': None,
        'weight': 2
    },
    {
        'name': 'Fragment 1',
        'text': 'धर्मक्षेत्रे',
        'expected_syllables': 4,
        'expected_meter': None,
        'weight': 1
    },
    {
        'name': 'Fragment 2',
        'text': 'समवेता युयुत्सवः',
        'expected_syllables': 8,
        'expected_meter': None,
        'weight': 1
    },
    {
        'name': 'Visarga boundary test',
        'text': 'नः प्रचोदयात्',
        'expected_syllables': 5,
        'expected_meter': None,
        'weight': 5  # CRITICAL test for boundary preservation
    },
    {
        'name': 'Complex visarga test',
        'text': 'धियो यो नः प्रचोदयात्',
        'expected_syllables': 9,
        'expected_meter': None,
        'weight': 3
    },
    {
        'name': 'Conjunct consonants',
        'text': 'तत्सवितुर्वरेण्यं',
        'expected_syllables': 7,
        'expected_meter': None,
        'weight': 2
    }
]

###############################################################################
# BENCHMARK FUNCTIONS
###############################################################################

def test_implementation(chanda_module, name, syllabization_method='sanskrit_text'):
    """Test a specific implementation"""
    print(f"\n{'='*80}")
    print(f"TESTING: {name} (method: {syllabization_method})")
    print(f"{'='*80}\n")
    
    try:
        c = chanda_module.Chanda('data/', syllabization_method=syllabization_method)
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return None
    
    results = {
        'name': name,
        'method': syllabization_method,
        'total_tests': len(TEST_CASES),
        'passed': 0,
        'failed': 0,
        'syllable_accuracy': 0,
        'meter_accuracy': 0,
        'total_time': 0,
        'avg_time_per_test': 0,
        'weighted_score': 0,
        'details': []
    }
    
    total_weight = sum(tc['weight'] for tc in TEST_CASES)
    weighted_score = 0
    
    for test_case in TEST_CASES:
        test_name = test_case['name']
        text = test_case['text']
        expected_syllables = test_case['expected_syllables']
        expected_meter = test_case['expected_meter']
        weight = test_case['weight']
        
        print(f"Test: {test_name}")
        print(f"Input: {text[:50]}...")
        
        try:
            start_time = time.time()
            result = c.identify_line(text)
            elapsed_time = time.time() - start_time
            
            actual_syllables = len(result.get('lg', []))
            found_meters = result.get('chanda', [])
            
            # Check syllable count
            syllable_match = (actual_syllables == expected_syllables)
            
            # Check meter identification
            meter_match = False
            if expected_meter:
                for meter in found_meters:
                    meter_name = meter[0] if isinstance(meter, tuple) else meter
                    if expected_meter in str(meter_name):
                        meter_match = True
                        break
            
            # Calculate score for this test
            test_passed = syllable_match
            if test_passed:
                results['passed'] += 1
                results['syllable_accuracy'] += 1
                if meter_match or expected_meter is None:
                    results['meter_accuracy'] += 1
                    weighted_score += weight
                else:
                    weighted_score += weight * 0.7  # Partial credit
            else:
                results['failed'] += 1
            
            results['total_time'] += elapsed_time
            
            # Store details
            status = '✓ PASS' if test_passed else '✗ FAIL'
            details = {
                'test': test_name,
                'passed': test_passed,
                'expected_syllables': expected_syllables,
                'actual_syllables': actual_syllables,
                'syllable_match': syllable_match,
                'expected_meter': expected_meter,
                'found_meters': [str(m) for m in found_meters[:3]],
                'meter_match': meter_match,
                'time': elapsed_time,
                'weight': weight
            }
            results['details'].append(details)
            
            print(f"  Expected syllables: {expected_syllables}")
            print(f"  Actual syllables: {actual_syllables}")
            if expected_meter:
                print(f"  Expected meter: {expected_meter}")
                print(f"  Found meters: {', '.join([str(m) for m in found_meters[:3]])}")
            print(f"  Time: {elapsed_time*1000:.2f}ms")
            print(f"  {status}")
            print()
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results['failed'] += 1
            results['details'].append({
                'test': test_name,
                'passed': False,
                'error': str(e),
                'weight': weight
            })
            print()
    
    # Calculate final metrics
    results['avg_time_per_test'] = results['total_time'] / results['total_tests']
    results['syllable_accuracy_pct'] = (results['syllable_accuracy'] / results['total_tests']) * 100
    results['meter_accuracy_pct'] = (results['meter_accuracy'] / results['total_tests']) * 100
    results['weighted_score'] = (weighted_score / total_weight) * 100
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"SUMMARY: {name}")
    print(f"{'='*80}")
    print(f"Total tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Syllable accuracy: {results['syllable_accuracy']}/{results['total_tests']} ({results['syllable_accuracy_pct']:.1f}%)")
    print(f"Meter accuracy: {results['meter_accuracy']}/{results['total_tests']} ({results['meter_accuracy_pct']:.1f}%)")
    print(f"Weighted score: {results['weighted_score']:.1f}/100")
    print(f"Total time: {results['total_time']*1000:.2f}ms")
    print(f"Avg time per test: {results['avg_time_per_test']*1000:.2f}ms")
    print(f"{'='*80}\n")
    
    return results

###############################################################################
# MAIN COMPARISON
###############################################################################

def main():
    print("\n" + "="*80)
    print("SYLLABIZATION OPTIONS BENCHMARK")
    print("Comparing: Original vs Option 1 (Boundary Fix) vs Option 2 (ICU Enhanced)")
    print("="*80)
    
    all_results = []
    
    # Test Original
    result_original = test_implementation(original_chanda, "Original (sanskrit_text)")
    if result_original:
        all_results.append(result_original)
    
    # Test Option 1
    result_option1 = test_implementation(option1_chanda, "Option 1: Boundary-Preserving Fix")
    if result_option1:
        all_results.append(result_option1)
    
    # Test Option 2 (ICU)
    if ICU_AVAILABLE and option2_chanda:
        result_option2 = test_implementation(option2_chanda, "Option 2: Enhanced ICU", syllabization_method='icu')
        if result_option2:
            all_results.append(result_option2)
    else:
        print("\n⚠️  Option 2 (ICU) not available - PyICU not installed")
    
    # Final Comparison
    print("\n" + "="*80)
    print("FINAL COMPARISON")
    print("="*80 + "\n")
    
    if len(all_results) >= 2:
        print(f"{'Implementation':<40} {'Syllable Acc':<15} {'Meter Acc':<15} {'Weighted Score':<15} {'Avg Time':<15}")
        print("-" * 100)
        
        for r in all_results:
            print(f"{r['name']:<40} {r['syllable_accuracy_pct']:>6.1f}% ({r['syllable_accuracy']}/{r['total_tests']})   "
                  f"{r['meter_accuracy_pct']:>6.1f}% ({r['meter_accuracy']}/{r['total_tests']})   "
                  f"{r['weighted_score']:>6.1f}/100       "
                  f"{r['avg_time_per_test']*1000:>6.2f}ms")
        
        print("\n" + "="*80)
        print("RECOMMENDATION")
        print("="*80)
        
        # Find best by weighted score
        best = max(all_results, key=lambda x: x['weighted_score'])
        print(f"\n🏆 WINNER: {best['name']}")
        print(f"   Weighted Score: {best['weighted_score']:.1f}/100")
        print(f"   Syllable Accuracy: {best['syllable_accuracy_pct']:.1f}%")
        print(f"   Meter Accuracy: {best['meter_accuracy_pct']:.1f}%")
        print(f"   Performance: {best['avg_time_per_test']*1000:.2f}ms per test")
        
        # Check if Option 1 achieves 100%
        if result_option1 and result_option1['syllable_accuracy'] == result_option1['total_tests']:
            print(f"\n✅ Option 1 achieves 100% syllable accuracy!")
            print(f"   RECOMMENDATION: Integrate Option 1 into chanda.py")
        
        print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()
