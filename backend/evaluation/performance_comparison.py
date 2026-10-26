#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Performance Comparison Test

Compares:
1. chanda_iitk.py (original IITK implementation) with small dataset against Rigveda validation
2. chanda_iitk.py with our large dataset against Rigveda validation
3. chanda_iitk.py with small dataset against CSV accuracy test
4. chanda_iitk.py with large dataset against CSV accuracy test
5. chanda.py (our implementation) with large dataset against Rigveda validation
6. chanda.py with large dataset against CSV accuracy test

@author: GitHub Copilot
@date: 2025-12-05
"""

import os
import sys

from backend.evaluation.performance_comparison_data import (
    LARGE_DATA_PATH,
    PAGE_CSV,
    RIGVEDA_CSV,
    ROOT_DIR,
    SMALL_DATA_PATH,
)
from backend.evaluation.performance_comparison_runs import (
    test_csv_with_iitk,
    test_csv_with_our_chanda,
    test_rigveda_with_iitk,
    test_rigveda_with_our_chanda,
)

# ============================================================================
# MAIN EXECUTION
# ============================================================================


def print_separator(char='=', length=70):
    print(char * length)


def print_results(title, results, test_type='rigveda'):
    """Print formatted results"""
    print(f"\n{title}")
    print_separator('-', len(title))

    if 'error' in results:
        print(f"  ❌ ERROR: {results['error']}")
        return

    if test_type == 'rigveda':
        print(f"  📊 Total verses tested:    {results['total']}")
        print(f"  ✅ Exact matches:          {results['exact_matches']} ({results['exact_accuracy']:.2f}%)")
        print(
            f"  🔶 Family matches:         {results['family_matches']} ({results['family_matches'] / results['total'] * 100:.2f}%)"
            if results['total'] > 0
            else ""
        )
        print(
            f"  ❌ Mismatches:             {results['mismatches']} ({results['mismatches'] / results['total'] * 100:.2f}%)"
            if results['total'] > 0
            else ""
        )
        print(f"  📈 EXACT ACCURACY:         {results['exact_accuracy']:.2f}%")
        print(f"  📈 FAMILY ACCURACY:        {results['family_accuracy']:.2f}%")
    else:  # csv
        print(f"  📊 Total verses tested:    {results['total']}")
        print(f"  ✅ Correct:                {results['correct']} ({results['accuracy']:.2f}%)")
        print(f"  ❌ Incorrect:              {results['incorrect']} ({100 - results['accuracy']:.2f}%)")
        print(f"  📈 ACCURACY:               {results['accuracy']:.2f}%")

    if 'time_seconds' in results:
        print(
            f"  ⏱️  Time:                   {results['time_seconds']:.2f}s ({results['time_per_verse_ms']:.2f}ms/verse)"
        )


def main():
    print_separator('=')
    print("🔬 COMPREHENSIVE PERFORMANCE COMPARISON")
    print("   Comparing chanda_iitk.py vs chanda.py implementations")
    print_separator('=')

    # Check if IITK implementation exists
    iitk_path = os.path.join(ROOT_DIR, 'reference', 'alternative_implementations', 'chanda_iitk.py')
    if not os.path.exists(iitk_path):
        print(f"❌ IITK implementation not found at: {iitk_path}")
        return 1

    # Import IITK Chanda
    import importlib.util

    spec = importlib.util.spec_from_file_location("chanda_iitk", iitk_path)
    chanda_iitk_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chanda_iitk_module)
    ChandaIITK = chanda_iitk_module.Chanda

    # Dataset info
    print("\n📁 Dataset Information:")
    print(f"   Small dataset (IITK original): {SMALL_DATA_PATH}")
    print(f"   Large dataset (Our enhanced):  {LARGE_DATA_PATH}")
    print(f"   Rigveda test file:             {RIGVEDA_CSV}")
    print(f"   CSV test file:                 {PAGE_CSV}")

    # Count meters in datasets
    small_count = 0
    large_count = 0
    for f in ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv']:
        small_file = os.path.join(SMALL_DATA_PATH, f)
        large_file = os.path.join(LARGE_DATA_PATH, f)
        if os.path.exists(small_file):
            small_count += sum(1 for _ in open(small_file)) - 1  # minus header
        if os.path.exists(large_file):
            large_count += sum(1 for _ in open(large_file)) - 1

    print(f"\n   Small dataset meter count:     ~{small_count} meters")
    print(f"   Large dataset meter count:     ~{large_count} meters")

    # Run all tests
    results = {}

    # 1. IITK + Small Dataset + Rigveda
    print_separator()
    print("\n🧪 Test 1: chanda_iitk.py + Small Dataset vs Rigveda Validation")
    results['iitk_small_rigveda'] = test_rigveda_with_iitk(ChandaIITK, SMALL_DATA_PATH, limit=1000)
    print_results("Results:", results['iitk_small_rigveda'], 'rigveda')

    # 2. IITK + Large Dataset + Rigveda
    print_separator()
    print("\n🧪 Test 2: chanda_iitk.py + Large Dataset vs Rigveda Validation")
    results['iitk_large_rigveda'] = test_rigveda_with_iitk(ChandaIITK, LARGE_DATA_PATH, limit=1000)
    print_results("Results:", results['iitk_large_rigveda'], 'rigveda')

    # 3. IITK + Small Dataset + CSV
    print_separator()
    print("\n🧪 Test 3: chanda_iitk.py + Small Dataset vs CSV Accuracy Test")
    results['iitk_small_csv'] = test_csv_with_iitk(ChandaIITK, SMALL_DATA_PATH)
    print_results("Results:", results['iitk_small_csv'], 'csv')

    # 4. IITK + Large Dataset + CSV
    print_separator()
    print("\n🧪 Test 4: chanda_iitk.py + Large Dataset vs CSV Accuracy Test")
    results['iitk_large_csv'] = test_csv_with_iitk(ChandaIITK, LARGE_DATA_PATH)
    print_results("Results:", results['iitk_large_csv'], 'csv')

    # 5. Our Chanda + Large Dataset + Rigveda
    print_separator()
    print("\n🧪 Test 5: chanda.py (Our) + Large Dataset vs Rigveda Validation")
    results['ours_large_rigveda'] = test_rigveda_with_our_chanda(limit=1000)
    print_results("Results:", results['ours_large_rigveda'], 'rigveda')

    # 6. Our Chanda + Large Dataset + CSV
    print_separator()
    print("\n🧪 Test 6: chanda.py (Our) + Large Dataset vs CSV Accuracy Test")
    results['ours_large_csv'] = test_csv_with_our_chanda()
    print_results("Results:", results['ours_large_csv'], 'csv')

    # Summary comparison
    print_separator('=')
    print("\n📊 SUMMARY COMPARISON TABLE")
    print_separator('=')

    print("\n┌─────────────────────────────────────────────────────────────────────────┐")
    print("│                    RIGVEDA VALIDATION RESULTS                            │")
    print("├─────────────────────────────────────────────────────────────────────────┤")
    print("│ Implementation          │ Dataset  │ Exact Acc  │ Family Acc │ Time/v   │")
    print("├─────────────────────────────────────────────────────────────────────────┤")

    def fmt_acc(r, key):
        if 'error' in r:
            return "ERROR"
        return f"{r[key]:.1f}%"

    def fmt_time(r):
        if 'error' in r or 'time_per_verse_ms' not in r:
            return "N/A"
        return f"{r['time_per_verse_ms']:.1f}ms"

    print(
        f"│ chanda_iitk.py          │ Small    │ {fmt_acc(results['iitk_small_rigveda'], 'exact_accuracy'):>10} │ {fmt_acc(results['iitk_small_rigveda'], 'family_accuracy'):>10} │ {fmt_time(results['iitk_small_rigveda']):>8} │"
    )
    print(
        f"│ chanda_iitk.py          │ Large    │ {fmt_acc(results['iitk_large_rigveda'], 'exact_accuracy'):>10} │ {fmt_acc(results['iitk_large_rigveda'], 'family_accuracy'):>10} │ {fmt_time(results['iitk_large_rigveda']):>8} │"
    )
    print(
        f"│ chanda.py (Ours)        │ Large    │ {fmt_acc(results['ours_large_rigveda'], 'exact_accuracy'):>10} │ {fmt_acc(results['ours_large_rigveda'], 'family_accuracy'):>10} │ {fmt_time(results['ours_large_rigveda']):>8} │"
    )
    print("└─────────────────────────────────────────────────────────────────────────┘")

    print("\n┌─────────────────────────────────────────────────────────────────────────┐")
    print("│                    CSV ACCURACY TEST RESULTS                             │")
    print("├─────────────────────────────────────────────────────────────────────────┤")
    print("│ Implementation          │ Dataset  │ Accuracy   │ Time/verse            │")
    print("├─────────────────────────────────────────────────────────────────────────┤")
    print(
        f"│ chanda_iitk.py          │ Small    │ {fmt_acc(results['iitk_small_csv'], 'accuracy'):>10} │ {fmt_time(results['iitk_small_csv']):>21} │"
    )
    print(
        f"│ chanda_iitk.py          │ Large    │ {fmt_acc(results['iitk_large_csv'], 'accuracy'):>10} │ {fmt_time(results['iitk_large_csv']):>21} │"
    )
    print(
        f"│ chanda.py (Ours)        │ Large    │ {fmt_acc(results['ours_large_csv'], 'accuracy'):>10} │ {fmt_time(results['ours_large_csv']):>21} │"
    )
    print("└─────────────────────────────────────────────────────────────────────────┘")

    # Analysis
    print("\n" + "=" * 70)
    print("📝 ANALYSIS")
    print("=" * 70)

    # Compare IITK small vs large
    if 'error' not in results['iitk_small_rigveda'] and 'error' not in results['iitk_large_rigveda']:
        diff = results['iitk_large_rigveda']['exact_accuracy'] - results['iitk_small_rigveda']['exact_accuracy']
        if diff > 0:
            print(f"✅ Larger dataset improves IITK accuracy by {diff:.1f}% on Rigveda")
        elif diff < 0:
            print(f"⚠️  Larger dataset decreases IITK accuracy by {abs(diff):.1f}% on Rigveda")
        else:
            print("➡️  Larger dataset has no effect on IITK accuracy on Rigveda")

    # Compare Our implementation vs IITK
    if 'error' not in results['ours_large_rigveda'] and 'error' not in results['iitk_large_rigveda']:
        diff = results['ours_large_rigveda']['exact_accuracy'] - results['iitk_large_rigveda']['exact_accuracy']
        if diff > 0:
            print(f"✅ Our implementation outperforms IITK by {diff:.1f}% on Rigveda (same dataset)")
        elif diff < 0:
            print(f"⚠️  Our implementation underperforms IITK by {abs(diff):.1f}% on Rigveda (same dataset)")
        else:
            print("➡️  Our implementation matches IITK on Rigveda (same dataset)")

    if 'error' not in results['ours_large_csv'] and 'error' not in results['iitk_large_csv']:
        diff = results['ours_large_csv']['accuracy'] - results['iitk_large_csv']['accuracy']
        if diff > 0:
            print(f"✅ Our implementation outperforms IITK by {diff:.1f}% on CSV test (same dataset)")
        elif diff < 0:
            print(f"⚠️  Our implementation underperforms IITK by {abs(diff):.1f}% on CSV test (same dataset)")
        else:
            print("➡️  Our implementation matches IITK on CSV test (same dataset)")

    print("\n" + "=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
