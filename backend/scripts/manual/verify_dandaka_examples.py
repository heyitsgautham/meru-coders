"""
Verify the syllable counts for the 4 Dandaka examples in examples.json
"""

import sys

sys.path.insert(0, '.')

from core.dandaka_detector import classify_dandaka_unit, count_aksaras

examples = {
    'संकीर्णदण्डकम्': "रामो राजमणिः सदा विजयते रामं रमेशं भजे",
    'मध्यमदण्डकम्': "यस्मिन् जातो रामः सर्वेषां लोकानां हितकरः सत्यप्रतिज्ञः धर्मात्मा स राजा दशरथः श्रीमान् कोसलराजधान्यां अयोध्यायां प्रजानां पालकः",
    'प्रबन्धदण्डकम्': "तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य चकास चामीकरशैलकूटनिष्क्रान्तशाखं महतः पतत्रम्",
    'अतिदण्डकम्': "तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य चकास चामीकरशैलकूटनिष्क्रान्तशाखं महतः पतत्रं स्फुरत्पाटलाभोगवपुः प्रभायां दधद्रोचिषां संहतिं रोचमानं तमः सद्य आर्द्रालिगोप्यम् अथ खं वियच्च तत्सर्वमेवाशु समावृणोदभ्रं महान्तं तमसा",
}

expected_ranges = {'संकीर्णदण्डकम्': (0, 26), 'मध्यमदण्डकम्': (27, 51), 'प्रबन्धदण्डकम्': (52, 108), 'अतिदण्डकम्': (109, 999)}

print("=" * 80)
print("DANDAKA EXAMPLES VERIFICATION")
print("=" * 80)

all_correct = True

for name, text in examples.items():
    aksara_count = count_aksaras(text)
    classification = classify_dandaka_unit(aksara_count)
    min_range, max_range = expected_ranges[name]

    print(f"\n{name}:")
    print(f"  Akṣara Count: {aksara_count}")
    print(f"  Classification: {classification}")
    print(f"  Expected Range: {min_range}-{max_range}")

    if min_range <= aksara_count <= max_range:
        print("  ✓ CORRECT - Within expected range")
    else:
        print("  ✗ INCORRECT - Outside expected range!")
        all_correct = False

    # Show first 80 chars of text
    preview = text[:80] + "..." if len(text) > 80 else text
    print(f"  Text: {preview}")

print("\n" + "=" * 80)
if all_correct:
    print("✓ ALL EXAMPLES ARE CORRECTLY CLASSIFIED!")
else:
    print("✗ SOME EXAMPLES NEED ADJUSTMENT")
print("=" * 80)
