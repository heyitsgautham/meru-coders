"""The verse-level scoring steps of identify_from_text, one at a time."""

import json

from backend.core.chanda_constants import CONFIDENCE_VEDIC_CLASSICAL_MAP
from backend.core.chanda_verse import VerseScoringMixin as V

GITA_1_1 = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय॥"


class TestRankVerseMeters:
    def test_highest_score_wins(self):
        assert V._rank_verse_meters([("मालिनी", 4.0), ("शालिनी", 2.0)]) == (["मालिनी"], 4.0)

    def test_classical_meters_lead_a_tie_with_vedic_categories(self):
        ranked = V._rank_verse_meters([("त्रिष्टुभ्", 4.0), ("इन्द्रवज्रा", 4.0), ("शालिनी", 1.0)])
        assert ranked == (["इन्द्रवज्रा", "त्रिष्टुभ्"], 4.0)

    def test_no_scores(self):
        assert V._rank_verse_meters([]) == ([], 0)


def test_fuzzy_matches_naming_the_verse_meter_move_first():
    line = {"result": {"fuzzy": [{"chanda": [("शालिनी", "1")]}, {"chanda": [("मालिनी", "1")]}]}}
    V._prioritise_matching_fuzzy(line, (["मालिनी"], 3.0))
    assert [m["chanda"][0][0] for m in line["result"]["fuzzy"]] == ["मालिनी", "शालिनी"]


class TestVedicClassicalMap:
    def test_mapped_classical_meter_is_raised(self):
        scores = {"tristubh": (6.0, "partial"), "मालिनी": (6.0, "partial")}
        V._apply_vedic_classical_map({"found": True, "meter": "त्रिष्टुभ्"}, scores)
        assert scores["tristubh"] == (CONFIDENCE_VEDIC_CLASSICAL_MAP, "vedic_classical_map_partial")
        assert scores["मालिनी"] == (6.0, "partial")

    def test_higher_confidence_is_kept(self):
        scores = {"tristubh": (10.0, "exact")}
        V._apply_vedic_classical_map({"found": True, "meter": "त्रिष्टुभ्"}, scores)
        assert scores["tristubh"] == (10.0, "exact")

    def test_nothing_happens_without_a_holistic_meter(self):
        scores = {"tristubh": (6.0, "partial")}
        V._apply_vedic_classical_map(None, scores)
        V._apply_vedic_classical_map({"found": False}, scores)
        assert scores == {"tristubh": (6.0, "partial")}


class TestEffectiveMode:
    def test_requested_mode_passes_through(self):
        assert V._effective_mode_used("classical", []) == "classical"

    def test_auto_mode_reports_vedic_for_a_vedic_winner(self):
        assert V._effective_mode_used("auto", [{"chanda": (["गायत्री"], 9.0)}]) == "vedic"

    def test_auto_mode_reports_classical_otherwise(self):
        assert V._effective_mode_used("auto", [{"chanda": (["मालिनी"], 9.0)}]) == "classical"


def test_identify_from_text_writes_json_and_text_results(chanda, tmp_path):
    response = chanda.identify_from_text(GITA_1_1, verse=True, save_path=str(tmp_path))
    names = response["path"]
    assert names["json"].startswith("result_") and names["json"].endswith("_1_0.json")
    saved = json.loads((tmp_path / names["json"]).read_text(encoding="utf-8"))
    assert saved["verse"][0]["chanda"][0] == response["result"]["verse"][0]["chanda"][0]
    report = (tmp_path / names["txt"]).read_text(encoding="utf-8")
    assert report.startswith("# अनुष्टुभ्")


def test_without_a_save_path_nothing_is_written(chanda):
    assert chanda.identify_from_text(GITA_1_1, verse=True)["path"] == {"json": None, "txt": None}
