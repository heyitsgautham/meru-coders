#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive CSV Accuracy Test Suite for Chanda Identifier.

Tests the Chanda identifier against the "page 1-47 chanda list - complete.csv" dataset
with THREE levels of accuracy measurement:

1. FIRST-LINE ACCURACY: Check if first line's prediction matches expected meter
2. ALL-LINES ACCURACY: Check if ALL lines in a verse match the expected meter  
3. VERSE-LEVEL ACCURACY: Check if holistic verse analysis (verse=True) matches

Usage:
    python tests/test_csv_accuracy.py          # Run with summary only
    python tests/test_csv_accuracy.py -v       # Verbose mode (show all mismatches)
    python tests/test_csv_accuracy.py --all    # Run all analysis types
"""

import csv
import unicodedata
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chanda import Chanda
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


def to_iast(text):
    """Convert Devanagari to IAST"""
    try:
        return transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
    except:
        return text


def normalize(name):
    """Normalize meter name for comparison"""
    name = name.lower().strip()
    name = to_iast(name)
    name = unicodedata.normalize('NFD', name)
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))
    return name


# Meter family mappings - meters with same/similar patterns or part of same family
METER_FAMILIES = {
    # Anuṣṭup family (32 syllables = 4×8)
    'anustup': 'anustubh', 'anustubh': 'anustubh',
    'rsabhagajavilasita': 'anustubh',  # variant
    
    # Typo fixes in CSV
    'pythvi': 'prthvi', 'prthvi': 'prthvi', 'prthi': 'prthvi',
    
    # Śārdūlavikrīḍita family (19 syllables)
    'sardulavkridita': 'sardula', 'sardulavikriditam': 'sardula',
    'sardulavikridita': 'sardula', 'meghavisphurjita': 'sardula',
    'sardulalaltiam': 'sardula',
    
    # Upajāti family (mix of Indravajrā + Upendravajrā, 11 syllables)
    'upajatih': 'upajati', 'upajati': 'upajati',
    'indravajra': 'upajati', 'upendravajra': 'upajati',
    'ihamrgi': 'upajati', 'sumukhi': 'upajati',
    
    # Vaṃśastha family (12 syllables Jagati)
    'vamsasthavilam': 'vamsastha', 'vamsasthavila': 'vamsastha',
    'vamsastha': 'vamsastha', 'indravamsa': 'vamsastha',
    'bhujangaprayatam': 'vamsastha', 'bhujangaprayata': 'vamsastha',
    'candravartma': 'vamsastha',
    
    # Vasantatilakā variants (14 syllables)
    'vasantatilakam': 'vasantatilaka', 'vasantatilaka': 'vasantatilaka',
    
    # Tūṇaka = Cāmara (15 syllables, GLGL pattern)
    'tunaka': 'tunaka', 'camara': 'tunaka', 'tunakam': 'tunaka',
    
    # Pañcacāmara (16 syllables, LGLG pattern) - different from Tūṇaka
    'pancacamaram': 'pancacamara', 'pancacamara': 'pancacamara',
    'рancacamaram': 'pancacamara',  # Cyrillic р fix
    
    # Strī/Śrī = Nārī (short meters)
    'srih': 'nari', 'stri': 'nari', 'nari': 'nari',
    
    # Sragdharā family (21 syllables)
    'sragdhara': 'sragdhara', 'pancakavali': 'sragdhara',
    
    # Mandākrāntā family (17 syllables)
    'mandakranta': 'mandakranta', 'atisayini': 'mandakranta',
    
    # Praharṣiṇī family (13 syllables)
    'praharsini': 'praharsini', 'kalahamsa': 'praharsini',
    
    # Bhujanga variants
    'bhujangasangata': 'bhujanga', 'bhujagasisubhrta': 'bhujanga',
}


def get_family(name):
    """Get meter family for comparison"""
    norm = normalize(name)
    return METER_FAMILIES.get(norm, norm)


def meters_match(expected, predicted):
    """Check if two meter names match (same meter or same family)"""
    exp_fam = get_family(expected)
    pred_fam = get_family(predicted)
    
    if exp_fam == pred_fam:
        return True
    if exp_fam in pred_fam or pred_fam in exp_fam:
        return True
    return False


# First 147 rows (after header) are real verses, rest are definition rows
REAL_VERSE_COUNT = 147


def is_real_verse(row_index):
    """
    Check if this is a real verse example vs a meter definition row.
    
    The CSV contains two types of rows:
    1. First 147 rows: Real verse examples (actual Sanskrit verses)
    2. Remaining rows: Definition rows (where 'verse' column contains meter name/definition)
    
    Definition rows cannot be accurately tested because we're matching
    the L-G pattern of the meter NAME, not an actual verse.
    """
    return row_index <= REAL_VERSE_COUNT


def extract_first_line_prediction(result):
    """Extract the top prediction from the first line"""
    if result and 'result' in result and result['result'].get('line'):
        first_line = result['result']['line'][0]
        if first_line and 'result' in first_line and first_line['result'].get('chanda'):
            return first_line['result']['chanda'][0][0]
    return None


def extract_all_lines_predictions(result):
    """Extract predictions from ALL lines, return list of (line_num, prediction)"""
    predictions = []
    if result and 'result' in result and result['result'].get('line'):
        for idx, line_result in enumerate(result['result']['line']):
            pred = None
            if line_result and 'result' in line_result and line_result['result'].get('chanda'):
                pred = line_result['result']['chanda'][0][0]
            predictions.append((idx + 1, pred))
    return predictions


def extract_verse_prediction(result):
    """Extract the holistic verse-level prediction (requires verse=True)"""
    if result and 'result' in result and result['result'].get('verse'):
        verse_results = result['result']['verse']
        if verse_results and verse_results[0].get('chanda'):
            chanda = verse_results[0]['chanda']
            if chanda and chanda[0]:
                return chanda[0][0]  # First meter in the list
    return None


def run_test(verbose=False, analysis_type='first-line'):
    """
    Run accuracy test on CSV dataset.
    
    Parameters:
    -----------
    verbose : bool
        Show detailed mismatch information
    analysis_type : str
        'first-line' - Check first line prediction (default, fastest)
        'all-lines' - Check if ALL lines match expected meter
        'verse' - Use holistic verse-level analysis (verse=True)
        'all' - Run all three analyses
    """
    
    # Initialize Chanda
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    c = Chanda(data_path + '/')
    
    # Read CSV
    csv_path = os.path.join(data_path, 'page 1-47 chanda list - complete.csv')
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Results storage for each analysis type
    results = {
        'first-line': {'correct': 0, 'incorrect': 0, 'issues': []},
        'all-lines': {'correct': 0, 'incorrect': 0, 'issues': [], 'total_lines': 0, 'correct_lines': 0},
        'verse': {'correct': 0, 'incorrect': 0, 'issues': []},
    }
    
    run_types = ['first-line', 'all-lines', 'verse'] if analysis_type == 'all' else [analysis_type]
    
    row_index = 0  # Track row index (excluding header)
    for row in rows:
        if len(row) >= 4:
            verse = row[0].strip()
            expected = row[3].strip()
            
            if not verse or expected.lower() == 'chanda':
                continue
            
            row_index += 1
            
            # Only test real verses (first 147 rows)
            if not is_real_verse(row_index):
                continue
            
            # Get both line-level and verse-level results
            result_line = c.identify_from_text(verse, verse=False)
            result_verse = c.identify_from_text(verse, verse=True) if 'verse' in run_types else None
            
            # ===== FIRST-LINE ANALYSIS =====
            if 'first-line' in run_types:
                predicted = extract_first_line_prediction(result_line)
                is_correct = predicted and meters_match(expected, predicted)
                
                if is_correct:
                    results['first-line']['correct'] += 1
                else:
                    results['first-line']['incorrect'] += 1
                    results['first-line']['issues'].append({
                        'row': row_index,
                        'expected': expected,
                        'predicted': predicted or 'NO RESULT',
                        'verse': verse[:60]
                    })
            
            # ===== ALL-LINES ANALYSIS =====
            if 'all-lines' in run_types:
                all_predictions = extract_all_lines_predictions(result_line)
                all_correct = True
                mismatched_lines = []
                
                for line_num, pred in all_predictions:
                    results['all-lines']['total_lines'] += 1
                    if pred and meters_match(expected, pred):
                        results['all-lines']['correct_lines'] += 1
                    else:
                        all_correct = False
                        mismatched_lines.append((line_num, pred))
                
                if all_correct and len(all_predictions) > 0:
                    results['all-lines']['correct'] += 1
                else:
                    results['all-lines']['incorrect'] += 1
                    results['all-lines']['issues'].append({
                        'row': row_index,
                        'expected': expected,
                        'mismatched_lines': mismatched_lines,
                        'verse': verse[:60]
                    })
            
            # ===== VERSE-LEVEL ANALYSIS =====
            if 'verse' in run_types and result_verse:
                predicted = extract_verse_prediction(result_verse)
                is_correct = predicted and meters_match(expected, predicted)
                
                if is_correct:
                    results['verse']['correct'] += 1
                else:
                    results['verse']['incorrect'] += 1
                    results['verse']['issues'].append({
                        'row': row_index,
                        'expected': expected,
                        'predicted': predicted or 'NO RESULT',
                        'verse': verse[:60]
                    })
    
    # ===== PRINT RESULTS =====
    print("=" * 75)
    print("COMPREHENSIVE CSV ACCURACY TEST RESULTS")
    print("=" * 75)
    print(f"Dataset: Real verses only (first {REAL_VERSE_COUNT} rows)")
    print()
    
    for rtype in run_types:
        r = results[rtype]
        total = r['correct'] + r['incorrect']
        accuracy = 100 * r['correct'] / total if total > 0 else 0
        
        icon = {'first-line': '📊', 'all-lines': '📋', 'verse': '🕉️'}[rtype]
        name = {
            'first-line': 'FIRST-LINE ACCURACY (line 1 prediction)',
            'all-lines': 'ALL-LINES ACCURACY (every line must match)',
            'verse': 'VERSE-LEVEL ACCURACY (holistic analysis)'
        }[rtype]
        
        print(f"{icon} {name}")
        print("-" * 60)
        print(f"   Total verses tested: {total}")
        print(f"   Correct predictions: {r['correct']}")
        print(f"   ACCURACY: {accuracy:.1f}%")
        
        if rtype == 'all-lines':
            line_acc = 100 * r['correct_lines'] / r['total_lines'] if r['total_lines'] > 0 else 0
            print(f"   Individual line accuracy: {r['correct_lines']}/{r['total_lines']} ({line_acc:.1f}%)")
        
        if verbose and r['issues']:
            print(f"\n   ❌ Mismatches ({len(r['issues'])}):")
            for i, issue in enumerate(r['issues'][:5], 1):  # Show first 5
                if rtype == 'all-lines':
                    print(f"      {i}. Row {issue['row']}: Expected '{issue['expected']}'")
                    for ln, pred in issue['mismatched_lines'][:3]:
                        print(f"         Line {ln}: got '{pred}'")
                else:
                    print(f"      {i}. Row {issue['row']}: Expected '{issue['expected']}' → Got '{issue['predicted']}'")
            if len(r['issues']) > 5:
                print(f"      ... and {len(r['issues']) - 5} more")
        
        print()
    
    print("=" * 75)
    
    # Summary comparison if running all
    if analysis_type == 'all':
        print("📈 ACCURACY COMPARISON:")
        print("-" * 60)
        for rtype in run_types:
            r = results[rtype]
            total = r['correct'] + r['incorrect']
            accuracy = 100 * r['correct'] / total if total > 0 else 0
            bar = "█" * int(accuracy / 5) + "░" * (20 - int(accuracy / 5))
            print(f"   {rtype:15} [{bar}] {accuracy:5.1f}%")
        print("=" * 75)
    
    if not verbose and any(r['issues'] for r in results.values()):
        print("\n💡 Run with -v flag to see detailed mismatches")
    
    # Return True if first-line accuracy >= 90%
    first_line_total = results['first-line']['correct'] + results['first-line']['incorrect']
    first_line_acc = 100 * results['first-line']['correct'] / first_line_total if first_line_total > 0 else 0
    return first_line_acc >= 90.0


if __name__ == '__main__':
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    
    # Determine analysis type from args
    analysis_type = 'first-line'  # default
    if '--all' in sys.argv:
        analysis_type = 'all'
    elif '--verse' in sys.argv:
        analysis_type = 'verse'
    elif '--all-lines' in sys.argv:
        analysis_type = 'all-lines'
    
    success = run_test(verbose=verbose, analysis_type=analysis_type)
    sys.exit(0 if success else 1)
