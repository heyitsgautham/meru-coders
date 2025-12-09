"""
Test new dandaka examples to verify proper classification
"""
import sys
sys.path.insert(0, '.')

from core.dandaka_detector import count_aksaras, classify_dandaka_unit

# Test examples from ExamplesView.tsx (FIXED)
examples = {
    'Sankīrṇa': """रामो राजमणिः सदा विजयते रामं रमेशं भजे।""",
    
    'Madhyama': """यस्मिन् जातो रामः सर्वेषां लोकानां हितकरः सत्यप्रतिज्ञः धर्मात्मा स राजा दशरथः।""",
    
    'Prabandha': """तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य।""",
    
    'Ati': """तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य चकास चामीकरशैलकूटनिष्क्रान्तशाखं महतः पतत्रं स्फुरत्पाटलाभोगवपुः प्रभायां दधद्रोचिषां संहतिं रोचमानं तमः सद्य आर्द्रालिगोप्यम्।"""
}

print("Testing Dandaka Examples Classification:\n")
print("=" * 80)

for name, text in examples.items():
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    
    print(f"\n{name} Example:")
    print(f"Total lines: {len(lines)}")
    
    # Count aksaras for each line
    classifications = []
    for i, line in enumerate(lines, 1):
        aksara_count = count_aksaras(line)
        classification = classify_dandaka_unit(aksara_count)
        classifications.append(classification)
        print(f"  Line {i}: {aksara_count} akṣaras → {classification}")
    
    # Determine overall classification (most common)
    from collections import Counter
    overall = Counter(classifications).most_common(1)[0][0]
    print(f"\n  ✓ OVERALL CLASSIFICATION: {overall}")
    
    # Verify it matches expected
    expected_class = {
        'Sankīrṇa': 'Saṃkīrṇa-daṇḍakam',
        'Madhyama': 'Madhyama-daṇḍakam',
        'Prabandha': 'Prabandha-daṇḍakam',
        'Ati': 'Ati-daṇḍakam'
    }[name]
    
    if overall == expected_class:
        print(f"  ✓ CORRECT - Matches {name}")
    else:
        print(f"  ✗ WRONG - Expected {expected_class}, got {overall}")

print("\n" + "=" * 80)
print("Test complete!")
