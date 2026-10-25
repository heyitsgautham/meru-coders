"""Helpers extracted from Chanda.identify_from_text."""

NASADIYA = "नासदासीन्नो सदासीत्तदानीं नासीद्रजो नो व्योमा परो यत् । किमावरीवः कुह कस्य शर्मन्नम्भः किमासीद्गहनं गभीरम्"


def test_caesura_danda_in_a_vedic_verse_is_merged(chanda):
    merged = chanda._merge_vedic_caesura(NASADIYA)
    assert "।" not in merged
    assert merged.startswith("नासदासीन्नो")


def test_short_text_keeps_its_danda(chanda):
    assert chanda._merge_vedic_caesura("राम । सीता") == "राम । सीता"


def test_double_danda_or_newline_keeps_the_text(chanda):
    assert chanda._merge_vedic_caesura(NASADIYA + " ॥") == NASADIYA + " ॥"
    assert chanda._merge_vedic_caesura(NASADIYA.replace(" । ", "\n")) == NASADIYA.replace(" । ", "\n")


def test_nasadiya_is_one_line_trishtubh(chanda):
    lines = chanda.identify_from_text(NASADIYA, mode="vedic")["result"]["line"]
    assert len(lines) == 1


def test_invalid_input_response_shape(chanda):
    response = chanda._invalid_input_response("hello", "English text")
    line = response["result"]["line"][0]
    assert response["path"] is None
    assert line["line"] == "hello"
    assert line["result"]["is_valid_input"] is False
    assert line["result"]["validation_error"] == "English text"
    assert response["result"]["verse"] == []


def test_english_input_takes_the_invalid_path(chanda):
    result = chanda.identify_from_text("the quick brown fox")["result"]["line"][0]["result"]
    assert result["is_valid_input"] is False
