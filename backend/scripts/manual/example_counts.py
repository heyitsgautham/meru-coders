"""Test akṣara counts for dandaka examples"""

import sys

sys.path.insert(0, 'D:\\Projects\\meru-coders')

from backend.core.dandaka_detector import classify_dandaka_unit, count_aksaras

examples = [
    (
        'Ati',
        'तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः। महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः। क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य।',
    ),
    ('Prabandha', 'श्रीमद्भगवद्गीतासूपनिषत्सु ब्रह्मविद्यायां योगशास्त्रे श्रीकृष्णार्जुनसंवादे अर्जुनविषादयोगो नाम प्रथमोऽध्यायः।'),
    ('Madhyama', 'दीपः प्रज्वलितो रात्रौ तमसः शत्रुरुच्यते। स एव दिवसे जातः किं नाम तमसः शत्रुः।'),
    ('Sankīrṇa', 'रामो राजमणिः सदा विजयते रामं रमेशं भजे।'),
]

print("=" * 80)
print("DANDAKA EXAMPLE AKSARA COUNTS")
print("=" * 80)

for expected_type, text in examples:
    count = count_aksaras(text)
    classification = classify_dandaka_unit(count)
    match = "✓" if expected_type.lower() in classification.lower() else "✗"
    print(f"\n{match} {expected_type}: {count} akṣaras → {classification}")

print("\n" + "=" * 80)
print("\nCLASSIFICATION RANGES:")
print("  Saṃkīrṇa: ≤26 akṣaras")
print("  Madhyama: 27-51 akṣaras")
print("  Prabandha: 52-108 akṣaras")
print("  Ati: >108 akṣaras")
print("=" * 80)
