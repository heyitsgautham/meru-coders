"""
Test user-provided examples to determine correct dandaka classification
"""

import sys

sys.path.insert(0, '.')

from core.dandaka_detector import classify_dandaka_unit, count_aksaras

# User provided examples
examples = {
    'Example 1': """विमुक्तः सकलापद्भिः लभेत्सम्पत्तिमुत्तमाम् ।
महापापोपपापौघैः सशीघ्रं मुच्यते नरः ॥ २३ ॥
जातिस्मरत्वमाप्नोति ब्रह्मज्ञानमनुत्तमम् ।
सदाशिवत्वमाप्नोति सोन्ते नात्र विचारणा ॥ २४ ॥
इति श्री श्यामला स्तोत्रम् ।""",
    'Example 2': """अणिमादिगुणाधारे जय नीलाद्रिसन्निभे ।
शङ्खपद्मादिसम्युक्ते सिद्धिदे त्वां भजाम्यहम् ॥ १२ ॥
जय त्वं वरभूषाङ्गि वराङ्गीं त्वां भजाम्यहम् ।
देवीं वन्दे योगिवन्द्ये जय लोकवशङ्करि ॥ १३ ॥
सर्वालङ्कारसम्युक्ते नमस्तुभ्यं निधीश्वरि ।
सर्गपालनसंहारहेतुभूते सनातनि ॥ १४ ॥
जय मातङ्गतनये जय नीलोत्पलप्रभे ।
भजे शक्रादिवन्द्ये त्वां जय त्वं भुवनेश्वरि ॥ १५ ॥
जय त्वं सर्वभक्तानां सकलाभीष्टदायिनि ।
जय त्वं सर्वभद्राङ्गी भक्ताऽशुभविनाशिनि ॥ १६ ॥
महाविद्ये नमस्तुभ्यं सिद्धलक्ष्मि नमोऽस्तु ते ।
ब्रह्मविष्णुशिवस्तुत्ये भक्तानां सर्वकामदे ॥ १७ ॥
मातङ्गीश्वरवन्द्ये त्वां प्रसीद मम सर्वदा ।
इत्येतच्छ्यामलास्तोत्रं सर्वकामसमृद्धिदम् ॥ १८ ॥
शुद्धात्मा प्रजपेद्यस्तु नित्यमेकाग्रमानसः ।
स लभेत्सकलान्कामान् वशीकुर्याज्जगत्त्रयम् ॥ १९ ॥
शीघ्रं दासा भवन्त्यस्य देवा योगीश्वरादयः ।
रम्भोर्वश्याद्यप्सरसामव्ययो मदनो भवेत् ॥ २० ॥
नृपाश्च मर्त्याः सर्वेऽस्य सदा दासा भवन्ति हि ।
लभेदष्टगुणैश्वर्यं दारिद्र्येण विमुच्यते ॥ २१ ॥
शङ्खादि निधयो द्वार्स्थाः सान्निध्यं पर्युपासते ।
व्याचष्टे सर्वशास्त्राणि सर्वविद्यानिधिर्भवेत् ॥ २२ ॥""",
    'Example 3': """जय मातर्विशालाक्षि जय सङ्गीतमातृके ।
जय मातङ्गि चण्डालि गृहीतमधुपात्रके ॥ १ ॥
नमस्तेऽस्तु महादेवि नमो भगवतीश्वरि ।
नमस्तेऽस्तु जगन्मातर्जय शङ्करवल्लभे ॥ २ ॥
जय त्वं श्यामले देवि शुकश्यामे नमोऽस्तु ते ।
महाश्यामे महारामे जय सर्वमनोहरे ॥ ३ ॥
जय नीलोत्पलप्रख्ये जय सर्ववशङ्करि ।
जय त्वजात्वसंस्तुत्ये लघुश्यामे नमोऽस्तु ते ॥ ४ ॥
नमो नमस्ते रक्ताक्षि जय त्वं मदशालिनि ।
जय मातर्महालक्ष्मि वागीश्वरि नमोऽस्तु ते ॥ ५ ॥
नम इन्द्रादिसंस्तुत्ये नमो ब्रह्मादिपूजिते ।
नमो मरकतप्रख्ये शङ्खकुण्डलशोभिते ॥ ६ ॥
जय त्वं जगदीशानि लोकमोहिनि ते नमः ।
नमस्तेऽस्तु महाकृष्णे नमो विश्वेशवल्लभे ॥ ७ ॥
महेश्वरि नमस्तेऽस्तु नीलाम्बरसमन्विते ।
नमः कल्याणि कृष्णाङ्गि नमस्ते परमेश्वरि ॥ ८ ॥
महादेवप्रियकरि नमः सर्ववशङ्करि ।
महासौभाग्यदे नॄणां कदम्बवनवासिनि ॥ ९ ॥
जय सङ्गीतरसिके वीणाहस्ते नमोऽस्तु ते ।
जनमोहिनि वन्दे त्वां ब्रह्मविष्णुशिवात्मिके ॥ १० ॥
वाग्वादिनि नमस्तुभ्यं सर्वविद्याप्रदे नमः ।
नमस्ते कुलदेवेशि नमो नारीवशङ्करि ॥ ११ ॥""",
}

print("Testing User-Provided Examples:\n")
print("=" * 80)

for name, text in examples.items():
    lines = [line.strip() for line in text.strip().split('\n') if line.strip() and not line.strip().startswith('॥')]

    print(f"\n{name}:")
    print(f"Total lines: {len(lines)}")

    # Count aksaras for each line
    classifications = []
    total_aksaras = 0
    for i, line in enumerate(lines[:5], 1):  # Show first 5 lines
        aksara_count = count_aksaras(line)
        classification = classify_dandaka_unit(aksara_count)
        classifications.append(classification)
        total_aksaras += aksara_count
        print(f"  Line {i}: {aksara_count} akṣaras → {classification}")

    if len(lines) > 5:
        print(f"  ... ({len(lines) - 5} more lines)")

    # Determine overall classification
    from collections import Counter

    overall = Counter(classifications).most_common(1)[0][0] if classifications else "Unknown"
    avg_aksaras = total_aksaras / len(lines) if lines else 0
    print(f"\n  Average: {avg_aksaras:.1f} akṣaras per line")
    print(f"  ✓ SUGGESTED CLASSIFICATION: {overall}")

print("\n" + "=" * 80)
print("\n✓ Use SINGLE lines from these examples for each dandaka category")
print("✓ Sankīrṇa: Pick a line with ~16-20 akṣaras")
print("✓ Madhyama: Pick a line with ~30-40 akṣaras")
print("✓ Prabandha: Pick a line with ~60-70 akṣaras")
print("✓ Ati: Combine multiple lines to reach >108 akṣaras")
