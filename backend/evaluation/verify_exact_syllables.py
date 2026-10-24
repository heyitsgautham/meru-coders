#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify exact syllable counts for all 7 Vedic meters"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chanda import Chanda

c = Chanda(os.path.join(os.path.dirname(__file__), '..', 'data'))

# Verses from rigveda_with_meters_complete.csv with EXACT syllable counts
VERSES = [
    ('Gayatri', 24, 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं', 'RV 1.1.1'),
    ('Ushnik', 28, 'अग्ने वाजस्य गोमत ईशानः सहसो यहो अस्मे धेहि जातवेदो महि श्रवः', 'RV 1.79.4'),
    ('Anushtubh', 32, 'सुविवृतं सुनिरजमिंद्र त्वादातमिद्यशः गवामप व्रजं वृधि कृणुष्व राधो अद्रिवः', 'RV 1.10.7'),
    ('Brihati', 36, 'तं घेमित्था नमस्विन उप स्वराजमासते होत्राभिरग्निं मनुषः समिंधते तितिर्वांसो अति स्रिधः', 'RV 1.36.7'),
    ('Pankti', 40, 'क्रत्वा महाँ अनुष्वधं भीम आ वावृधे शवः श्रिय ऋष्व उपाकयोर्नि शिप्री हरिवांदधे हस्तयोर्वज्रमायसं', 'RV 1.81.4'),
    ('Trishtubh', 44, 'अमी य ऋक्षा निहितास उच्चा नक्तं ददृश्रे कुह चिद्दिवेयुः अदब्धानि वरुणस्य व्रतानि विचाकशच्चंद्रमा नक्तमेति', 'RV 1.24.10'),
    ('Jagati', 48, 'आ नासत्या त्रिभिरेकादशैरिह देवेभिर्यातं मधुपेयमश्विना प्रायुस्तारिष्टं नी रपांसि मृक्षतं सेधतं द्वेषो भवतं सचाभुवा', 'RV 1.34.11'),
]

print()
print('='*75)
print('VERIFYING EXACT SYLLABLE COUNTS FOR 7 VEDIC METERS')
print('='*75)
print()

all_pass = True
for name, expected, verse, source in VERSES:
    r = c.identify_line(verse)
    actual = r.get('display_length', 0)
    if isinstance(actual, str):
        actual = int(actual) if actual.isdigit() else 0
    meter = r.get('display_chanda_primary', '')
    
    if actual == expected:
        status = '✅ EXACT'
    else:
        status = f'❌ OFF BY {abs(actual - expected)}'
        all_pass = False
    
    print(f'{name:12} | {status}')
    print(f'  Expected: {expected} syllables | Actual: {actual} syllables')
    print(f'  Meter: {meter}')
    print(f'  Source: {source}')
    print(f'  Verse: {verse[:60]}...')
    print()

print('='*75)
if all_pass:
    print('✅ ALL 7 METERS HAVE EXACT SYLLABLE COUNTS!')
else:
    print('❌ Some meters have incorrect syllable counts')
print('='*75)
