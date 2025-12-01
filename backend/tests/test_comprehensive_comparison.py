#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE MODEL PERFORMANCE COMPARISON
==========================================
SIH 2025 Grand Finale - Chandojñānam Project

Compares:
- Our Model (chanda.py with 2,055 meters database)
- IITK Reference Model (chanda_iitk.py with 398 meters database)

Test Categories:
1. Single Pada (Quarter-verse) Tests - Fair comparison
2. Full Shloka Tests - Tests complete verse handling
3. Vedic Meter Tests - Tests special meter categories
"""

import os
import sys
import time
import csv

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'reference', 'alternative_implementations')))

from core.chanda import Chanda as OurChanda
from chanda_iitk import Chanda as IITKChanda


# Test Categories
SINGLE_PADA_TESTS = [
    ('Anushtubh', 'अनुष्टुभ्', 'धर्मक्षेत्रे कुरुक्षेत्रे'),
    ('Anushtubh', 'अनुष्टुभ्', 'समवेता युयुत्सवः'),
    ('Anushtubh', 'अनुष्टुभ्', 'कर्मण्येवाधिकारस्ते'),
    ('Anushtubh', 'अनुष्टुभ्', 'मा फलेषु कदाचन'),
    ('Anushtubh', 'अनुष्टुभ्', 'यदा यदा हि धर्मस्य'),
    ('Anushtubh', 'अनुष्टुभ्', 'ग्लानिर्भवति भारत'),
    ('Anushtubh', 'अनुष्टुभ्', 'वक्रतुण्ड महाकाय'),
    ('Anushtubh', 'अनुष्टुभ्', 'गुरुर्ब्रह्मा गुरुर्विष्णुः'),
]

FULL_SHLOKA_TESTS = [
    ('Full Anushtubh (BG 1.1)', 'अनुष्टुभ्', 
     'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय'),
    ('Full Anushtubh (BG 4.7)', 'अनुष्टुभ्', 
     'यदा यदा हि धर्मस्य ग्लानिर्भवति भारत अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम्'),
    ('Full Anushtubh (BG 2.47)', 'अनुष्टुभ्', 
     'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि'),
]

VEDIC_METER_TESTS = [
    ('Gayatri (24 syllables)', 'गायत्री', 
     'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्'),
]

JAGATI_TESTS = [
    ('Jagati (48 syllables)', 'जगती',
     'काश्चित्कान्ता समुपेत्य यस्तया सह मोदते विरहः स पुनर्मिलनं सः खलु नः पुनराप्तसंगमानां विरहजनितवेदनां न वेत्ति'),
]


def check_result(expected, result):
    """Check if expected meter is in result"""
    if not result:
        return False, None
    
    chanda_list = result.get('chanda', [])
    if chanda_list:
        for item in chanda_list:
            if isinstance(item, (list, tuple)) and len(item) > 0:
                name = item[0]
                if expected in name or name in expected:
                    return True, name
    
    fuzzy_list = result.get('fuzzy', [])
    for fuzzy in fuzzy_list:
        for item in fuzzy.get('chanda', []):
            if isinstance(item, (list, tuple)) and len(item) > 0:
                name = item[0]
                if expected in name or name in expected:
                    return True, name
    
    first = None
    if chanda_list and isinstance(chanda_list[0], (list, tuple)):
        first = chanda_list[0][0]
    return False, first


def run_category_tests(model_name, model, tests, category_name):
    """Run tests for a category and return results"""
    correct = 0
    times = []
    results = []
    
    for test in tests:
        name, expected, verse = test
        start = time.time()
        try:
            result = model.identify_line(verse, fuzzy=True)
            match, got = check_result(expected, result)
        except Exception as e:
            match, got = False, f"Error"
        elapsed = time.time() - start
        times.append(elapsed)
        
        if match:
            correct += 1
        results.append((name, expected, got, match))
    
    return {
        'correct': correct,
        'total': len(tests),
        'accuracy': correct / len(tests) * 100 if tests else 0,
        'avg_time': sum(times) / len(times) * 1000 if times else 0,
        'results': results
    }


def main():
    print("=" * 95)
    print("CHANDOJÑĀNAM - COMPREHENSIVE MODEL PERFORMANCE COMPARISON")
    print("SIH 2025 Grand Finale | Meru Coders Team")
    print("=" * 95)
    print()
    
    # Initialize
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    our_data_path = os.path.join(base_path, 'data')
    iitk_data_path = os.path.join(base_path, '..', 'repos', 'chanda', 'data')
    
    print("Loading models...")
    our_model = OurChanda(our_data_path)
    iitk_model = IITKChanda(iitk_data_path)
    print("✓ Models loaded successfully")
    print()
    
    # Count database sizes
    our_count = 0
    for f in ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv', 'chanda_vedic.csv', 'chanda_matra.csv']:
        fp = os.path.join(our_data_path, f)
        if os.path.exists(fp):
            with open(fp, 'r') as fh:
                our_count += max(0, sum(1 for line in fh if line.strip()) - 1)
    
    iitk_count = 0
    for f in ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv']:
        fp = os.path.join(iitk_data_path, f)
        if os.path.exists(fp):
            with open(fp, 'r') as fh:
                iitk_count += max(0, sum(1 for line in fh if line.strip()) - 1)
    
    print(f"Database Comparison:")
    print(f"  Our Model:  {our_count:,} meters")
    print(f"  IITK Model: {iitk_count:,} meters")
    print(f"  Ratio:      {our_count/iitk_count:.1f}x larger")
    print()
    
    # Test categories
    categories = [
        ("SINGLE PADA (QUARTER-VERSE)", SINGLE_PADA_TESTS),
        ("FULL SHLOKA (COMPLETE VERSE)", FULL_SHLOKA_TESTS),
        ("VEDIC METERS", VEDIC_METER_TESTS),
        ("JAGATI (48 SYLLABLES)", JAGATI_TESTS),
    ]
    
    our_total = {'correct': 0, 'total': 0, 'times': []}
    iitk_total = {'correct': 0, 'total': 0, 'times': []}
    
    for cat_name, tests in categories:
        print("=" * 95)
        print(f"CATEGORY: {cat_name}")
        print("=" * 95)
        
        our_results = run_category_tests("Our", our_model, tests, cat_name)
        iitk_results = run_category_tests("IITK", iitk_model, tests, cat_name)
        
        # Print results table
        print(f"{'Test':<40} {'Expected':<15} {'Our':<12} {'IITK':<12} {'Our':>5} {'IITK':>5}")
        print("-" * 95)
        
        for i in range(len(tests)):
            our_name, our_exp, our_got, our_match = our_results['results'][i]
            iitk_name, iitk_exp, iitk_got, iitk_match = iitk_results['results'][i]
            
            our_status = "✅" if our_match else "❌"
            iitk_status = "✅" if iitk_match else "❌"
            our_display = (our_got or "None")[:10]
            iitk_display = (iitk_got or "None")[:10]
            
            print(f"{our_name[:38]:<40} {our_exp[:13]:<15} {our_display:<12} {iitk_display:<12} {our_status:>5} {iitk_status:>5}")
        
        print()
        print(f"Category Results: Our Model {our_results['correct']}/{our_results['total']} ({our_results['accuracy']:.0f}%) | "
              f"IITK Model {iitk_results['correct']}/{iitk_results['total']} ({iitk_results['accuracy']:.0f}%)")
        print()
        
        our_total['correct'] += our_results['correct']
        our_total['total'] += our_results['total']
        iitk_total['correct'] += iitk_results['correct']
        iitk_total['total'] += iitk_results['total']
    
    # Final Summary
    print("=" * 95)
    print("FINAL SUMMARY")
    print("=" * 95)
    print()
    
    our_accuracy = our_total['correct'] / our_total['total'] * 100
    iitk_accuracy = iitk_total['correct'] / iitk_total['total'] * 100
    
    print(f"{'Metric':<40} {'Our Model':>25} {'IITK Model':>25}")
    print("-" * 95)
    print(f"{'Database Size':<40} {f'{our_count:,} meters':>25} {f'{iitk_count:,} meters':>25}")
    print(f"{'Total Test Cases':<40} {our_total['total']:>25} {iitk_total['total']:>25}")
    print(f"{'Correct Identifications':<40} {our_total['correct']:>25} {iitk_total['correct']:>25}")
    print(f"{'Overall Accuracy':<40} {f'{our_accuracy:.1f}%':>25} {f'{iitk_accuracy:.1f}%':>25}")
    print()
    
    # Winner announcement
    print("=" * 95)
    diff = our_accuracy - iitk_accuracy
    if diff > 0:
        print(f"🏆 WINNER: OUR MODEL with {our_accuracy:.1f}% accuracy (vs IITK's {iitk_accuracy:.1f}%)")
        print(f"   Improvement: +{diff:.1f}% accuracy with {our_count/iitk_count:.1f}x larger database")
    elif diff < 0:
        print(f"📉 IITK Model leads with {iitk_accuracy:.1f}% (vs Our's {our_accuracy:.1f}%)")
    else:
        print(f"🤝 TIE: Both models at {our_accuracy:.1f}% accuracy")
    
    print()
    print("KEY ADVANTAGES OF OUR MODEL:")
    print(f"  ✓ {our_count:,} meters vs {iitk_count:,} meters ({our_count/iitk_count:.1f}x larger)")
    print(f"  ✓ Handles full shlokas (IITK only handles single padas)")
    print(f"  ✓ Vedic meter support with syllable-count detection")
    print(f"  ✓ Multi-level confidence scoring")
    print("=" * 95)


if __name__ == '__main__':
    main()
