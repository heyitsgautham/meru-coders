#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparison test: Sanskrit Repo Algorithm vs Our Chanda System

Tests the sanskrit-coders repository's identification algorithm against:
1. test_csv_accuracy.py dataset (147 real verses)
2. test_rigveda_validation.py dataset (Rigveda corpus)

This allows us to benchmark their approach vs ours.
"""

import csv
import sys
import os
from collections import defaultdict

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sanskrit_repo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'repos/sanskrit')
sys.path.insert(0, sanskrit_repo_path)

# Import our system
from core import Chanda
from config import settings

# Import sanskrit repo components
try:
    # Change to sanskrit repo directory for data file access
    original_cwd = os.getcwd()
    os.chdir(sanskrit_repo_path)
    
    from identify.identifier import Identifier
    from data import metrical_data
    import scan
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
    
    # Return to original directory
    os.chdir(original_cwd)
    
    SANSKRIT_REPO_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Cannot import sanskrit repo: {e}")
    if 'original_cwd' in locals():
        os.chdir(original_cwd)
    SANSKRIT_REPO_AVAILABLE = False


def to_slp1(text):
    """Convert text to SLP1 for sanskrit repo processing"""
    try:
        # Try to detect and convert
        from indic_transliteration.detect import detect
        script = detect(text)
        if script:
            return transliterate(text, script, sanscript.SLP1)
        return text
    except:
        return text


def normalize_meter_name(name):
    """Normalize meter names for comparison"""
    if not name:
        return ""
    
    # Convert to IAST if needed
    try:
        from indic_transliteration.detect import detect
        script = detect(name)
        if script == sanscript.DEVANAGARI:
            name = transliterate(name, sanscript.DEVANAGARI, sanscript.IAST)
    except:
        pass
    
    # Normalize
    name = name.lower().strip()
    name = name.replace('ṣ', 's').replace('ṭ', 't').replace('ṇ', 'n')
    name = name.replace('ī', 'i').replace('ā', 'a').replace('ū', 'u')
    name = name.replace('ṛ', 'r').replace('ṅ', 'n').replace('ḥ', 'h')
    name = name.replace('ṁ', 'm').replace('ṃ', 'm')
    
    # Common equivalences
    equivalences = {
        'anustup': 'anustubh',
        'sloka': 'anustubh',
        'tristup': 'tristubh',
        'tristubh': 'tristubh',
    }
    
    return equivalences.get(name, name)


def identify_with_sanskrit_repo(text, identifier):
    """
    Use sanskrit repo to identify meter from text.
    
    Returns: (meter_name, confidence_type) or (None, None)
    """
    if not SANSKRIT_REPO_AVAILABLE or not identifier:
        return None, None
    
    try:
        # Convert to SLP1
        slp1_text = to_slp1(text)
        
        # Split into lines (simple split by common delimiters)
        lines = []
        for line in slp1_text.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)
        
        if not lines:
            return None, None
        
        # Scan to get L-G patterns
        try:
            lg_patterns = scan.ScanVerse(lines)
        except Exception as e:
            # If scanning fails, try as single line
            try:
                lg_patterns = [scan._ScanVowelInitialLine(slp1_text, True)]
            except:
                return None, None
        
        # Identify using patterns
        results = identifier.IdentifyFromPatternLines(lg_patterns, input_type='full')
        
        # Extract best match (prefer exact over partial over accidental)
        for match_type in ['exact', 'partial', 'accidental']:
            if match_type in results and results[match_type]:
                meter_name = list(results[match_type].keys())[0]
                return meter_name, match_type
        
        return None, None
        
    except Exception as e:
        print(f"  Error in sanskrit repo identification: {e}")
        return None, None


def test_csv_accuracy_comparison(verbose=False):
    """
    Test both systems on the CSV dataset (147 real verses).
    """
    print("\n" + "=" * 75)
    print("📊 CSV ACCURACY COMPARISON (147 Real Verses)")
    print("=" * 75)
    
    # Initialize both systems
    our_chanda = Chanda(data_path=str(settings.DATA_DIR))
    
    sanskrit_identifier = None
    if SANSKRIT_REPO_AVAILABLE:
        # Change to sanskrit repo directory for data initialization
        original_cwd = os.getcwd()
        try:
            os.chdir(sanskrit_repo_path)
            metrical_data.InitializeData()
            sanskrit_identifier = Identifier(metrical_data)
            print("✓ Sanskrit repo system initialized")
        except Exception as e:
            print(f"✗ Failed to initialize sanskrit repo: {e}")
        finally:
            os.chdir(original_cwd)
    else:
        print("✗ Sanskrit repo not available")
    
    # Load CSV data
    csv_path = os.path.join(settings.DATA_DIR, 'page 1-47 chanda list - complete.csv')
    
    our_correct = 0
    their_correct = 0
    both_correct = 0
    our_only = 0
    their_only = 0
    both_wrong = 0
    total = 0
    
    mismatches = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Process first 147 real verses only
    row_index = 0
    for row in rows:
        if len(row) >= 4:
            verse = row[0].strip()
            expected = row[3].strip()
            
            if not verse or expected.lower() == 'chanda':
                continue
            
            row_index += 1
            if row_index > 147:  # Only test first 147 real verses
                break
            
            total += 1
            
            # Test our system
            our_result = our_chanda.identify_from_text(verse, verse=False)
            our_pred = None
            if our_result and 'result' in our_result and our_result['result'].get('line'):
                first_line = our_result['result']['line'][0]
                if first_line and 'result' in first_line and first_line['result'].get('chanda'):
                    our_pred = first_line['result']['chanda'][0][0]
            
            # Test sanskrit repo system
            their_pred, confidence = identify_with_sanskrit_repo(verse, sanskrit_identifier)
            
            # Normalize predictions
            expected_norm = normalize_meter_name(expected)
            our_pred_norm = normalize_meter_name(our_pred) if our_pred else None
            their_pred_norm = normalize_meter_name(their_pred) if their_pred else None
            
            # Check matches
            our_match = our_pred_norm and (expected_norm in our_pred_norm or our_pred_norm in expected_norm)
            their_match = their_pred_norm and (expected_norm in their_pred_norm or their_pred_norm in expected_norm)
            
            if our_match:
                our_correct += 1
            if their_match:
                their_correct += 1
            
            if our_match and their_match:
                both_correct += 1
            elif our_match and not their_match:
                our_only += 1
                if verbose:
                    mismatches.append(f"  ✓✗ Row {row_index}: Expected '{expected}' → Ours: '{our_pred}' | Theirs: '{their_pred}'")
            elif their_match and not our_match:
                their_only += 1
                if verbose:
                    mismatches.append(f"  ✗✓ Row {row_index}: Expected '{expected}' → Ours: '{our_pred}' | Theirs: '{their_pred}'")
            else:
                both_wrong += 1
                if verbose:
                    mismatches.append(f"  ✗✗ Row {row_index}: Expected '{expected}' → Ours: '{our_pred}' | Theirs: '{their_pred}'")
    
    # Print results
    print(f"\nTotal verses tested: {total}")
    print()
    print(f"{'System':<25} {'Correct':<10} {'Accuracy':<12}")
    print("-" * 75)
    
    our_acc = 100 * our_correct / total if total > 0 else 0
    their_acc = 100 * their_correct / total if total > 0 else 0
    
    print(f"{'Our Chanda System':<25} {our_correct:<10} {our_acc:>6.1f}%")
    if SANSKRIT_REPO_AVAILABLE:
        print(f"{'Sanskrit Repo System':<25} {their_correct:<10} {their_acc:>6.1f}%")
    else:
        print(f"{'Sanskrit Repo System':<25} {'N/A':<10} {'N/A':<12}")
    
    if SANSKRIT_REPO_AVAILABLE:
        print()
        print("Agreement Analysis:")
        print("-" * 75)
        print(f"  Both correct:        {both_correct:>6} ({100*both_correct/total:.1f}%)")
        print(f"  Only ours correct:   {our_only:>6} ({100*our_only/total:.1f}%)")
        print(f"  Only theirs correct: {their_only:>6} ({100*their_only/total:.1f}%)")
        print(f"  Both wrong:          {both_wrong:>6} ({100*both_wrong/total:.1f}%)")
        
        if verbose and mismatches:
            print("\nSample disagreements (first 10):")
            for mismatch in mismatches[:10]:
                print(mismatch)
    
    return our_acc, their_acc


def test_rigveda_comparison(verbose=False, limit=100):
    """
    Test both systems on Rigveda dataset (limited for performance).
    """
    print("\n" + "=" * 75)
    print(f"🕉️ RIGVEDA COMPARISON (first {limit} verses)")
    print("=" * 75)
    
    # Initialize systems
    our_chanda = Chanda(data_path=str(settings.DATA_DIR))
    
    sanskrit_identifier = None
    if SANSKRIT_REPO_AVAILABLE:
        original_cwd = os.getcwd()
        try:
            os.chdir(sanskrit_repo_path)
            if not hasattr(metrical_data, 'known_full_patterns') or not metrical_data.known_full_patterns:
                metrical_data.InitializeData()
            sanskrit_identifier = Identifier(metrical_data)
        except Exception as e:
            print(f"✗ Failed to initialize sanskrit repo: {e}")
        finally:
            os.chdir(original_cwd)
    
    # Load Rigveda dataset
    dataset_path = os.path.join(settings.DATA_DIR, 'rigveda_with_meters_complete.csv')
    
    if not os.path.exists(dataset_path):
        print("⚠️ Rigveda dataset not found")
        return None, None
    
    our_correct = 0
    their_correct = 0
    total = 0
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            
            verse_text = row.get('verse_text', '').strip()
            expected_meter = row.get('meter', '').strip()
            
            if not verse_text or not expected_meter:
                continue
            
            total += 1
            
            # Test our system (Vedic mode)
            our_result = our_chanda._identify_vedic_mode(verse_text)
            our_pred = our_result.get('meter')
            
            # Test sanskrit repo
            their_pred, _ = identify_with_sanskrit_repo(verse_text, sanskrit_identifier)
            
            # Normalize and check
            expected_norm = normalize_meter_name(expected_meter)
            our_pred_norm = normalize_meter_name(our_pred) if our_pred else None
            their_pred_norm = normalize_meter_name(their_pred) if their_pred else None
            
            if our_pred_norm and expected_norm in our_pred_norm:
                our_correct += 1
            if their_pred_norm and expected_norm in their_pred_norm:
                their_correct += 1
    
    # Print results
    print(f"\nTotal verses tested: {total}")
    print()
    print(f"{'System':<25} {'Correct':<10} {'Accuracy':<12}")
    print("-" * 75)
    
    our_acc = 100 * our_correct / total if total > 0 else 0
    their_acc = 100 * their_correct / total if total > 0 else 0
    
    print(f"{'Our Chanda System':<25} {our_correct:<10} {our_acc:>6.1f}%")
    if SANSKRIT_REPO_AVAILABLE:
        print(f"{'Sanskrit Repo System':<25} {their_correct:<10} {their_acc:>6.1f}%")
    else:
        print(f"{'Sanskrit Repo System':<25} {'N/A':<10} {'N/A':<12}")
    
    return our_acc, their_acc


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Compare sanskrit repo algorithm with ours')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--csv-only', action='store_true', help='Test only CSV dataset')
    parser.add_argument('--rigveda-only', action='store_true', help='Test only Rigveda dataset')
    parser.add_argument('--rigveda-limit', type=int, default=100, help='Limit Rigveda test size')
    args = parser.parse_args()
    
    if not SANSKRIT_REPO_AVAILABLE:
        print("\n" + "=" * 75)
        print("❌ SANSKRIT REPO NOT AVAILABLE")
        print("=" * 75)
        print("\nCannot run comparison test without sanskrit repo components.")
        print("The repo is attached but imports are failing.")
        print("\nPossible issues:")
        print("  1. Missing dependencies (slp1.py, etc.)")
        print("  2. Python 2 vs Python 3 compatibility issues")
        print("  3. Import path issues")
        return 1
    
    # Run tests
    if not args.rigveda_only:
        csv_ours, csv_theirs = test_csv_accuracy_comparison(verbose=args.verbose)
    
    if not args.csv_only:
        rv_ours, rv_theirs = test_rigveda_comparison(verbose=args.verbose, limit=args.rigveda_limit)
    
    # Summary
    print("\n" + "=" * 75)
    print("📈 SUMMARY")
    print("=" * 75)
    print("\nKey Findings:")
    print("  • Our system has been optimized for these specific datasets")
    print("  • Sanskrit repo uses a different approach (regex + pattern matching)")
    print("  • Both systems have strengths and weaknesses")
    print("  • Consider hybrid approach for best results")
    print("\n" + "=" * 75)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
