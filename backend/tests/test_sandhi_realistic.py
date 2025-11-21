#!/usr/bin/env python3
"""
Realistic Sandhi Resolution Test - Cases that ACTUALLY need sandhi resolution

This tests verses in their NATURAL merged form (as found in manuscripts/texts)
vs artificially split forms. These are real-world cases where sandhi resolution
is essential for correct meter identification.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.chanda import Chanda

# Initialize
DATA_PATH = Path(__file__).parent.parent / "data"
chanda = Chanda(str(DATA_PATH))

# Test cases with ACTUAL merged forms that fail without sandhi
TEST_CASES = [
    {
        'name': 'Rigveda 1.1.1 - Opening verse (MERGED NATURAL FORM)',
        'merged': 'अग्निमीळेपुरोहितं',  # How it appears in manuscripts
        'split': 'अग्निम् ईळे पुरोहितम्',  # Grammatically correct split
        'expected_syllables': 8,
        'expected_meter': 'गायत्री',
        'note': 'Real merged form from Rigveda - requires sandhi resolution'
    },
    {
        'name': 'Bhagavad Gita 2.47 - Natural manuscript form',
        'merged': 'कर्मण्येवाधिकारस्ते',  # Natural continuous form
        'split': 'कर्मणि एव अधिकारः ते',
        'expected_syllables': 10,
        'note': 'Multiple sandhis: karmaNi+eva+adhikAraH'
    },
    {
        'name': 'Mahabharata verse - Compound word',
        'merged': 'धर्मक्षेत्रेकुरुक्षेत्रे',  # Pure merged form
        'split': 'धर्म क्षेत्रे कुरु क्षेत्रे',
        'expected_syllables': 10,
        'note': 'Compound with internal sandhis'
    },
    {
        'name': 'Upanishadic mahavakya',
        'merged': 'तत्त्वमसि',  # Classical merged form
        'split': 'तत् त्वम् असि',
        'expected_syllables': 5,
        'note': 'tat+tvam+asi - Great saying of Chandogya Upanishad'
    },
    {
        'name': 'Ramayana verse fragment',
        'merged': 'रामोऽवदत्',  # With avagraha
        'split': 'रामः अवदत्',
        'expected_syllables': 5,
        'note': 'Visarga + vowel with avagraha notation'
    },
]

def test_realistic_sandhi():
    """Test with real merged forms that actually need sandhi resolution"""
    
    print("="*80)
    print("REALISTIC SANDHI RESOLUTION TEST")
    print("="*80)
    print("\nTesting verses in their NATURAL MERGED form (as found in texts)")
    print("vs ARTIFICIALLY SPLIT forms (grammatically correct)")
    print()
    
    results = {
        'merged_fail_split_pass': [],
        'both_pass': [],
        'sandhi_fixes': [],
        'total': len(TEST_CASES)
    }
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"Test #{i}: {test['name']}")
        print(f"{'='*80}")
        print(f"Merged form:  {test['merged']}")
        print(f"Split form:   {test['split']}")
        print(f"Note:         {test['note']}")
        print()
        
        # Test merged form WITHOUT sandhi
        print("❌ WITHOUT SANDHI (merged form):")
        merged_result = chanda.identify_line(test['merged'])
        merged_found = merged_result.get('found', False)
        merged_syllables = len(merged_result.get('syllables', []))
        merged_meter = merged_result.get('chanda', ['None'])[0]
        if isinstance(merged_meter, tuple):
            merged_meter = merged_meter[0]
        
        print(f"   Found: {merged_found}")
        print(f"   Syllables: {merged_syllables}")
        print(f"   Top meter: {merged_meter}")
        
        # Test split form WITHOUT sandhi
        print("\n✅ WITHOUT SANDHI (split form):")
        split_result = chanda.identify_line(test['split'])
        split_found = split_result.get('found', False)
        split_syllables = len(split_result.get('syllables', []))
        split_meter = split_result.get('chanda', ['None'])[0]
        if isinstance(split_meter, tuple):
            split_meter = split_meter[0]
        
        print(f"   Found: {split_found}")
        print(f"   Syllables: {split_syllables}")
        print(f"   Top meter: {split_meter}")
        
        # Test merged form WITH sandhi
        print("\n🔧 WITH SANDHI RESOLUTION (merged form):")
        sandhi_result = chanda.identify_with_sandhi(test['merged'], k_candidates=5)
        
        if sandhi_result:
            sandhi_found = sandhi_result.get('found', False)
            sandhi_syllables = len(sandhi_result.get('syllables', []))
            sandhi_meter = sandhi_result.get('chanda', ['None'])[0]
            if isinstance(sandhi_meter, tuple):
                sandhi_meter = sandhi_meter[0]
            
            # Get candidate info from sandhi_info if available
            sandhi_info = sandhi_result.get('sandhi_info', {})
            sandhi_candidate = sandhi_info.get('candidate_text', test['merged'])
            sandhi_score = sandhi_info.get('combined_score', 0.0)
            sandhi_rules = sandhi_info.get('rules', ['identity'])
            
            print(f"   Best candidate: {sandhi_candidate}")
            if isinstance(sandhi_rules, list):
                print(f"   Applied rules: {', '.join(sandhi_rules)}")
            print(f"   Found: {sandhi_found}")
            print(f"   Syllables: {sandhi_syllables}")
            print(f"   Top meter: {sandhi_meter}")
            print(f"   Combined score: {sandhi_score:.2f}")
        else:
            print("   ❌ Sandhi resolution unavailable")
            sandhi_found = False
            sandhi_syllables = 0
        
        # Analyze impact
        print(f"\n{'─'*80}")
        print("IMPACT ANALYSIS:")
        
        if not merged_found and split_found:
            print("⚠️  CRITICAL: Merged form FAILS, split form SUCCEEDS")
            print("   → This demonstrates the NEED for sandhi resolution")
            results['merged_fail_split_pass'].append(test['name'])
            
            if sandhi_found and sandhi_syllables == split_syllables:
                print("✅ FIXED: Sandhi resolution correctly identifies the meter!")
                results['sandhi_fixes'].append(test['name'])
            else:
                print("❌ NOT FIXED: Sandhi resolution doesn't help yet")
        
        elif merged_found and split_found:
            if merged_syllables != split_syllables:
                print("⚠️  WARNING: Both succeed but with DIFFERENT syllable counts")
                print(f"   Merged: {merged_syllables} syllables → {merged_meter}")
                print(f"   Split:  {split_syllables} syllables → {split_meter}")
                
                if sandhi_found and sandhi_syllables == split_syllables:
                    print("✅ RESOLVED: Sandhi finds the correct split-form syllables!")
                    results['sandhi_fixes'].append(test['name'])
            else:
                print("✅ BOTH FORMS WORK: Verse is well-formed")
                results['both_pass'].append(test['name'])
        
        else:
            print("❌ BOTH FAIL: Verse may not be in database")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total test cases: {results['total']}")
    print(f"\n📊 CRITICAL CASES (merged fails, split succeeds):")
    print(f"   Count: {len(results['merged_fail_split_pass'])}")
    for name in results['merged_fail_split_pass']:
        print(f"   • {name}")
    
    print(f"\n🔧 SANDHI RESOLUTION FIXES:")
    print(f"   Count: {len(results['sandhi_fixes'])}")
    for name in results['sandhi_fixes']:
        print(f"   • {name}")
    
    print(f"\n✅ BOTH FORMS WORK (no sandhi needed):")
    print(f"   Count: {len(results['both_pass'])}")
    
    print(f"\n{'='*80}")
    if results['sandhi_fixes']:
        success_rate = len(results['sandhi_fixes']) / max(1, len(results['merged_fail_split_pass'])) * 100
        print(f"🎯 SANDHI RESOLUTION SUCCESS RATE: {success_rate:.1f}%")
        print(f"   ({len(results['sandhi_fixes'])}/{len(results['merged_fail_split_pass'])} critical cases fixed)")
    else:
        print("⚠️  Need better test cases to demonstrate sandhi value")
    
    return results

if __name__ == '__main__':
    results = test_realistic_sandhi()
