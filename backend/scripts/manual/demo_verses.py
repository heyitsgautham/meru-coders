#!/usr/bin/env python3
"""Demo verses for SIH 2025 judges showing different confidence scores."""

import sys
sys.path.insert(0, '/home/harevasu/Projects/meru-coders')

from backend.core import Chanda
from backend.config import settings

chanda = Chanda(data_path=str(settings.DATA_DIR))

# Test verses for different confidence levels - carefully selected to show variety
test_verses = [
    # 1. EXACT PATTERN MATCH (10.0) - Classic Anushtubh from Bhagavad Gita
    ("धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः", "Bhagavad Gita 1.1 - Exact Pattern Match"),
    
    # 2. VEDIC SYLLABLE COUNT (6.0) - Gayatri Mantra
    ("तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्", "Gayatri Mantra - Vedic Syllable Match"),
    
    # 3. MANDAKRANTA (10.0) - Complex 17-syllable classical meter  
    ("कश्चित्कान्ताविरहगुरुणा स्वाधिकारात्प्रमत्तः", "Meghaduta Opening - Mandakranta"),
]

print("=" * 80)
print("CONFIDENCE SCORING EXAMPLES FOR SIH 2025 JUDGES")
print("=" * 80)

for verse, description in test_verses:
    result = chanda.identify_line(verse)
    reason = result.get('primary_confidence_reason', {})
    
    if reason:
        print(f"\n{'─' * 80}")
        print(f"📜 VERSE: {verse}")
        print(f"📝 Source: {description}")
        print(f"{'─' * 80}")
        print(f"✅ Identified Meter: {result.get('display_chanda_primary', 'Unknown')}")
        print(f"📊 Confidence Score: {reason.get('confidence', 0)}/10")
        print(f"🎯 Confidence Level: {reason.get('level', 'unknown').replace('_', ' ').title()}")
        print(f"🔍 Match Type: {reason.get('match_type', 'unknown')}")
        print(f"💡 Reason: {reason.get('reason', 'N/A')}")
        print(f"📏 Syllables: {result.get('display_length', 0)}")
        lg_pattern = ''.join([c for c in result.get('display_lg', []) if c])
        print(f"🔤 L-G Pattern: {lg_pattern}")
    else:
        print(f"\n⚠️ {description}: No confidence reason available")

print("\n" + "=" * 80)
