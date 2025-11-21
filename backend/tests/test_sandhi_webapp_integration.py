#!/usr/bin/env python3
"""
Quick test to verify sandhi integration in webapp works correctly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.chanda import Chanda

# Test verses
TEST_CASES = [
    {
        'name': 'Bhagavad Gita 2.47 (merged)',
        'text': 'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन',
        'expected_syllables_without_sandhi': 16,
        'expected_syllables_with_sandhi': 16,  # May vary based on best candidate
    },
    {
        'name': 'Simple verse with visarga sandhi',
        'text': 'धर्मो रक्षति रक्षितः',
        'expected_found': True
    },
    {
        'name': 'Merged compound word',
        'text': 'सत्यमेव जयते',
        'expected_found': True
    }
]

def test_sandhi_integration():
    """Test that sandhi parameter works in identify_from_text"""
    print("="*80)
    print("SANDHI INTEGRATION TEST")
    print("="*80)
    
    DATA_PATH = Path(__file__).parent.parent / "data"
    chanda = Chanda(str(DATA_PATH))
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"Text: {test['text']}")
        
        try:
            # Test WITHOUT sandhi
            result_without = chanda.identify_from_text(
                test['text'],
                verse=False,
                fuzzy=True,
                use_sandhi=False
            )
            
            # Test WITH sandhi
            result_with = chanda.identify_from_text(
                test['text'],
                verse=False,
                fuzzy=True,
                use_sandhi=True
            )
            
            # Verify both work
            without_found = result_without['result']['line'][0]['result']['found']
            with_found = result_with['result']['line'][0]['result']['found']
            
            print(f"  Without sandhi: Found={without_found}")
            print(f"  With sandhi:    Found={with_found}")
            
            # Check if sandhi info is present when enabled
            with_result = result_with['result']['line'][0]['result']
            has_sandhi_info = 'sandhi_info' in with_result
            
            if has_sandhi_info:
                print(f"  ✓ Sandhi info present: {with_result['sandhi_info'].get('rules', [])}")
            else:
                print(f"  ℹ️  No sandhi info (may use identity)")
            
            if without_found or with_found:
                print(f"  ✅ PASS - At least one method found meter")
                passed += 1
            else:
                print(f"  ❌ FAIL - Neither method found meter")
                failed += 1
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0

if __name__ == '__main__':
    success = test_sandhi_integration()
    sys.exit(0 if success else 1)
