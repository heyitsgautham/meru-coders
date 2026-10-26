#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Syllabification Analysis

Compares multiple syllabification approaches:
1. Our sanskrit_text method (default)
2. Our ICU method
3. IITK reference implementation
4. Raw sanskrit_text library

Goal: Identify root causes of undercounting and find the best approach.
"""

import sanskrit_text as skt

from backend.config import settings
from backend.core.chanda import Chanda
from backend.evaluation.syllabification_analysis_verses import TEST_VERSES

# Try to import IITK reference
try:
    from reference.alternative_implementations.chanda_iitk import Chanda as ChandaIITK

    IITK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: IITK reference not available: {e}")
    IITK_AVAILABLE = False


# =============================================================================
# TEST VERSES - From simple to complex
# =============================================================================


def count_valid_lg(lg_list):
    """Count only valid L/G marks (exclude empty strings)"""
    return len([x for x in lg_list if x in ['L', 'G', 'ल', 'ग']])


def normalize_lg(lg_list):
    """Convert LG list to string, handling both formats"""
    result = []
    for mark in lg_list:
        if mark == 'L' or mark == 'ल':
            result.append('L')
        elif mark == 'G' or mark == 'ग':
            result.append('G')
        # Skip empty marks
    return ''.join(result)


def analyze_with_our_sanskrit_text(text, data_path):
    """Analyze using our Chanda class with sanskrit_text method"""
    chanda = Chanda(data_path, syllabization_method='sanskrit_text')
    syllables, lg_marks = chanda.mark_lg(text)

    # Flatten syllables
    if syllables and isinstance(syllables[0], list):
        flat_syl = [s for ln in syllables for w in ln for s in w]
    else:
        flat_syl = syllables

    return {
        'method': 'Our sanskrit_text',
        'syllables': flat_syl,
        'syllable_count': len(flat_syl),
        'lg_marks': lg_marks,
        'lg_count': count_valid_lg(lg_marks),
        'lg_string': normalize_lg(lg_marks),
    }


def analyze_with_our_icu(text, data_path):
    """Analyze using our Chanda class with ICU method"""
    try:
        chanda = Chanda(data_path, syllabization_method='icu')
        syllables, lg_marks = chanda.mark_lg(text)

        # Flatten syllables
        if syllables and isinstance(syllables[0], list):
            flat_syl = [s for ln in syllables for w in ln for s in w]
        else:
            flat_syl = syllables

        return {
            'method': 'Our ICU',
            'syllables': flat_syl,
            'syllable_count': len(flat_syl),
            'lg_marks': lg_marks,
            'lg_count': count_valid_lg(lg_marks),
            'lg_string': normalize_lg(lg_marks),
        }
    except Exception as e:
        return {
            'method': 'Our ICU',
            'error': str(e),
            'syllables': [],
            'syllable_count': 0,
            'lg_marks': [],
            'lg_count': 0,
            'lg_string': '',
        }


def analyze_with_iitk(text, data_path):
    """Analyze using IITK reference implementation"""
    if not IITK_AVAILABLE:
        return {
            'method': 'IITK Reference',
            'error': 'Not available',
            'syllables': [],
            'syllable_count': 0,
            'lg_marks': [],
            'lg_count': 0,
            'lg_string': '',
        }

    try:
        chanda = ChandaIITK(data_path)
        syllables, lg_marks = chanda.mark_lg(text)

        # Flatten syllables
        flat_syl = [s for ln in syllables for w in ln for s in w]

        return {
            'method': 'IITK Reference',
            'syllables': flat_syl,
            'syllable_count': len(flat_syl),
            'lg_marks': lg_marks,
            'lg_count': count_valid_lg(lg_marks),
            'lg_string': normalize_lg(lg_marks),
        }
    except Exception as e:
        return {
            'method': 'IITK Reference',
            'error': str(e),
            'syllables': [],
            'syllable_count': 0,
            'lg_marks': [],
            'lg_count': 0,
            'lg_string': '',
        }


def analyze_with_raw_sanskrit_text(text):
    """Analyze using raw sanskrit_text library directly"""
    try:
        # Clean the text first
        clean_text = skt.clean(text)
        syllables = skt.get_syllables(clean_text)
        flat_syl = [s for ln in syllables for w in ln for s in w]

        # Compute LG marks manually
        lg_marks = []
        skip_syllables = [skt.AVAGRAHA]

        if not flat_syl:
            return {
                'method': 'Raw sanskrit_text',
                'syllables': [],
                'syllable_count': 0,
                'lg_marks': [],
                'lg_count': 0,
                'lg_string': '',
            }

        for idx, syllable in enumerate(flat_syl[:-1]):
            if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
                lg_marks.append('')
                continue
            laghu = skt.is_laghu(syllable) and (skt.HALANTA not in flat_syl[idx + 1])
            lg_marks.append('L' if laghu else 'G')

        # Last syllable
        syllable = flat_syl[-1]
        if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
            lg_marks.append('')
        else:
            lg_marks.append('L' if skt.is_laghu(syllable) else 'G')

        return {
            'method': 'Raw sanskrit_text',
            'syllables': flat_syl,
            'syllable_count': len(flat_syl),
            'lg_marks': lg_marks,
            'lg_count': count_valid_lg(lg_marks),
            'lg_string': normalize_lg(lg_marks),
        }
    except Exception as e:
        return {
            'method': 'Raw sanskrit_text',
            'error': str(e),
            'syllables': [],
            'syllable_count': 0,
            'lg_marks': [],
            'lg_count': 0,
            'lg_string': '',
        }


def run_analysis():
    """Run comprehensive syllabification analysis"""
    data_path = str(settings.DATA_DIR)

    print("=" * 80)
    print("COMPREHENSIVE SYLLABIFICATION ANALYSIS")
    print("=" * 80)
    print()

    # Summary statistics
    stats = {
        'simple': {'total': 0, 'perfect': 0, 'methods': {}},
        'gayatri': {'total': 0, 'perfect': 0, 'methods': {}},
        'anushtubh': {'total': 0, 'perfect': 0, 'methods': {}},
        'trishtubh': {'total': 0, 'perfect': 0, 'methods': {}},
        'jagati': {'total': 0, 'perfect': 0, 'methods': {}},
        'conjunct': {'total': 0, 'perfect': 0, 'methods': {}},
        'vedic': {'total': 0, 'perfect': 0, 'methods': {}},
    }

    method_totals = {
        'Our sanskrit_text': {'correct': 0, 'total': 0, 'diff_sum': 0},
        'Our ICU': {'correct': 0, 'total': 0, 'diff_sum': 0},
        'IITK Reference': {'correct': 0, 'total': 0, 'diff_sum': 0},
        'Raw sanskrit_text': {'correct': 0, 'total': 0, 'diff_sum': 0},
    }

    for verse in TEST_VERSES:
        category = verse['category']
        stats[category]['total'] += 1

        print(f"\n{'=' * 80}")
        print(f"[{verse['id']}] {verse['category'].upper()} - {verse['notes']}")
        print(f"{'=' * 80}")
        print(f"Text: {verse['text']}")
        print(f"Expected syllables: {verse['expected_syllables']}")
        if verse['expected_lg']:
            print(f"Expected L-G: {verse['expected_lg']}")
        print()

        # Run all analyses
        results = [
            analyze_with_our_sanskrit_text(verse['text'], data_path),
            analyze_with_our_icu(verse['text'], data_path),
            analyze_with_iitk(verse['text'], data_path),
            analyze_with_raw_sanskrit_text(verse['text']),
        ]

        best_diff = float('inf')
        best_method = None

        for result in results:
            method = result['method']
            if 'error' in result:
                print(f"  {method}: ERROR - {result['error']}")
                continue

            syl_count = result['syllable_count']
            lg_count = result['lg_count']
            expected = verse['expected_syllables']
            diff = abs(syl_count - expected)

            # Update method totals
            method_totals[method]['total'] += 1
            method_totals[method]['diff_sum'] += diff
            if diff == 0:
                method_totals[method]['correct'] += 1

            # Track best method for this verse
            if diff < best_diff:
                best_diff = diff
                best_method = method

            status = '✓' if diff == 0 else f'✗ (diff={diff})'

            print(f"  {method}:")
            print(f"    Syllables: {result['syllables']}")
            print(f"    Count: {syl_count} (LG count: {lg_count}) {status}")
            print(f"    L-G: {result['lg_string']}")

        print()
        print(f"  BEST: {best_method} (diff={best_diff})")

        if best_diff == 0:
            stats[category]['perfect'] += 1

    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY BY CATEGORY")
    print("=" * 80)

    for category, data in stats.items():
        if data['total'] > 0:
            pct = (data['perfect'] / data['total']) * 100
            print(f"  {category.upper()}: {data['perfect']}/{data['total']} perfect ({pct:.1f}%)")

    print()
    print("=" * 80)
    print("SUMMARY BY METHOD")
    print("=" * 80)

    for method, data in method_totals.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            avg_diff = data['diff_sum'] / data['total']
            print(f"  {method}:")
            print(f"    Exact matches: {data['correct']}/{data['total']} ({accuracy:.1f}%)")
            print(f"    Average diff: {avg_diff:.2f} syllables")

    print()
    print("=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)

    # Compare methods
    methods_sorted = sorted(method_totals.items(), key=lambda x: (x[1]['correct'], -x[1]['diff_sum']), reverse=True)

    print(f"\n  BEST METHOD: {methods_sorted[0][0]}")
    print(f"    - {methods_sorted[0][1]['correct']}/{methods_sorted[0][1]['total']} exact matches")
    print(
        f"    - {methods_sorted[0][1]['diff_sum'] / max(1, methods_sorted[0][1]['total']):.2f} avg syllable difference"
    )


def detailed_syllable_breakdown():
    """Show detailed breakdown of how syllables are being split"""
    print()
    print("=" * 80)
    print("DETAILED SYLLABLE BREAKDOWN - PROBLEMATIC VERSES")
    print("=" * 80)

    problematic = [
        ('Trishtubh', 'इन्द्रस्य नु वीर्याणि प्र वोचं यानि चकार प्रथमानि वज्री', 22),
        ('Jagati', 'इन्द्रं मित्रं वरुणमग्निमाहुरथो दिव्यः स सुपर्णो गरुत्मान्', 24),
        ('Jagati', 'द्वा सुपर्णा सयुजा सखाया समानं वृक्षं परिषस्वजाते', 24),
    ]

    for category, text, expected in problematic:
        print(f"\n{category}: {text}")
        print(f"Expected: {expected} syllables")
        print()

        # Clean and get syllables
        clean_text = skt.clean(text)
        syllables = skt.get_syllables(clean_text)

        print("Word-by-word breakdown:")
        total = 0
        for _line_idx, line in enumerate(syllables):
            for word_idx, word in enumerate(line):
                word_str = ''.join(word)
                print(f"  Word {word_idx + 1}: '{word_str}' -> {word} ({len(word)} syllables)")
                total += len(word)

        print(f"\nTotal syllables: {total}")
        print(f"Difference: {expected - total}")


if __name__ == '__main__':
    run_analysis()
    detailed_syllable_breakdown()
