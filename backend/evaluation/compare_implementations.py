#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to compare current implementation vs IITK implementation
Using patterns from tests_lg.json
"""

import os
import sys
import json
from collections import defaultdict

# Add paths for both implementations
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.join(project_root, 'repos', 'chanda'))

# Import both implementations
from core.chanda import Chanda as CurrentChanda
# Import IITK implementation with alias
import importlib.util
iitk_spec = importlib.util.spec_from_file_location(
    "iitk_chanda", 
    os.path.join(project_root, 'repos', 'chanda', 'chanda.py')
)
iitk_module = importlib.util.module_from_spec(iitk_spec)
iitk_spec.loader.exec_module(iitk_module)
IITKChanda = iitk_module.Chanda

# Data paths
current_data_path = os.path.join(backend_dir, 'data')
iitk_data_path = os.path.join(project_root, 'repos', 'chanda', 'data')

# Load test patterns
test_file = os.path.join(current_dir, 'tests_lg.json')
with open(test_file, 'r', encoding='utf-8') as f:
    test_patterns = json.load(f)

def normalize_pattern(pattern):
    """Normalize pattern by removing separators and spaces"""
    return pattern.replace('|', '').replace(' ', '').replace('.', '')

def pattern_to_lg(pattern):
    """Convert pattern with separators to clean L-G string"""
    clean = normalize_pattern(pattern)
    # Filter only L and G characters
    return ''.join(c for c in clean if c in 'LG')

def find_meter_in_chanda(chanda_instance, lg_pattern, meter_name):
    """
    Check if a meter with the given L-G pattern exists in the chanda dictionary
    Returns: (found_exact, found_names, matched_pattern)
    """
    found_names = []
    matched_pattern = None
    
    # Check in CHANDA dictionary
    if lg_pattern in chanda_instance.CHANDA:
        found_names = [name for name, _ in chanda_instance.CHANDA[lg_pattern]]
        matched_pattern = lg_pattern
    
    # Try with last syllable as Guru (common variant)
    if not found_names and lg_pattern and lg_pattern[-1] == 'L':
        lg_pattern_guru = lg_pattern[:-1] + 'G'
        if lg_pattern_guru in chanda_instance.CHANDA:
            found_names = [name for name, _ in chanda_instance.CHANDA[lg_pattern_guru]]
            matched_pattern = lg_pattern_guru
    
    # Check SINGLE_CHANDA
    if not found_names:
        if lg_pattern in chanda_instance.SINGLE_CHANDA:
            found_names = [name for name, _ in chanda_instance.SINGLE_CHANDA[lg_pattern]]
            matched_pattern = lg_pattern
    
    # Check MULTI_CHANDA
    if not found_names:
        if lg_pattern in chanda_instance.MULTI_CHANDA:
            found_names = [name for name, _ in chanda_instance.MULTI_CHANDA[lg_pattern]]
            matched_pattern = lg_pattern
    
    return bool(found_names), found_names, matched_pattern

def normalize_meter_name(name):
    """Normalize meter name for comparison"""
    # Remove diacritics and make lowercase
    name = name.lower()
    # Common transliteration variants
    replacements = {
        'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṛ': 'r', 'ṝ': 'r',
        'ṅ': 'n', 'ñ': 'n', 'ṭ': 't', 'ḍ': 'd', 'ṇ': 'n',
        'ś': 's', 'ṣ': 's', 'ḥ': 'h', 'ṃ': 'm', 'ḷ': 'l',
        'ḻ': 'l', 'kṣ': 'ksh', 'jñ': 'gn'
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name

def name_matches(expected_name, found_names):
    """Check if expected name matches any found name"""
    expected_norm = normalize_meter_name(expected_name)
    for found in found_names:
        found_norm = normalize_meter_name(found)
        if expected_norm in found_norm or found_norm in expected_norm:
            return True
    return False

def run_comparison():
    """Run comparison between current and IITK implementations"""
    print("=" * 80)
    print("COMPARISON: Current Implementation vs IITK Implementation")
    print("Using patterns from tests_lg.json")
    print("=" * 80)
    
    # Initialize both implementations
    print("\nInitializing implementations...")
    try:
        current_chanda = CurrentChanda(current_data_path)
        print(f"  ✓ Current implementation loaded (data: {current_data_path})")
    except Exception as e:
        print(f"  ✗ Current implementation failed: {e}")
        return
    
    try:
        iitk_chanda = IITKChanda(iitk_data_path)
        print(f"  ✓ IITK implementation loaded (data: {iitk_data_path})")
    except Exception as e:
        print(f"  ✗ IITK implementation failed: {e}")
        return
    
    # Database statistics
    print("\n" + "-" * 80)
    print("DATABASE STATISTICS")
    print("-" * 80)
    print(f"\nCurrent Implementation:")
    print(f"  Total CHANDA entries: {len(current_chanda.CHANDA)}")
    print(f"  SINGLE_CHANDA entries: {len(current_chanda.SINGLE_CHANDA)}")
    print(f"  MULTI_CHANDA entries: {len(current_chanda.MULTI_CHANDA)}")
    print(f"  JAATI entries: {len(current_chanda.JAATI)}")
    if hasattr(current_chanda, 'MATRA'):
        print(f"  MATRA entries: {len(current_chanda.MATRA)}")
    
    print(f"\nIITK Implementation:")
    print(f"  Total CHANDA entries: {len(iitk_chanda.CHANDA)}")
    print(f"  SINGLE_CHANDA entries: {len(iitk_chanda.SINGLE_CHANDA)}")
    print(f"  MULTI_CHANDA entries: {len(iitk_chanda.MULTI_CHANDA)}")
    print(f"  JAATI entries: {len(iitk_chanda.JAATI)}")
    
    # Test results
    results = {
        'current': {'exact': 0, 'name_match': 0, 'pattern_only': 0, 'not_found': 0},
        'iitk': {'exact': 0, 'name_match': 0, 'pattern_only': 0, 'not_found': 0}
    }
    
    detailed_results = []
    
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    
    total_tests = 0
    
    for test in test_patterns:
        meter_name = test['name']
        patterns = test.get('pattern', [])
        counts = test.get('counts', None)
        
        # Skip meters without patterns (like āryā which uses counts)
        if not patterns or all(not pattern_to_lg(p) for p in patterns):
            continue
        
        for pattern in patterns:
            lg_pattern = pattern_to_lg(pattern)
            if not lg_pattern:
                continue
            
            total_tests += 1
            
            # Test current implementation
            curr_found, curr_names, curr_matched = find_meter_in_chanda(
                current_chanda, lg_pattern, meter_name
            )
            
            # Test IITK implementation
            iitk_found, iitk_names, iitk_matched = find_meter_in_chanda(
                iitk_chanda, lg_pattern, meter_name
            )
            
            # Categorize results
            curr_status = 'not_found'
            iitk_status = 'not_found'
            
            if curr_found:
                if name_matches(meter_name, curr_names):
                    curr_status = 'exact'
                    results['current']['exact'] += 1
                else:
                    curr_status = 'pattern_only'
                    results['current']['pattern_only'] += 1
            else:
                results['current']['not_found'] += 1
            
            if iitk_found:
                if name_matches(meter_name, iitk_names):
                    iitk_status = 'exact'
                    results['iitk']['exact'] += 1
                else:
                    iitk_status = 'pattern_only'
                    results['iitk']['pattern_only'] += 1
            else:
                results['iitk']['not_found'] += 1
            
            detailed_results.append({
                'meter': meter_name,
                'pattern': pattern,
                'lg_pattern': lg_pattern,
                'current': {'found': curr_found, 'names': curr_names, 'status': curr_status},
                'iitk': {'found': iitk_found, 'names': iitk_names, 'status': iitk_status}
            })
    
    # Print detailed results
    print(f"\n{'Meter Name':<25} {'Pattern':<20} {'Current':<15} {'IITK':<15}")
    print("-" * 80)
    
    for result in detailed_results:
        curr_icon = '✓' if result['current']['found'] else '✗'
        iitk_icon = '✓' if result['iitk']['found'] else '✗'
        
        curr_text = f"{curr_icon} {result['current']['status']}"
        iitk_text = f"{iitk_icon} {result['iitk']['status']}"
        
        # Truncate pattern for display
        pattern_display = result['pattern'][:18] + '..' if len(result['pattern']) > 20 else result['pattern']
        
        print(f"{result['meter']:<25} {pattern_display:<20} {curr_text:<15} {iitk_text:<15}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal test patterns: {total_tests}")
    
    print(f"\n{'Metric':<30} {'Current':<15} {'IITK':<15}")
    print("-" * 60)
    print(f"{'Exact Match (name + pattern)':<30} {results['current']['exact']:<15} {results['iitk']['exact']:<15}")
    print(f"{'Pattern Found (diff name)':<30} {results['current']['pattern_only']:<15} {results['iitk']['pattern_only']:<15}")
    print(f"{'Not Found':<30} {results['current']['not_found']:<15} {results['iitk']['not_found']:<15}")
    
    curr_total_found = results['current']['exact'] + results['current']['pattern_only']
    iitk_total_found = results['iitk']['exact'] + results['iitk']['pattern_only']
    
    print("-" * 60)
    print(f"{'Total Found':<30} {curr_total_found:<15} {iitk_total_found:<15}")
    
    curr_rate = (curr_total_found / total_tests * 100) if total_tests > 0 else 0
    iitk_rate = (iitk_total_found / total_tests * 100) if total_tests > 0 else 0
    
    print(f"{'Success Rate':<30} {curr_rate:.1f}%{'':<8} {iitk_rate:.1f}%{'':<8}")
    
    # Show differences
    print("\n" + "-" * 80)
    print("DIFFERENCES (Found in one but not other)")
    print("-" * 80)
    
    only_current = [r for r in detailed_results if r['current']['found'] and not r['iitk']['found']]
    only_iitk = [r for r in detailed_results if r['iitk']['found'] and not r['current']['found']]
    
    if only_current:
        print(f"\nFound ONLY in Current ({len(only_current)}):")
        for r in only_current:
            print(f"  - {r['meter']}: {r['lg_pattern'][:30]}...")
            if r['current']['names']:
                print(f"    Names: {', '.join(r['current']['names'][:3])}")
    
    if only_iitk:
        print(f"\nFound ONLY in IITK ({len(only_iitk)}):")
        for r in only_iitk:
            print(f"  - {r['meter']}: {r['lg_pattern'][:30]}...")
            if r['iitk']['names']:
                print(f"    Names: {', '.join(r['iitk']['names'][:3])}")
    
    if not only_current and not only_iitk:
        print("\nNo differences - both implementations have identical coverage!")
    
    # Show not found in both
    not_found_both = [r for r in detailed_results if not r['current']['found'] and not r['iitk']['found']]
    if not_found_both:
        print(f"\nNot found in BOTH implementations ({len(not_found_both)}):")
        for r in not_found_both:
            print(f"  - {r['meter']}: {r['lg_pattern'][:40]}...")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    return results, detailed_results

if __name__ == "__main__":
    run_comparison()
