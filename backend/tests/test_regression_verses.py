"""The regression verses from backend/evaluation/all_fixes.py, as assertions.

That script printed PASS or FAIL for eight hand-picked cases and always exited 0.
Its fourth case was hard-coded to pass ("functionality verified elsewhere") and is dropped.
The Jagatī case still fails, so it is an expected failure that turns red the day it passes.
"""

import pytest

ANUSHTUBH = ("अनुष्टुभ्", "Anushtubh", "Anustubh")

GITA = {
    "2.47": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।\nमा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥",
    "1.1": "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥",
    "4.7": "यदा यदा हि धर्मस्य ग्लानिर्भवति भारत ।\nअभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम् ॥",
}


def top_verse_meter(chanda, text):
    verse = chanda.identify_from_text(text, verse=True, fuzzy=True)["result"]["verse"]
    return str(verse[0]["chanda"]) if verse else ""


def test_the_gayatri_mantra_has_24_syllables_and_is_found(chanda):
    result = chanda.identify_line("तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्")
    assert len(result["lg"]) == 24
    assert result["found"]
    assert "गायत्री" in result["display_chanda"]


@pytest.mark.parametrize("ref", GITA)
def test_gita_verses_are_anushtubh(chanda, ref):
    meter = top_verse_meter(chanda, GITA[ref])
    assert any(name in meter for name in ANUSHTUBH), f"Gita {ref}: {meter!r}"


@pytest.mark.parametrize(("fragment", "syllables"), [("धर्मक्षेत्रे", 4), ("समवेता युयुत्सवः", 8)])
def test_short_fragments_are_syllabified(chanda, fragment, syllables):
    assert len(chanda.identify_line(fragment)["lg"]) == syllables


@pytest.mark.xfail(strict=True, reason="the Jagatī regression case still fails, as the README records")
def test_the_jagati_case(chanda):
    text = "काश्चित्कान्ता समुपेत्य यस्तया सह मोदते विरहः स पुनर्मिलनं ।\nसः खलु नः पुनराप्तसंगमानां विरहजनितवेदनां न वेत्ति ॥"
    result = chanda.identify_from_text(text, verse=True, fuzzy=True)["result"]
    syllables = sum(len(line["result"]["lg"]) for line in result["line"])
    meter = str(result["verse"][0]["chanda"]) if result["verse"] else ""
    assert "जगती" in meter or "Jagati" in meter or syllables == 48
