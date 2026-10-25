"""identify_line's fallbacks for lines without an exact pattern match."""

import pytest

from backend.core.chanda_constants import CONFIDENCE_VEDIC_CLASSICAL_MAP
from backend.core.chanda_line_fallbacks import VEDIC_METER_NAMES, LineFallbackMixin


@pytest.mark.parametrize(
    ("syllables", "meter", "confidence"),
    [(22, "गायत्री", 10.0), (30, "अनुष्टुभ्", 10.5), (43, "त्रिष्टुभ्", 11.0), (46, "जगती", 10.5)],
)
def test_vedic_range_picks_the_closest_common_meter(chanda, syllables, meter, confidence):
    assert chanda._vedic_range_match(syllables) == (meter, confidence)


def test_vedic_range_has_no_answer_for_a_tiny_line(chanda):
    assert chanda._vedic_range_match(5) is None


def test_heuristic_matches_are_grouped_by_kind():
    matches = [
        (("मालिनी", ("1",)), 6.0, "pada_sama"),
        ("त्रिष्टुभ्", 5.0, "vedic_syllable"),
        ("शालिनी", 4.0, "fuzzy"),
        ("other", 1.0, "unknown"),
    ]
    pada, syllable, fuzzy = LineFallbackMixin._group_heuristic_matches(matches)
    assert pada == [(("मालिनी", ("1",)), 6.0, "pada_sama")]
    assert syllable == [(("त्रिष्टुभ्", ("",)), 5.0, "vedic_syllable")]
    assert fuzzy == [(("शालिनी", ("",)), 4.0, "fuzzy")]


def test_add_line_matches_keeps_the_first_confidence_per_meter():
    chanda, confidence_map = [], {}
    LineFallbackMixin._add_line_matches(
        [(("मालिनी", ("1",)), 6.0, "pada_sama"), (("मालिनी", ("2",)), 3.0, "pada_sama")], chanda, confidence_map
    )
    assert confidence_map == {"मालिनी": (6.0, "pada_sama")}
    assert chanda == [("मालिनी", ("1",))]


def test_vedic_classical_map_raises_a_mapped_meter():
    confidence_map = {"tristubh": (4.0, "fuzzy"), "मालिनी": (4.0, "fuzzy")}
    LineFallbackMixin._apply_vedic_classical_line_map("त्रिष्टुभ्", confidence_map)
    assert confidence_map["tristubh"] == (CONFIDENCE_VEDIC_CLASSICAL_MAP, "vedic_classical_map_fuzzy")
    assert confidence_map["मालिनी"] == (4.0, "fuzzy")


def test_vedic_classical_map_needs_a_vedic_meter():
    confidence_map = {"tristubh": (4.0, "fuzzy")}
    LineFallbackMixin._apply_vedic_classical_line_map(None, confidence_map)
    assert confidence_map == {"tristubh": (4.0, "fuzzy")}


def test_vedic_names_cover_every_spelling_in_lower_case():
    assert {"गायत्री", "gāyatrī", "triṣṭubh", "virat"} <= VEDIC_METER_NAMES
    assert all(name == name.lower() for name in VEDIC_METER_NAMES)


def test_a_rigveda_line_off_the_standard_counts_gets_the_range_fallback(chanda):
    # RV 1.1.2 has 23 syllables in the corpus, one short of a Gāyatrī.
    result = chanda.identify_line("अग्निः पूर्वेभिर्ऋषिभिरीड्यो नूतनैरुत स देवाँ एह वक्षति")
    assert result["found"]
    meters = {name: kind for name, (_conf, kind) in result["confidence_scores"].items()}
    assert "गायत्री" in meters
