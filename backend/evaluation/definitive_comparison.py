#!/usr/bin/env python3
"""
Definitive Accuracy & Performance Comparison Test
==================================================

This test provides the DEFINITIVE comparison between implementations.

Test Configurations:
1. IITK implementation + Original dataset (434 patterns)
2. IITK implementation + Our dataset (2062 patterns)
3. Our implementation + Our dataset (2062 patterns)

Test Datasets:
- Sheet1.csv: 109 verses, 22 unique chandas (smaller test set)
- complete.csv: 264 verses, 134 unique chandas (comprehensive test set)

Run with:
    cd /path/to/meru-coders
    PYTHONPATH=backend pytest backend/tests/test_definitive_comparison.py -v -s

Or directly:
    cd /path/to/meru-coders
    source backend/.venv/bin/activate
    python backend/tests/test_definitive_comparison.py

Expected Results (as of Nov 2025):
==================================
| Implementation                      | Sheet1 (109) | Complete (264) | Speed     |
|-------------------------------------|--------------|----------------|-----------|
| IITK + Original (434 patterns)      | ~62% (68)    | ~33% (87)      | ~0.3ms    |
| IITK + Our data (2062 patterns)     | ~83% (90)    | ~53% (140)     | ~42ms     |
| Our impl + Our data (2062 patterns) | ~93% (101)   | ~84% (222)     | ~2.6ms    |

Key Insights:
- Data expansion (434→2062 patterns): +20% accuracy
- Code improvements (confidence scoring, multi-level matching): +31% accuracy
- Our regex pre-compilation: 16x faster than IITK with same dataset
"""

import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest

# Setup paths
BASE_PATH = Path(__file__).parent.parent.parent
BACKEND_PATH = BASE_PATH / 'backend'
REFERENCE_PATH = BASE_PATH / 'reference' / 'alternative_implementations'

sys.path.insert(0, str(BACKEND_PATH))
sys.path.insert(0, str(REFERENCE_PATH))

# Import transliteration library for proper Devanagari handling
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
    HAS_TRANSLITERATION = True
except ImportError:
    HAS_TRANSLITERATION = False
    print("Warning: indic_transliteration not installed. Install with: pip install indic_transliteration")


# =============================================================================
# Core Utilities
# =============================================================================

def normalize_chanda_name(name: str) -> str:
    """
    Normalize meter name by converting to basic Latin for comparison.
    Uses proper transliteration library for accurate Devanagari→IAST conversion.
    
    Examples:
        'इन्द्रवज्रा' → 'indravajra'
        'indravajrā' → 'indravajra'
        'vasantatilakam' → 'vasantatilak'
    """
    if not name:
        return ''

    name = name.strip()

    # Check if contains Devanagari (Unicode range 0900-097F)
    has_devanagari = any('\u0900' <= c <= '\u097F' for c in name)

    if has_devanagari and HAS_TRANSLITERATION:
        # Use proper transliteration for accurate conversion
        name = transliterate(name, sanscript.DEVANAGARI, sanscript.IAST)
    elif has_devanagari:
        # Fallback: basic character-by-character mapping (less accurate)
        devanagari_map = {
            'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ii', 'उ': 'u', 'ऊ': 'uu',
            'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
            'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'na',
            'च': 'ca', 'छ': 'cha', 'ज': 'ja', 'झ': 'jha', 'ञ': 'na',
            'ट': 'ta', 'ठ': 'tha', 'ड': 'da', 'ढ': 'dha', 'ण': 'na',
            'त': 'ta', 'थ': 'tha', 'द': 'da', 'ध': 'dha', 'न': 'na',
            'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
            'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va', 'श': 'sha',
            'ष': 'sha', 'स': 'sa', 'ह': 'ha',
            'ा': 'a', 'ि': 'i', 'ी': 'i', 'ु': 'u', 'ू': 'u',
            'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
            'ं': 'm', 'ः': 'h', '्': '', 'ृ': 'ri',
            'ँ': '', 'ऽ': '',
        }
        for dev, lat in devanagari_map.items():
            name = name.replace(dev, lat)

    # Now normalize IAST diacritics to basic Latin
    n = name.lower()
    replacements = [
        ('ā', 'a'), ('ä', 'a'),  # long a
        ('ī', 'i'),              # long i
        ('ü', 'u'), ('ū', 'u'),  # long u
        ('ṭ', 't'), ('ḍ', 'd'),  # retroflex
        ('ṇ', 'n'), ('ṅ', 'n'), ('ñ', 'n'),  # nasals
        ('ṃ', 'm'), ('ṁ', 'm'),  # anusvara
        ('ḥ', 'h'),              # visarga
        ('ś', 'sh'), ('ṣ', 'sh'),  # sibilants
        ('ṛ', 'ri'),             # vocalic r
        ('ḷ', 'l'),              # vocalic l
    ]
    for old, new in replacements:
        n = n.replace(old, new)

    # Remove trailing 'm' or 'a' (common suffix variations)
    for suffix in ['m', 'a']:
        if n.endswith(suffix) and len(n) > 5:
            n = n[:-1]

    return n


def chanda_names_match(expected: str, actual_list: list) -> bool:
    """
    Check if expected meter name matches any name in actual_list.
    
    Uses normalized comparison with proper Devanagari transliteration.
    Also handles common spelling variants and partial matching.
    
    Examples that should match:
        - 'indravajrā' and 'इन्द्रवज्रा'
        - 'anuṣṭup' and 'anuṣṭubh'  
        - 'vasantatilakam' and 'वसन्ततिलका'
    """
    if not expected or not actual_list:
        return False

    exp_norm = normalize_chanda_name(expected)

    # Common spelling variants (normalized_expected -> normalized_variants)
    SPELLING_VARIANTS = {
        'anushtup': ['anushtubh', 'anustubh', 'anustup', 'slok', 'shlok'],
        'slok': ['anushtup', 'anushtubh', 'anustubh'],
        'pythvi': ['prithvi', 'prthvi', 'prithv'],
        'shardulavikridita': ['shardulvikriditam', 'shardulavikriditam', 'shardulvikridita'],
        'shardulvikridita': ['shardulvikriditam', 'shardulavikriditam'],
        'indravajr': ['upajati'],  # Indravajra is a type of Upajati
        'upendravajr': ['upajati'],
    }

    for actual in actual_list:
        act_norm = normalize_chanda_name(actual)

        # Exact normalized match
        if exp_norm == act_norm:
            return True

        # Check spelling variants
        if exp_norm in SPELLING_VARIANTS:
            if act_norm in SPELLING_VARIANTS[exp_norm]:
                return True

        # Prefix match for longer names (at least 5 chars matching)
        min_len = min(len(exp_norm), len(act_norm))
        if min_len >= 5:
            # Check if first 5+ chars match (handles suffix variations)
            prefix_len = max(5, min_len - 2)
            if exp_norm[:prefix_len] == act_norm[:prefix_len]:
                return True

        # One contains the other (for compound names)
        if len(exp_norm) >= 5 and len(act_norm) >= 5:
            if exp_norm in act_norm or act_norm in exp_norm:
                return True

    return False


def load_test_csv(csv_path: str) -> list:
    """
    Load test data from CSV file.
    Returns list of (verse, expected_chanda) tuples.
    """
    df = pd.read_csv(csv_path, skiprows=1)
    df.columns = [c.strip() for c in df.columns]
    df = df[df['Shloka'].notna() & df['chanda'].notna()]
    return [(row['Shloka'], row['chanda']) for _, row in df.iterrows()]


def extract_chanda_names_from_result(result: dict) -> list:
    """
    Extract chanda names from identify_line() result dictionary.
    Handles the nested structure: {'chanda': [[name, [variants]], ...]}
    """
    names = []
    if result and 'chanda' in result:
        for item in result['chanda']:
            if isinstance(item, (list, tuple)) and len(item) >= 1:
                names.append(item[0])
    return names


def run_accuracy_test(implementation, test_data: list) -> dict:
    """
    Run accuracy test on an implementation.
    
    Args:
        implementation: Chanda class instance with identify_line() method
        test_data: List of (verse, expected_chanda) tuples
    
    Returns:
        dict with keys: correct, total, accuracy, avg_ms, mismatches
    """
    correct = 0
    mismatches = []
    times = []

    for verse, expected in test_data:
        # Use first line only (multi-line verses in CSV)
        first_line = verse.replace('\r', '').split('\n')[0].strip()

        start = time.perf_counter()
        try:
            result = implementation.identify_line(first_line)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

            actual_names = extract_chanda_names_from_result(result)

            if chanda_names_match(expected, actual_names):
                correct += 1
            else:
                top = actual_names[0] if actual_names else '(none)'
                mismatches.append((expected, top))
        except Exception as e:
            mismatches.append((expected, f'ERROR: {str(e)[:40]}'))

    avg_ms = 1000 * sum(times) / len(times) if times else 0

    return {
        'correct': correct,
        'total': len(test_data),
        'accuracy': 100 * correct / len(test_data),
        'avg_ms': avg_ms,
        'mismatches': mismatches,
    }


# =============================================================================
# Test Class
# =============================================================================

class TestDefinitiveComparison:
    """Definitive comparison tests between implementations."""

    @pytest.fixture(scope="class")
    def paths(self):
        """Return all necessary paths."""
        return {
            'iitk_data': str(BASE_PATH / 'repos' / 'chanda' / 'data'),
            'our_data': str(BACKEND_PATH / 'data'),
            'sheet1_csv': str(BACKEND_PATH / 'data' / 'page 1-47 chanda list - Sheet1.csv'),
            'complete_csv': str(BACKEND_PATH / 'data' / 'page 1-47 chanda list - complete.csv'),
        }

    @pytest.fixture(scope="class")
    def our_impl(self, paths):
        """Our implementation with our dataset."""
        from core.chanda import Chanda
        return Chanda(data_path=paths['our_data'])

    @pytest.fixture(scope="class")
    def iitk_impl_original(self, paths):
        """IITK implementation with original dataset (434 patterns)."""
        try:
            from chanda_iitk import Chanda
            return Chanda(paths['iitk_data'])
        except ImportError:
            pytest.skip("IITK implementation not available at reference/alternative_implementations/chanda_iitk.py")

    @pytest.fixture(scope="class")
    def iitk_impl_our_data(self, paths):
        """IITK implementation with our dataset (2062 patterns)."""
        try:
            from chanda_iitk import Chanda
            return Chanda(paths['our_data'])
        except ImportError:
            pytest.skip("IITK implementation not available")

    @pytest.fixture(scope="class")
    def sheet1_data(self, paths):
        """Sheet1 test data: 109 verses, 22 unique chandas."""
        return load_test_csv(paths['sheet1_csv'])

    @pytest.fixture(scope="class")
    def complete_data(self, paths):
        """Complete test data: 264 verses, 134 unique chandas."""
        return load_test_csv(paths['complete_csv'])

    # =========================================================================
    # Main Comparison Test
    # =========================================================================

    def test_full_comparison_complete_dataset(self, our_impl, iitk_impl_original,
                                               iitk_impl_our_data, complete_data):
        """
        MAIN TEST: Full comparison on complete dataset (264 verses).
        
        This is the definitive test that shows:
        1. Effect of data expansion (434 → 2062 patterns)
        2. Effect of code improvements (confidence scoring, multi-level matching)
        3. Performance comparison
        """
        # Run all three configurations
        r1 = run_accuracy_test(iitk_impl_original, complete_data)
        r2 = run_accuracy_test(iitk_impl_our_data, complete_data)
        r3 = run_accuracy_test(our_impl, complete_data)

        n = len(complete_data)

        # Print results
        print(f"\n{'='*75}")
        print("DEFINITIVE COMPARISON RESULTS - Complete Dataset (264 verses)")
        print(f"{'='*75}")
        print(f"\n| {'Implementation':<42} | {'Accuracy':<18} | {'Speed':<12} |")
        print(f"|{'-'*42}|{'-'*18}|{'-'*12}|")
        print(f"| IITK + Original (434 patterns)           | {r1['correct']:>3}/{n} ({r1['accuracy']:>5.1f}%)     | {r1['avg_ms']:>6.2f} ms   |")
        print(f"| IITK + Our data (2062 patterns)          | {r2['correct']:>3}/{n} ({r2['accuracy']:>5.1f}%)     | {r2['avg_ms']:>6.2f} ms   |")
        print(f"| Our impl + Our data (2062 patterns)      | {r3['correct']:>3}/{n} ({r3['accuracy']:>5.1f}%)     | {r3['avg_ms']:>6.2f} ms   |")
        print(f"{'='*75}")

        print("\nKey Insights:")
        print(f"  • Data expansion (434→2062): +{r2['accuracy']-r1['accuracy']:.1f}% accuracy improvement")
        print(f"  • Code improvements: +{r3['accuracy']-r2['accuracy']:.1f}% accuracy improvement")
        print(f"  • Total improvement: +{r3['accuracy']-r1['accuracy']:.1f}% over IITK baseline")
        print(f"  • Speed: Our impl is {r2['avg_ms']/r3['avg_ms']:.1f}x faster than IITK with same data")

        # Show mismatches
        if r3['mismatches']:
            print(f"\nRemaining mismatches in our impl ({len(r3['mismatches'])}):")
            for (exp, act), cnt in Counter(r3['mismatches']).most_common(10):
                print(f"  [{cnt}x] Expected: {exp:<25} Got: {act}")

        # Assertions
        assert r3['accuracy'] >= 80.0, f"Our accuracy {r3['accuracy']:.1f}% is below 80% threshold"
        assert r3['accuracy'] >= r2['accuracy'], "Our impl should be more accurate than IITK with same data"
        assert r3['avg_ms'] < r2['avg_ms'], "Our impl should be faster than IITK with same data"

    def test_full_comparison_sheet1_dataset(self, our_impl, iitk_impl_original,
                                            iitk_impl_our_data, sheet1_data):
        """
        Comparison on Sheet1 dataset (109 verses, simpler test set).
        """
        r1 = run_accuracy_test(iitk_impl_original, sheet1_data)
        r2 = run_accuracy_test(iitk_impl_our_data, sheet1_data)
        r3 = run_accuracy_test(our_impl, sheet1_data)

        n = len(sheet1_data)

        print(f"\n{'='*75}")
        print("COMPARISON RESULTS - Sheet1 Dataset (109 verses)")
        print(f"{'='*75}")
        print(f"\n| {'Implementation':<42} | {'Accuracy':<18} | {'Speed':<12} |")
        print(f"|{'-'*42}|{'-'*18}|{'-'*12}|")
        print(f"| IITK + Original (434 patterns)           | {r1['correct']:>3}/{n} ({r1['accuracy']:>5.1f}%)     | {r1['avg_ms']:>6.2f} ms   |")
        print(f"| IITK + Our data (2062 patterns)          | {r2['correct']:>3}/{n} ({r2['accuracy']:>5.1f}%)     | {r2['avg_ms']:>6.2f} ms   |")
        print(f"| Our impl + Our data (2062 patterns)      | {r3['correct']:>3}/{n} ({r3['accuracy']:>5.1f}%)     | {r3['avg_ms']:>6.2f} ms   |")
        print(f"{'='*75}")

        assert r3['accuracy'] >= 90.0, f"Our accuracy {r3['accuracy']:.1f}% is below 90% threshold on Sheet1"

    # =========================================================================
    # Individual Performance Tests
    # =========================================================================

    def test_our_impl_speed_threshold(self, our_impl, complete_data):
        """Our implementation should process each verse in under 10ms."""
        result = run_accuracy_test(our_impl, complete_data)
        print(f"\nOur impl speed: {result['avg_ms']:.2f} ms/verse")
        assert result['avg_ms'] < 10.0, f"Speed {result['avg_ms']:.2f}ms exceeds 10ms threshold"

    def test_our_impl_accuracy_threshold(self, our_impl, complete_data):
        """Our implementation should achieve at least 80% accuracy."""
        result = run_accuracy_test(our_impl, complete_data)
        print(f"\nOur impl accuracy: {result['accuracy']:.1f}%")
        assert result['accuracy'] >= 80.0, f"Accuracy {result['accuracy']:.1f}% is below 80% threshold"

    def test_speedup_over_iitk(self, our_impl, iitk_impl_our_data, complete_data):
        """Our implementation should be at least 5x faster than IITK with same data."""
        our_result = run_accuracy_test(our_impl, complete_data)
        iitk_result = run_accuracy_test(iitk_impl_our_data, complete_data)

        speedup = iitk_result['avg_ms'] / our_result['avg_ms']
        print(f"\nSpeedup: {speedup:.1f}x (IITK: {iitk_result['avg_ms']:.2f}ms, Ours: {our_result['avg_ms']:.2f}ms)")

        assert speedup >= 5.0, f"Speedup {speedup:.1f}x is below 5x threshold"


# =============================================================================
# Standalone Execution
# =============================================================================

def main(quick_mode=False):
    """
    Run comparison directly without pytest.
    
    Args:
        quick_mode: If True, skip IITK tests (which are slow)
    """
    from core.chanda import Chanda as OurChanda

    print("Loading implementations...")

    # Load our implementation
    our_impl = OurChanda(data_path=str(BACKEND_PATH / 'data'))

    # Load IITK implementation (skip if quick mode)
    iitk_orig = None
    iitk_ours = None
    if not quick_mode:
        try:
            from chanda_iitk import Chanda as IITKChanda
            iitk_orig = IITKChanda(str(BASE_PATH / 'repos' / 'chanda' / 'data'))
            iitk_ours = IITKChanda(str(BACKEND_PATH / 'data'))
            print("  - IITK implementation loaded")
        except ImportError as e:
            print(f"Warning: Could not import IITK implementation: {e}")
            print("  Skipping IITK comparison tests.")
    else:
        print("  - Quick mode: skipping IITK (slow)")

    print("  - Our implementation loaded")

    # Load test data
    complete_csv = str(BACKEND_PATH / 'data' / 'page 1-47 chanda list - complete.csv')
    sheet1_csv = str(BACKEND_PATH / 'data' / 'page 1-47 chanda list - Sheet1.csv')

    complete_data = load_test_csv(complete_csv)
    sheet1_data = load_test_csv(sheet1_csv)

    print(f"\nLoaded {len(complete_data)} verses from complete.csv")
    print(f"Loaded {len(sheet1_data)} verses from Sheet1.csv")

    # Run tests on complete dataset
    print("\nRunning tests on complete dataset (264 verses)...")

    r1 = None
    r2 = None
    if iitk_orig:
        print("  Testing IITK + Original data (this takes ~10 seconds)...")
        r1 = run_accuracy_test(iitk_orig, complete_data)
    if iitk_ours:
        print("  Testing IITK + Our data (this takes ~2 minutes)...")
        r2 = run_accuracy_test(iitk_ours, complete_data)

    print("  Testing Our implementation...")
    r3 = run_accuracy_test(our_impl, complete_data)

    n = len(complete_data)

    print(f"\n{'='*75}")
    print("DEFINITIVE COMPARISON RESULTS")
    print(f"{'='*75}")
    print(f"Dataset: page 1-47 chanda list - complete.csv ({n} verses)")
    print(f"{'='*75}")
    print(f"\n| {'Implementation':<42} | {'Accuracy':<18} | {'Speed':<12} |")
    print(f"|{'-'*42}|{'-'*18}|{'-'*12}|")

    if r1:
        print(f"| IITK + Original (434 patterns)           | {r1['correct']:>3}/{n} ({r1['accuracy']:>5.1f}%)     | {r1['avg_ms']:>6.2f} ms   |")
    else:
        print(f"| IITK + Original (434 patterns)           | {'(skipped)':<18} | {'---':<12} |")

    if r2:
        print(f"| IITK + Our data (2062 patterns)          | {r2['correct']:>3}/{n} ({r2['accuracy']:>5.1f}%)     | {r2['avg_ms']:>6.2f} ms   |")
    else:
        print(f"| IITK + Our data (2062 patterns)          | {'(skipped)':<18} | {'---':<12} |")

    print(f"| Our impl + Our data (2062 patterns)      | {r3['correct']:>3}/{n} ({r3['accuracy']:>5.1f}%)     | {r3['avg_ms']:>6.2f} ms   |")
    print(f"{'='*75}")

    if r1 and r2:
        print("\nKey Insights:")
        print(f"  • Data expansion (434→2062): +{r2['accuracy']-r1['accuracy']:.1f}% accuracy")
        print(f"  • Code improvements: +{r3['accuracy']-r2['accuracy']:.1f}% accuracy")
        print(f"  • Total improvement: +{r3['accuracy']-r1['accuracy']:.1f}% over baseline")
        print(f"  • Speed: Our impl is {r2['avg_ms']/r3['avg_ms']:.1f}x faster than IITK with same data")

    if r3['mismatches']:
        print(f"\nMismatches in our impl ({len(r3['mismatches'])}):")
        for (exp, act), cnt in Counter(r3['mismatches']).most_common(15):
            print(f"  [{cnt}x] Expected: {exp:<25} Got: {act}")

    # Summary
    print(f"\n{'='*75}")
    print("SUMMARY")
    print(f"{'='*75}")
    print(f"✓ Our implementation achieves {r3['accuracy']:.1f}% accuracy on {n} verses")
    print(f"✓ Speed: {r3['avg_ms']:.2f} ms/verse")
    if r2:
        print(f"✓ {r2['avg_ms']/r3['avg_ms']:.1f}x faster than IITK with same data")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Definitive Chanda Comparison Test')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Quick mode: skip slow IITK tests')
    parser.add_argument('--full', '-f', action='store_true',
                       help='Full mode: include all IITK tests (slow)')
    args = parser.parse_args()

    # Default to quick mode unless --full is specified
    quick_mode = not args.full
    if args.quick:
        quick_mode = True

    main(quick_mode=quick_mode)
