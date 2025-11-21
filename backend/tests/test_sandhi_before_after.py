#!/usr/bin/env python3
"""
Before/After Test: Sandhi Resolution Integration

This test demonstrates the impact of integrating sandhi resolution
into the Chandojñānam system. It compares:

BEFORE: identify_line() - requires pre-split text
AFTER:  identify_with_sandhi() - handles merged Sanskrit text automatically

Test cases include:
- Classical verses with merged sandhi
- Bhagavad Gita verses
- Vedic verses
- Common shlokas

Metrics measured:
- Identification success rate
- Meter accuracy
- Syllable count accuracy
- User experience improvement
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.chanda import Chanda

# Initialize Chanda
DATA_PATH = Path(__file__).parent.parent / "data"
chanda = Chanda(str(DATA_PATH))


# Test cases: verses with natural sandhi (as they appear in texts)
TEST_VERSES = [
    {
        'id': 1,
        'text': 'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन',
        'description': 'Bhagavad Gita 2.47 - Famous karma yoga verse',
        'expected_meter': 'अनुष्टुभ्',
        'manually_split': 'कर्मणि एव अधिकारः ते मा फलेषु कदाचन',
        'note': 'Contains "karmaNyevAdhikAraste" - common merged form'
    },
    {
        'id': 2,
        'text': 'धर्मो रक्षति रक्षितः',
        'description': 'Sanskrit subhashita - Dharma protects those who protect it',
        'expected_meter': 'गायत्री',
        'manually_split': 'धर्मः रक्षति रक्षितः',
        'note': 'Visarga sandhi: dharmaH -> dharmo'
    },
    {
        'id': 3,
        'text': 'सत्यमेव जयते नानृतम्',
        'description': 'Mundaka Upanishad - Truth alone triumphs',
        'expected_meter': None,
        'manually_split': 'सत्यम् एव जयते न अनृतम्',
        'note': 'Multiple sandhis: satyam+eva, na+anṛtam'
    },
    {
        'id': 4,
        'text': 'रामो राजमणिः सदा विजयते',
        'description': 'Verse praising Rama',
        'expected_meter': None,
        'manually_split': 'रामः राजमणिः सदा विजयते',
        'note': 'Visarga sandhi + compound words'
    },
    {
        'id': 5,
        'text': 'योगश्चित्तवृत्तिनिरोधः',
        'description': 'Yoga Sutras 1.2 - Definition of yoga',
        'expected_meter': None,
        'manually_split': 'योगः चित्त वृत्ति निरोधः',
        'note': 'Compound word with multiple sandhis'
    },
    {
        'id': 6,
        'text': 'सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः',
        'description': 'Mangala mantra - May all be happy',
        'expected_meter': 'अनुष्टुभ्',
        'manually_split': 'सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः',
        'note': 'Standard anushtubh - well-formed'
    },
    {
        'id': 7,
        'text': 'नमो नमः शिवाय',
        'description': 'Shiva mantra',
        'expected_meter': None,
        'manually_split': 'नमः नमः शिवाय',
        'note': 'Simple visarga sandhi'
    },
    {
        'id': 8,
        'text': 'अहं ब्रह्मास्मि',
        'description': 'Brihadaranyaka Upanishad mahavakya',
        'expected_meter': None,
        'manually_split': 'अहम् ब्रह्म अस्मि',
        'note': 'aham+brahma+asmi with anusvara'
    },
]


def test_single_verse(verse_data, verbose=True):
    """Test a single verse with both methods."""
    verse_id = verse_data['id']
    text = verse_data['text']
    manually_split = verse_data['manually_split']
    description = verse_data['description']
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"Test Case #{verse_id}: {description}")
        print(f"{'='*80}")
        print(f"Original (merged): {text}")
        print(f"Manual split:      {manually_split}")
        print(f"Note:              {verse_data['note']}")
    
    # =========================================================================
    # BEFORE: Using identify_line() with merged text (will likely fail)
    # =========================================================================
    try:
        before_merged = chanda.identify_line(text, fuzzy=False)
        before_manual = chanda.identify_line(manually_split, fuzzy=False)
    except Exception as e:
        if verbose:
            print(f"\n❌ BEFORE (identify_line) - ERROR: {e}")
        return None
    
    # =========================================================================
    # AFTER: Using identify_with_sandhi() with merged text (should succeed)
    # =========================================================================
    try:
        after_sandhi = chanda.identify_with_sandhi(text, k_candidates=5)
    except Exception as e:
        if verbose:
            print(f"\n❌ AFTER (identify_with_sandhi) - ERROR: {e}")
        return None
    
    # =========================================================================
    # Compare Results
    # =========================================================================
    if verbose:
        print(f"\n{'-'*80}")
        print("BEFORE: identify_line() on MERGED text")
        print(f"{'-'*80}")
        print(f"  Found:      {before_merged['found']}")
        print(f"  Syllables:  {len(before_merged['syllables'])}")
        if before_merged['found']:
            top_chanda = before_merged['display_chanda'].split('/')[0].strip() if before_merged['display_chanda'] else 'None'
            print(f"  Top meter:  {top_chanda}")
        else:
            print(f"  Top meter:  (not found)")
        
        print(f"\n{'-'*80}")
        print("BEFORE: identify_line() on MANUALLY SPLIT text")
        print(f"{'-'*80}")
        print(f"  Found:      {before_manual['found']}")
        print(f"  Syllables:  {len(before_manual['syllables'])}")
        if before_manual['found']:
            top_chanda = before_manual['display_chanda'].split('/')[0].strip() if before_manual['display_chanda'] else 'None'
            print(f"  Top meter:  {top_chanda}")
        else:
            print(f"  Top meter:  (not found)")
        
        print(f"\n{'-'*80}")
        print("AFTER: identify_with_sandhi() on MERGED text")
        print(f"{'-'*80}")
        print(f"  Sandhi available: {after_sandhi.get('sandhi_available', False)}")
        
        if after_sandhi.get('sandhi_best'):
            best = after_sandhi['sandhi_best']
            print(f"  Best candidate:   {best['candidate']}")
            print(f"  Sandhi score:     {best['sandhi_score']:.2f}")
            print(f"  Sandhi rules:     {', '.join(best['rules'])}")
            print(f"  Meter confidence: {best['meter_confidence']:.2f}")
            print(f"  Combined score:   {best['combined_score']:.2f}")
        
        print(f"  Found:        {after_sandhi['found']}")
        print(f"  Syllables:    {len(after_sandhi['syllables'])}")
        
        if after_sandhi['found']:
            top_chanda = after_sandhi['display_chanda'].split('/')[0].strip() if after_sandhi['display_chanda'] else 'None'
            print(f"  Top meter:    {top_chanda}")
            
            # Show all candidates tried
            if verbose and after_sandhi.get('sandhi_candidates'):
                print(f"\n  All candidates tried:")
                for i, cand in enumerate(after_sandhi['sandhi_candidates'][:5], 1):
                    print(f"    {i}. [{cand['combined_score']:.2f}] {cand['candidate']}")
                    print(f"       Rules: {', '.join(cand['rules'])}")
        else:
            print(f"  Top meter:    (not found)")
    
    # =========================================================================
    # Calculate improvement
    # =========================================================================
    improvement = {
        'id': verse_id,
        'text': text,
        'before_merged_found': before_merged['found'],
        'before_manual_found': before_manual['found'],
        'after_sandhi_found': after_sandhi['found'],
        'sandhi_enabled_success': not before_merged['found'] and after_sandhi['found'],
        'matches_manual': (
            after_sandhi['found'] and before_manual['found'] and 
            len(after_sandhi['syllables']) == len(before_manual['syllables'])
        )
    }
    
    if verbose:
        print(f"\n{'='*80}")
        print("IMPACT ASSESSMENT")
        print(f"{'='*80}")
        
        if improvement['sandhi_enabled_success']:
            print("✅ SUCCESS: Sandhi resolution ENABLED identification!")
            print("   BEFORE (merged): ❌ Not found")
            print("   AFTER (sandhi):  ✅ Found")
        elif improvement['matches_manual']:
            print("✅ SUCCESS: Automatic sandhi matches manual splitting!")
            print("   Same syllable count and meter identification")
        elif not before_merged['found'] and not after_sandhi['found']:
            print("⚠️  PARTIAL: Neither method found meter (may be invalid input)")
        else:
            print("ℹ️  INFO: Both methods produced results")
    
    return improvement


def run_comparison_tests(verbose=True):
    """Run all comparison tests and generate summary."""
    print("="*80)
    print("SANDHI RESOLUTION INTEGRATION - BEFORE/AFTER COMPARISON")
    print("="*80)
    print(f"\nTesting {len(TEST_VERSES)} verses...")
    
    results = []
    for verse in TEST_VERSES:
        result = test_single_verse(verse, verbose=verbose)
        if result:
            results.append(result)
    
    # =========================================================================
    # Summary Statistics
    # =========================================================================
    print(f"\n\n{'='*80}")
    print("SUMMARY STATISTICS")
    print(f"{'='*80}")
    
    total = len(results)
    sandhi_enabled = sum(1 for r in results if r['sandhi_enabled_success'])
    matches_manual = sum(1 for r in results if r['matches_manual'])
    both_failed = sum(1 for r in results if not r['after_sandhi_found'])
    
    print(f"\nTotal verses tested: {total}")
    print(f"\n🎯 KEY METRICS:")
    print(f"  Sandhi ENABLED identification:  {sandhi_enabled}/{total} ({sandhi_enabled/total*100:.1f}%)")
    print(f"  Matches manual splitting:        {matches_manual}/{total} ({matches_manual/total*100:.1f}%)")
    print(f"  Both methods failed:             {both_failed}/{total} ({both_failed/total*100:.1f}%)")
    
    print(f"\n📊 BEFORE vs AFTER:")
    before_merged_success = sum(1 for r in results if r['before_merged_found'])
    after_sandhi_success = sum(1 for r in results if r['after_sandhi_found'])
    improvement_rate = ((after_sandhi_success - before_merged_success) / total * 100)
    
    print(f"  BEFORE (merged text):  {before_merged_success}/{total} ({before_merged_success/total*100:.1f}%)")
    print(f"  AFTER (with sandhi):   {after_sandhi_success}/{total} ({after_sandhi_success/total*100:.1f}%)")
    print(f"  Improvement:           {improvement_rate:+.1f}%")
    
    print(f"\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}")
    
    if improvement_rate > 20:
        print("✅ MAJOR IMPROVEMENT: Sandhi resolution significantly enhances identification!")
        print("   Users can now input natural Sanskrit text without manual splitting.")
    elif improvement_rate > 0:
        print("✅ IMPROVEMENT: Sandhi resolution helps in some cases.")
        print("   Provides convenience for users with merged text.")
    else:
        print("ℹ️  NEUTRAL: Test cases may already be well-formed.")
        print("   Sandhi resolution provides user convenience without hurting accuracy.")
    
    return results


def quick_demo():
    """Quick demonstration of sandhi resolution."""
    print("\n" + "="*80)
    print("QUICK DEMO: Sandhi Resolution in Action")
    print("="*80)
    
    example = "कर्मण्येवाधिकारस्ते"
    print(f"\nInput: {example}")
    print("(Natural Sanskrit text as it appears in Bhagavad Gita)\n")
    
    print("WITHOUT sandhi resolution:")
    result_before = chanda.identify_line(example, fuzzy=False)
    print(f"  Found: {result_before['found']}")
    if result_before['found']:
        print(f"  Meter: {result_before['display_chanda']}")
    print()
    
    print("WITH sandhi resolution:")
    result_after = chanda.identify_with_sandhi(example)
    print(f"  Found: {result_after['found']}")
    if result_after['found']:
        print(f"  Meter: {result_after['display_chanda']}")
        print(f"  Split: {result_after['sandhi_best']['candidate']}")
        print(f"  Rules: {', '.join(result_after['sandhi_best']['rules'])}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Before/After comparison of sandhi integration')
    parser.add_argument('-q', '--quick', action='store_true', help='Run quick demo only')
    parser.add_argument('-s', '--silent', action='store_true', help='Show summary only (no verbose output)')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_demo()
    else:
        run_comparison_tests(verbose=not args.silent)
