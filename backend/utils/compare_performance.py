#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Comparison: Original vs ICU vs Hybrid
Compares three implementations on accuracy, speed, and coverage
"""

import time
import sys
import os
from collections import Counter

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from chanda import Chanda
from chanda_icu import ChandaICU
from chanda_hybrid import ChandaHybrid


# Test cases from test_all_fixes.py
TEST_CASES = [
    {
        'name': 'Gayatri Mantra (24 syllables)',
        'text': 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्',
        'expected_syllables': 24,
        'expected_meter': 'गायत्री'
    },
    {
        'name': 'Anushtubh (Bhagavad Gita 2.47)',
        'text': 'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।\nमा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥',
        'expected_syllables': 32,
        'expected_meter': 'अनुष्टुभ्'
    },
    {
        'name': 'Anushtubh (Bhagavad Gita 1.1)',
        'text': 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥',
        'expected_syllables': 32,
        'expected_meter': 'अनुष्टुभ्'
    },
    {
        'name': 'Anushtubh (Bhagavad Gita 4.7)',
        'text': 'यदा यदा हि धर्मस्य ग्लानिर्भवति भारत ।\nअभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम् ॥',
        'expected_syllables': 32,
        'expected_meter': 'अनुष्टुभ्'
    },
    {
        'name': 'Jagati (48 syllables)',
        'text': 'काश्चित्कान्ता समुपेत्य यस्तया सह मोदते विरहः स पुनर्मिलनं ।\nसः खलु नः पुनराप्तसंगमानां विरहजनितवेदनां न वेत्ति ॥',
        'expected_syllables': 48,
        'expected_meter': 'जगती'
    },
    {
        'name': 'Praharshini (Shakuntala)',
        'text': 'निर्दिष्टाङ् कुलपतिना स पर्णशालाम् अध्यास्य प्रयतपरिग्रहद्वितीयः ।\nतच्छिष्याध्ययननिवेदितावसानां सव्ँविष्टः कुशशयने निशान् निनाय ॥',
        'expected_syllables': 52,
        'expected_meter': 'प्रहर्षिणी'
    },
    {
        'name': 'Fragment Test 1',
        'text': 'धर्मक्षेत्रे',
        'expected_syllables': 4,
        'expected_meter': None
    },
    {
        'name': 'Fragment Test 2',
        'text': 'समवेता युयुत्सवः',
        'expected_syllables': 8,
        'expected_meter': None
    }
]


def count_syllables(result):
    """Count syllables from result"""
    if 'syllables' in result:
        syllables = result['syllables']
        if isinstance(syllables, list):
            if len(syllables) > 0 and isinstance(syllables[0], list):
                # Nested structure [[['syl1', 'syl2']]] or [['syl1', 'syl2']]
                try:
                    return sum(len(word) for line in syllables for word in line)
                except:
                    # Maybe it's just [['syl1', 'syl2']]
                    return sum(len(item) if isinstance(item, list) else 1 for item in syllables)
            else:
                # Flat structure ['syl1', 'syl2']
                return len(syllables)
    if 'lg' in result:
        return len([x for x in result['lg'] if x])  # Count non-empty
    if 'lg_str' in result:
        return len(result['lg_str'])
    return 0


def test_implementation(impl_class, impl_name, data_path):
    """Test a single implementation"""
    print(f"\n{'='*70}")
    print(f"Testing: {impl_name}")
    print(f"{'='*70}")
    
    try:
        # Initialize
        start_init = time.time()
        impl = impl_class(data_path)
        init_time = time.time() - start_init
        
        print(f"Initialization time: {init_time:.4f}s")
        
        # Get implementation info if available
        if hasattr(impl, 'get_method_info'):
            info = impl.get_method_info()
            print(f"Method info: {info}")
        
        results = []
        total_time = 0
        correct_syllables = 0
        correct_meters = 0
        total_identified = 0
        
        for test_case in TEST_CASES:
            print(f"\n--- {test_case['name']} ---")
            
            # Time the identification
            start = time.time()
            
            # Handle different verse structures
            if '\n' in test_case['text']:
                try:
                    result_obj = impl.identify_from_text(test_case['text'], verse=True)
                    if 'result' in result_obj:
                        result_obj = result_obj['result']
                    
                    if 'verse' in result_obj and result_obj['verse']:
                        verse_result = result_obj['verse'][0]
                        chanda_names = [c[0] if isinstance(c, tuple) else c 
                                       for c in verse_result['chanda'][0]]
                        score = verse_result['chanda'][1]
                        syllable_count = sum(
                            count_syllables(lr['result']) 
                            for lr in result_obj['line']
                        )
                    else:
                        chanda_names = []
                        score = 0
                        syllable_count = 0
                except Exception as e:
                    print(f"  Error in verse processing: {e}")
                    chanda_names = []
                    score = 0
                    syllable_count = 0
            else:
                result = impl.identify_line(test_case['text'])
                chanda_names = [c[0] if isinstance(c, tuple) else c 
                               for c in result.get('chanda', [])]
                score = 1 if result.get('found') else 0
                syllable_count = count_syllables(result)
            
            elapsed = time.time() - start
            total_time += elapsed
            
            # Check syllable accuracy
            syllable_match = syllable_count == test_case['expected_syllables']
            if syllable_match:
                correct_syllables += 1
            
            # Check meter identification
            meter_found = False
            if test_case['expected_meter'] and chanda_names:
                # Flexible matching
                expected = test_case['expected_meter'].lower()
                meter_found = any(expected in str(c).lower() or str(c).lower() in expected 
                                 for c in chanda_names)
                if meter_found:
                    correct_meters += 1
                    total_identified += 1
            elif test_case['expected_meter'] is None and chanda_names:
                total_identified += 1
            
            print(f"Syllables: {syllable_count} (expected: {test_case['expected_syllables']}) "
                  f"{'✓' if syllable_match else '✗'}")
            print(f"Identified: {chanda_names[:3]}... ({len(chanda_names)} total)")
            if test_case['expected_meter']:
                print(f"Expected meter: {test_case['expected_meter']} "
                      f"{'✓ FOUND' if meter_found else '✗ NOT FOUND'}")
            print(f"Time: {elapsed:.4f}s")
            
            results.append({
                'test': test_case['name'],
                'syllable_correct': syllable_match,
                'meter_found': meter_found,
                'identified_count': len(chanda_names),
                'time': elapsed
            })
        
        # Summary
        print(f"\n{'='*70}")
        print(f"SUMMARY: {impl_name}")
        print(f"{'='*70}")
        print(f"Initialization time: {init_time:.4f}s")
        print(f"Total processing time: {total_time:.4f}s")
        print(f"Average time per test: {total_time/len(TEST_CASES):.4f}s")
        print(f"Syllable accuracy: {correct_syllables}/{len(TEST_CASES)} "
              f"({100*correct_syllables/len(TEST_CASES):.1f}%)")
        
        # Only count tests that have expected meters
        tests_with_meters = sum(1 for tc in TEST_CASES if tc['expected_meter'])
        print(f"Meter identification: {correct_meters}/{tests_with_meters} "
              f"({100*correct_meters/tests_with_meters:.1f}%)")
        print(f"Total identifications made: {total_identified}/{len(TEST_CASES)}")
        
        return {
            'name': impl_name,
            'init_time': init_time,
            'total_time': total_time,
            'avg_time': total_time/len(TEST_CASES),
            'syllable_accuracy': correct_syllables/len(TEST_CASES),
            'meter_accuracy': correct_meters/tests_with_meters if tests_with_meters > 0 else 0,
            'results': results,
            'success': True
        }
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'name': impl_name,
            'success': False,
            'error': str(e)
        }


def main():
    """Run all tests and compare"""
    print("="*70)
    print("CHANDA IMPLEMENTATION PERFORMANCE COMPARISON")
    print("="*70)
    print(f"\nTest cases: {len(TEST_CASES)}")
    print("Implementations: Original, ICU-based, Hybrid")
    
    data_path = os.path.join(os.path.dirname(__file__), 'data')
    
    # Test all three implementations
    implementations = [
        (Chanda, "Original (sanskrit_text)"),
        (ChandaICU, "ICU-based"),
        (ChandaHybrid, "Hybrid (ICU + Original)")
    ]
    
    all_results = []
    for impl_class, impl_name in implementations:
        result = test_implementation(impl_class, impl_name, data_path)
        all_results.append(result)
        time.sleep(0.5)  # Brief pause between tests
    
    # Final comparison
    print(f"\n\n{'='*70}")
    print("FINAL COMPARISON")
    print(f"{'='*70}\n")
    
    successful = [r for r in all_results if r['success']]
    
    if len(successful) > 0:
        print(f"{'Implementation':<30} {'Init(s)':<10} {'Avg(s)':<10} {'Syllable':<12} {'Meter':<12}")
        print(f"{'-'*30} {'-'*10} {'-'*10} {'-'*12} {'-'*12}")
        
        for result in successful:
            print(f"{result['name']:<30} "
                  f"{result['init_time']:<10.4f} "
                  f"{result['avg_time']:<10.4f} "
                  f"{result['syllable_accuracy']*100:<11.1f}% "
                  f"{result['meter_accuracy']*100:<11.1f}%")
        
        # Determine winner
        print(f"\n{'='*70}")
        print("WINNER ANALYSIS")
        print(f"{'='*70}")
        
        best_speed = min(successful, key=lambda x: x['avg_time'])
        best_syllable = max(successful, key=lambda x: x['syllable_accuracy'])
        best_meter = max(successful, key=lambda x: x['meter_accuracy'])
        
        print(f"⚡ Fastest: {best_speed['name']} ({best_speed['avg_time']:.4f}s avg)")
        print(f"🎯 Best syllable accuracy: {best_syllable['name']} ({best_syllable['syllable_accuracy']*100:.1f}%)")
        print(f"🏆 Best meter identification: {best_meter['name']} ({best_meter['meter_accuracy']*100:.1f}%)")
        
        # Overall recommendation
        print(f"\n{'='*70}")
        print("RECOMMENDATION")
        print(f"{'='*70}")
        
        # Score each implementation
        scores = {}
        for result in successful:
            score = (
                result['syllable_accuracy'] * 40 +  # 40% weight
                result['meter_accuracy'] * 40 +      # 40% weight
                (1 / (result['avg_time'] + 0.001)) * 20 * 0.01  # 20% weight (normalized)
            )
            scores[result['name']] = score
        
        best_overall = max(scores.items(), key=lambda x: x[1])
        print(f"\n🏅 BEST OVERALL: {best_overall[0]}")
        print(f"   Score: {best_overall[1]:.2f}/100")
        
        print(f"\nAll scores:")
        for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            print(f"  {name}: {score:.2f}")
    
    failed = [r for r in all_results if not r['success']]
    if failed:
        print(f"\n⚠️  Failed implementations:")
        for result in failed:
            print(f"  - {result['name']}: {result.get('error', 'Unknown error')}")


if __name__ == '__main__':
    main()
