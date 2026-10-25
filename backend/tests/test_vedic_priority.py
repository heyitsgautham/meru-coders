"""Verse-level Vedic meters win over pada-level matches when the verse structure confirms them.

RV 1.164.46 has four 11-syllable padas. Its fourth pada also matches the
classical vidhvaṅkamālā pattern exactly, but the 4×11 structure makes the
verse a Triṣṭubh.
"""

import pytest

EKAM_SAT = [
    "इन्द्रं मित्रं वरुणमग्निमाहुः",
    "अथो दिव्यः स सुपर्णो गरुत्मान्",
    "एकं सद्विप्रा बहुधा वदन्ति",
    "अग्निं यमं मातरिश्वानमाहुः",
]


def primary_verse_meter(result):
    verse_results = result["result"]["verse"]
    assert verse_results, "expected a verse-level result"
    best_meters, _score = verse_results[0]["chanda"]
    first = best_meters[0]
    return first[0] if isinstance(first, tuple) else first


def test_trishtubh_wins_over_vidhvankamala(chanda):
    result = chanda.identify_from_text("\n".join(EKAM_SAT), verse=True)
    assert primary_verse_meter(result) == "त्रिष्टुभ्"


def test_verse_structure_confirms_4x11(chanda):
    structure = chanda.detect_verse_structure(EKAM_SAT)
    assert structure["syllables_per_pada"] == [11, 11, 11, 11]
    assert structure["total_syllables"] == 44
    assert structure["expected_vedic_meter"] == "त्रिष्टुभ्"
    assert structure["vedic_structure_confirmed"]


def test_holistic_identification_reports_the_structure(chanda):
    result = chanda.identify_verse_holistically(EKAM_SAT)
    assert result["structure"]["vedic_structure_confirmed"]
    assert result["total_syllables"] == 44


def test_four_ten_syllable_padas_are_a_pankti(chanda):
    verse = "\n".join(
        [
            "प्रथमः पादः द्वादशाक्षरं",
            "द्वितीयः पादः द्वादशाक्षरं",
            "तृतीयः पादः द्वादशाक्षरं",
            "चतुर्थः पादः द्वादशाक्षरं",
        ]
    )
    structure = chanda.detect_verse_structure(verse.split("\n"))
    assert structure["total_syllables"] == 40
    assert not structure["vedic_structure_confirmed"]
    assert primary_verse_meter(chanda.identify_from_text(verse, verse=True)) == "पङ्क्ति"


def test_single_pada_is_named_as_a_pada_of_trishtubh(chanda):
    result = chanda.identify_line(EKAM_SAT[0])
    assert result["length"] == 11
    names = {name for name, _padas in result["chanda"][:4]}
    assert names == {"त्रिष्टुभ्"}
    assert result["display_chanda"].startswith("त्रिष्टुभ् (पाद 1)")


@pytest.mark.parametrize("meter", ["त्रिष्टुभ्", "जगती", "गायत्री", "अनुष्टुभ्"])
def test_vedic_meters_are_not_pada_level(chanda, meter):
    assert chanda.is_pada_level_meter(meter) is False
