#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for PadaSplitter CSV loading functionality.

Tests the loading of Viṣamavṛtta (unequal meter) and Ardhasama (half-equal meter) 
patterns from CSV files.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.pada_splitter import PadaSplitter


def test_csv_loading():
    """Test that CSV files are loaded correctly."""
    splitter = PadaSplitter()

    print("\n=== Test CSV Loading ===")

    # Check Viṣamavṛtta loading
    vishama_count = len(splitter.vishama_patterns)
    print(f"✓ Loaded {vishama_count} Viṣamavṛtta meters")
    assert vishama_count > 0, "No Viṣamavṛtta meters loaded"

    # Check Ardhasama loading
    ardhasama_count = len(splitter.ardhasama_patterns)
    print(f"✓ Loaded {ardhasama_count} Ardhasama meters")
    assert ardhasama_count > 0, "No Ardhasama meters loaded"

    return True


def test_vishama_pattern_access():
    """Test accessing specific Viṣamavṛtta patterns."""
    splitter = PadaSplitter()

    print("\n=== Test Viṣamavṛtta Pattern Access ===")

    # Test उद्गता (Udgata) - a classic Viṣamavṛtta
    udgata_pada1 = splitter.get_vishama_pattern('उद्गता', 1)
    assert udgata_pada1 is not None, "उद्गता pada 1 not found"
    print(f"✓ उद्गता pada 1: syllables={udgata_pada1['syllables']}, pattern={udgata_pada1['pattern']}")

    udgata_pada4 = splitter.get_vishama_pattern('उद्गता', 4)
    assert udgata_pada4 is not None, "उद्गता pada 4 not found"
    print(f"✓ उद्गता pada 4: syllables={udgata_pada4['syllables']}, pattern={udgata_pada4['pattern']}")

    # Verify unequal syllables (defining feature of Viṣamavṛtta)
    if udgata_pada1['syllables'] != udgata_pada4['syllables']:
        print(f"✓ Confirmed unequal padas: pada 1 = {udgata_pada1['syllables']}, pada 4 = {udgata_pada4['syllables']}")

    return True


def test_is_vishama_meter():
    """Test the is_vishama_meter method."""
    splitter = PadaSplitter()

    print("\n=== Test is_vishama_meter() ===")

    # Known Viṣamavṛtta
    assert splitter.is_vishama_meter('उद्गता'), "उद्गता should be Viṣamavṛtta"
    print("✓ उद्गता correctly identified as Viṣamavṛtta")

    # Not a Viṣamavṛtta (standard Sama meter)
    assert not splitter.is_vishama_meter('अनुष्टुभ्'), "अनुष्टुभ् should NOT be Viṣamavṛtta"
    print("✓ अनुष्टुभ् correctly identified as NOT Viṣamavṛtta")

    return True


def test_get_meter_info():
    """Test the get_meter_info method."""
    splitter = PadaSplitter()

    print("\n=== Test get_meter_info() ===")

    # Test Viṣamavṛtta info
    udgata_info = splitter.get_meter_info('उद्गता')
    assert udgata_info is not None, "उद्गता info not found"
    assert udgata_info['type'] == 'viṣamavṛtta', "उद्गता should be type viṣamavṛtta"
    print(f"✓ उद्गता: type={udgata_info['type']}, total_syllables={udgata_info['total_syllables']}")

    # Test standard meter info
    anushtubh_info = splitter.get_meter_info('anushtubh')
    assert anushtubh_info is not None, "anushtubh info not found"
    print(f"✓ anushtubh: type={anushtubh_info['type']}, total_syllables={anushtubh_info['total_syllables']}")

    return True


def test_meter_aliases():
    """Test that meter aliases are created correctly."""
    splitter = PadaSplitter()

    print("\n=== Test Meter Aliases ===")

    # Check that Viṣamavṛtta names are added as aliases
    if 'उद्गता' in splitter.METER_ALIASES:
        print(f"✓ उद्गता alias: {splitter.METER_ALIASES['उद्गता']}")

    # Check METERS dictionary has new entries
    udgata_key = splitter._create_meter_key('उद्गता')
    if udgata_key in splitter.METERS:
        print(f"✓ उद्गता in METERS: key={udgata_key}, pattern={splitter.METERS[udgata_key]}")

    return True


def test_list_all_vishama():
    """List all loaded Viṣamavṛtta meters with their patterns."""
    splitter = PadaSplitter()

    print("\n=== All Viṣamavṛtta Meters ===")
    print(f"{'Meter Name':<20} {'Pada 1':<6} {'Pada 2':<6} {'Pada 3':<6} {'Pada 4':<6} {'Total':<6}")
    print("-" * 60)

    for name in sorted(splitter.vishama_patterns.keys()):
        padas = splitter.vishama_patterns[name]
        syllables = {p: padas[p]['syllables'] for p in sorted(padas.keys())}
        total = sum(syllables.values())
        p1 = syllables.get(1, '-')
        p2 = syllables.get(2, '-')
        p3 = syllables.get(3, '-')
        p4 = syllables.get(4, '-')
        print(f"{name:<20} {str(p1):<6} {str(p2):<6} {str(p3):<6} {str(p4):<6} {total:<6}")

    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("PadaSplitter CSV Loading Tests")
    print("=" * 60)

    tests = [
        ("CSV Loading", test_csv_loading),
        ("Viṣamavṛtta Pattern Access", test_vishama_pattern_access),
        ("is_vishama_meter()", test_is_vishama_meter),
        ("get_meter_info()", test_get_meter_info),
        ("Meter Aliases", test_meter_aliases),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n✗ {name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ {name} ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{passed + failed} tests passed")

    # Optionally list all meters
    print("\n" + "=" * 60)
    test_list_all_vishama()

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
