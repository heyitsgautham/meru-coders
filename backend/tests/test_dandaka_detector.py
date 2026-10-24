"""Daṇḍaka and Rājaśyāmalā detection in backend.core.dandaka_detector.

The four examples are the ones the frontend's ExamplesView offers for
daṇḍaka mode, one per class.
"""

import pytest

from backend.core import dandaka_detector as dd

EXAMPLES = {
    'Saṃkīrṇa-daṇḍakam': """रामो राजमणिः सदा विजयते रामं रमेशं भजे।""",

    'Madhyama-daṇḍakam': """यस्मिन् जातो रामः सर्वेषां लोकानां हितकरः सत्यप्रतिज्ञः धर्मात्मा स राजा दशरथः।""",

    'Prabandha-daṇḍakam': """तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य।""",

    'Ati-daṇḍakam': """तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य चकास चामीकरशैलकूटनिष्क्रान्तशाखं महतः पतत्रं स्फुरत्पाटलाभोगवपुः प्रभायां दधद्रोचिषां संहतिं रोचमानं तमः सद्य आर्द्रालिगोप्यम्।"""
}

EXPECTED_AKSARAS = {
    'Saṃkīrṇa-daṇḍakam': 19,
    'Madhyama-daṇḍakam': 31,
    'Prabandha-daṇḍakam': 66,
    'Ati-daṇḍakam': 121,
}


@pytest.mark.parametrize("expected_class", list(EXAMPLES))
def test_examples_classify_by_aksara_count(expected_class):
    text = EXAMPLES[expected_class].strip()
    count = dd.count_aksaras(text)
    assert count == EXPECTED_AKSARAS[expected_class]
    assert dd.classify_dandaka_unit(count) == expected_class


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (0, 'Saṃkīrṇa-daṇḍakam'),
        (26, 'Saṃkīrṇa-daṇḍakam'),
        (27, 'Madhyama-daṇḍakam'),
        (51, 'Madhyama-daṇḍakam'),
        (52, 'Prabandha-daṇḍakam'),
        (108, 'Prabandha-daṇḍakam'),
        (109, 'Ati-daṇḍakam'),
        (10_000, 'Ati-daṇḍakam'),
    ],
)
def test_class_boundaries(count, expected):
    assert dd.classify_dandaka_unit(count) == expected


@pytest.mark.parametrize(
    ("text", "aksaras"),
    [("राम", 2), ("रामः", 2), ("क्ष्म", 1), ("धर्मक्षेत्रे", 4)],
)
def test_count_aksaras(text, aksaras):
    assert dd.count_aksaras(text) == aksaras


def test_virama_density():
    assert dd.count_viramas("धर्मक्षेत्रे") == 3
    assert dd.calculate_density(4, 3) == 0.75
    assert dd.calculate_density(0, 5) == 0.0


def test_detect_dandaka_splits_on_danda():
    result = dd.detect_dandaka("रामो राजमणिः सदा विजयते । रामं रमेशं भजे ॥")
    assert len(result["units"]) == 2
    assert result["total_aksaras"] == sum(u["aksara_count"] for u in result["units"])


def test_long_unit_is_dandaka():
    result = dd.detect_dandaka(EXAMPLES['Ati-daṇḍakam'])
    assert result["is_dandaka"] is True
    assert result["units"][0]["text"].endswith("...")


def test_empty_text_is_not_dandaka():
    result = dd.detect_dandaka("")
    assert result == {
        "is_dandaka": False,
        "units": [],
        "total_aksaras": 0,
        "total_viramas": 0,
        "average_density": 0.0,
    }


def test_rajashyamala_title_and_keywords():
    result = dd.detect_rajashyamala("श्री राजश्यामला स्तोत्रम् । मातङ्गी वाग्देवी वरदा ॥")
    assert result["title_match"] is True
    assert result["is_rajashyamala"] is True
    assert {"मातङ्गी", "वाग्देवी", "वरदा"} <= set(result["matched_keywords"])
    assert result["structure_type"] == "stotra-prose"


def test_analyze_mode_text_types():
    assert dd.analyze_dandaka_mode("श्री राजश्यामला स्तोत्रम् ।")["text_type"] == "rajashyamala-stotram"
    assert dd.analyze_dandaka_mode(EXAMPLES['Ati-daṇḍakam'])["text_type"] == "dandaka"
    assert dd.analyze_dandaka_mode("रामो राजमणिः सदा विजयते ।")["text_type"] == "unclassified"
