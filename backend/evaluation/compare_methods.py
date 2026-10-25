#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare ICU vs sanskrit_text syllabization for युयुत्सवः"""

from backend.config import settings
from backend.core import Chanda

# Test with both methods
print("=" * 60)
print("Comparing ICU vs sanskrit_text syllabization")
print("=" * 60)

word = 'युयुत्सवः'

# Test with ICU method
chanda_icu = Chanda(data_path=str(settings.DATA_DIR), syllabization_method='icu')
syllables_icu, lg_icu = chanda_icu.mark_lg(word)
print("\nICU Method:")
print(f"  Syllables: {syllables_icu}")
print(f"  LG marks:  {lg_icu}")

# Test with sanskrit_text method
chanda_skt = Chanda(data_path=str(settings.DATA_DIR), syllabization_method='sanskrit_text')
syllables_skt, lg_skt = chanda_skt.mark_lg(word)
print("\nsanskrit_text Method:")
print(f"  Syllables: {syllables_skt}")
print(f"  LG marks:  {lg_skt}")

print("\n" + "=" * 60)
print("Traditional Sanskrit Prosody Rules:")
print("=" * 60)
print("""
A syllable is Guru if:
1. It contains a long vowel (दीर्घ स्वर): आ, ई, ऊ, ए, ऐ, ओ, औ
2. It ends with anusvara (ं) or visarga (ः)
3. It ends with a consonant AND is followed by another consonant
   (This is 'samyoga' or 'संयोग' - consonant cluster)

For युयुत्सवः:
- यु: Short vowel उ, not followed by consonant cluster → LAGHU
- यु: Short vowel उ, followed by त्स (conjunct starts NEXT syllable) → ??? 

The key question: Does the conjunct त्स at the START of the next syllable
make the previous syllable Guru?

Traditional view: NO - the conjunct belongs to the next syllable.
The position-makes-Guru rule applies when the consonant cluster is in the
CODA of the current syllable, not the ONSET of the next syllable.
""")
