#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test confidence reasons module integration with chanda.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config import settings
from backend.core import Chanda


def test_confidence_reasons():
    """Test that confidence reasons are correctly generated."""
    chanda = Chanda(data_path=str(settings.DATA_DIR))

    # Test 1: Anushtubh (should have exact pattern match)
    print("=" * 60)
    print("TEST 1: Anushtubh - Exact Pattern Match Expected")
    print("=" * 60)

    result = chanda.identify_line("धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः")

    assert 'confidence_scores' in result, "Missing confidence_scores"
    assert 'confidence_reasons' in result, "Missing confidence_reasons"
    assert 'primary_confidence_reason' in result, "Missing primary_confidence_reason"

    primary_reason = result['primary_confidence_reason']
    print(f"Primary Meter: {result.get('display_chanda_primary')}")
    print(f"Confidence Score: {primary_reason.get('confidence')}")
    print(f"Confidence Level: {primary_reason.get('level')}")
    print(f"Match Type: {primary_reason.get('match_type')}")
    print(f"Reason: {primary_reason.get('reason')}")
    print()
    print("Technical Details:")
    for key, value in primary_reason.get('technical_details', {}).items():
        print(f"  {key}: {value}")
    print()

    assert primary_reason is not None, "Primary confidence reason is None"
    assert 'confidence' in primary_reason, "Missing confidence in reason"
    assert 'level' in primary_reason, "Missing level in reason"
    assert 'reason' in primary_reason, "Missing reason text"
    assert primary_reason['confidence'] > 0, "Confidence should be positive"
    print("✓ Test 1 PASSED\n")

    # Test 2: Gayatri (24 syllables - Vedic meter)
    print("=" * 60)
    print("TEST 2: Gayatri - Vedic Meter")
    print("=" * 60)

    result2 = chanda.identify_line("तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्")

    primary_reason2 = result2['primary_confidence_reason']
    print(f"Primary Meter: {result2.get('display_chanda_primary')}")
    print(f"Confidence Score: {primary_reason2.get('confidence')}")
    print(f"Confidence Level: {primary_reason2.get('level')}")
    print(f"Match Type: {primary_reason2.get('match_type')}")
    print(f"Reason: {primary_reason2.get('reason')}")
    print()

    assert primary_reason2 is not None, "Primary confidence reason is None"
    print("✓ Test 2 PASSED\n")

    # Test 3: Check all confidence reasons dict
    print("=" * 60)
    print("TEST 3: All Confidence Reasons Dict")
    print("=" * 60)

    all_reasons = result['confidence_reasons']
    print(f"Number of meters with reasons: {len(all_reasons)}")

    for meter_name, reason_dict in list(all_reasons.items())[:3]:  # Show first 3
        print(f"\n  {meter_name}:")
        print(f"    Score: {reason_dict.get('confidence')}")
        print(f"    Level: {reason_dict.get('level')}")
        print(f"    Match Type: {reason_dict.get('match_type')}")

    assert len(all_reasons) > 0, "Should have at least one confidence reason"
    print("\n✓ Test 3 PASSED\n")

    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == '__main__':
    test_confidence_reasons()
