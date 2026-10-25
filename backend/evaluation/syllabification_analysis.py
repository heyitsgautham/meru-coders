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

TEST_VERSES = [
    # =========================================================================
    # SIMPLE VERSES (Short, clear words)
    # =========================================================================
    {
        'id': 'Simple-1',
        'text': 'राम',
        'expected_syllables': 2,
        'expected_lg': 'GL',
        'category': 'simple',
        'notes': 'Simple 2-syllable word',
    },
    {
        'id': 'Simple-2',
        'text': 'नमस्ते',
        'expected_syllables': 3,
        'expected_lg': 'LGG',
        'category': 'simple',
        'notes': 'Common greeting',
    },
    {
        'id': 'Simple-3',
        'text': 'भगवान्',
        'expected_syllables': 3,
        'expected_lg': 'LLG',
        'category': 'simple',
        'notes': 'Word ending in halanta',
    },
    {
        'id': 'Simple-4',
        'text': 'ओम्',
        'expected_syllables': 1,
        'expected_lg': 'G',
        'category': 'simple',
        'notes': 'Single long syllable with anusvara',
    },
    # =========================================================================
    # GAYATRI (24 syllables = 3×8)
    # =========================================================================
    {
        'id': 'Gayatri-1',
        'text': 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि । धियो यो नः प्रचोदयात् ॥',
        'expected_syllables': 24,
        'expected_lg': 'GGLLGLGGGGLGGLGLLGLGLGG',  # May need verification
        'category': 'gayatri',
        'notes': 'Famous Gayatri Mantra',
    },
    {
        'id': 'Gayatri-2',
        'text': 'अग्निमीळे पुरोहितं यज्ञस्य देवं ऋत्विजम् । होतारं रत्नधातमम् ॥',
        'expected_syllables': 24,
        'expected_lg': None,  # Need to verify
        'category': 'gayatri',
        'notes': 'RV 1.1.1',
    },
    # =========================================================================
    # ANUSHTUBH (32 syllables = 4×8)
    # =========================================================================
    {
        'id': 'Anushtubh-1',
        'text': 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः',
        'expected_syllables': 16,
        'expected_lg': 'GLGGLGGLLLGGLLLL',
        'category': 'anushtubh',
        'notes': 'BG 1.1 first half',
    },
    {
        'id': 'Anushtubh-2',
        'text': 'सहस्रशीर्षा पुरुषः सहस्राक्षः सहस्रपात्',
        'expected_syllables': 16,
        'expected_lg': 'LLGGGLLGLLGGLLLG',
        'category': 'anushtubh',
        'notes': 'Purusha Sukta first half',
    },
    # =========================================================================
    # TRISHTUBH (44 syllables = 4×11) - MOST PROBLEMATIC
    # =========================================================================
    {
        'id': 'Trishtubh-1',
        'text': 'इन्द्रस्य नु वीर्याणि प्र वोचं यानि चकार प्रथमानि वज्री',
        'expected_syllables': 22,
        'expected_lg': 'GGLLLGGLLLGGGLLGLGLGG',
        'category': 'trishtubh',
        'notes': 'RV 1.32.1 first half (pada 1-2)',
    },
    {
        'id': 'Trishtubh-2',
        'text': 'अहन्नहिमन्वपस्ततर्द प्र वक्षणा अभिनत्पर्वतानाम्',
        'expected_syllables': 22,
        'expected_lg': 'LGLLGLGLGLGGLGLLGLGGG',
        'category': 'trishtubh',
        'notes': 'RV 1.32.1 second half (pada 3-4)',
    },
    {
        'id': 'Trishtubh-3',
        'text': 'नासदासीन्नो सदासीत्तदानीं नासीद्रजो नो व्योमा परो यत्',
        'expected_syllables': 22,
        'expected_lg': None,
        'category': 'trishtubh',
        'notes': 'Nasadiya Sukta first half',
    },
    # =========================================================================
    # JAGATI (48 syllables = 4×12) - SEVERELY UNDERCOUNTED
    # =========================================================================
    {
        'id': 'Jagati-1',
        'text': 'इन्द्रं मित्रं वरुणमग्निमाहुरथो दिव्यः स सुपर्णो गरुत्मान्',
        'expected_syllables': 24,
        'expected_lg': None,
        'category': 'jagati',
        'notes': 'RV 1.164.46 first half (pada 1-2)',
    },
    {
        'id': 'Jagati-2',
        'text': 'एकं सद्विप्रा बहुधा वदन्त्यग्निं यमं मातरिश्वानमाहुः',
        'expected_syllables': 24,
        'expected_lg': None,
        'category': 'jagati',
        'notes': 'RV 1.164.46 second half (pada 3-4)',
    },
    {
        'id': 'Jagati-3',
        'text': 'द्वा सुपर्णा सयुजा सखाया समानं वृक्षं परिषस्वजाते',
        'expected_syllables': 24,
        'expected_lg': None,
        'category': 'jagati',
        'notes': 'RV 1.164.20 first half',
    },
    # =========================================================================
    # COMPLEX CONJUNCTS - Testing specific problematic patterns
    # =========================================================================
    {
        'id': 'Conjunct-1',
        'text': 'क्षत्रियः',
        'expected_syllables': 3,
        'expected_lg': 'GLG',
        'category': 'conjunct',
        'notes': 'क्ष conjunct',
    },
    {
        'id': 'Conjunct-2',
        'text': 'ज्ञानम्',
        'expected_syllables': 2,
        'expected_lg': 'GG',
        'category': 'conjunct',
        'notes': 'ज्ञ conjunct',
    },
    {
        'id': 'Conjunct-3',
        'text': 'स्वर्गः',
        'expected_syllables': 2,
        'expected_lg': 'GG',
        'category': 'conjunct',
        'notes': 'स्व conjunct with visarga',
    },
    {
        'id': 'Conjunct-4',
        'text': 'प्रज्ञा',
        'expected_syllables': 2,
        'expected_lg': 'GG',
        'category': 'conjunct',
        'notes': 'Double conjunct प्र + ज्ञ',
    },
    {
        'id': 'Conjunct-5',
        'text': 'त्र्यम्बकम्',
        'expected_syllables': 3,
        'expected_lg': 'GGG',
        'category': 'conjunct',
        'notes': 'त्र्य complex conjunct',
    },
    # =========================================================================
    # VEDIC SPECIFIC - Special characters
    # =========================================================================
    {
        'id': 'Vedic-1',
        'text': 'अग्निः',
        'expected_syllables': 2,
        'expected_lg': 'GG',
        'category': 'vedic',
        'notes': 'Visarga ending',
    },
    {
        'id': 'Vedic-2',
        'text': 'देवाः',
        'expected_syllables': 2,
        'expected_lg': 'GG',
        'category': 'vedic',
        'notes': 'Long vowel + visarga',
    },
]


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
