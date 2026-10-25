"""PadaSplitter: meter tables from the CSVs, syllable counting, and splitting verses into padas."""

import pytest

from backend.config import settings
from backend.utils.pada_meters import PadaMeterCatalog
from backend.utils.pada_splitter import Pada, PadaSplitter, SplitResult
from backend.utils.pada_syllables import PadaSyllables

GITA_1_1 = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय"


@pytest.fixture(scope="module")
def splitter():
    return PadaSplitter(str(settings.DATA_DIR))


class TestMeterCatalog:
    def test_splitter_combines_both_mixins(self):
        assert issubclass(PadaSplitter, PadaMeterCatalog)
        assert issubclass(PadaSplitter, PadaSyllables)

    def test_csv_meters_load(self, splitter):
        assert len(splitter.vishama_patterns) == 45
        assert len(splitter.ardhasama_patterns) == 8

    def test_missing_data_dir_loads_nothing(self, tmp_path):
        empty = PadaSplitter(str(tmp_path))
        assert empty.vishama_patterns == {} and empty.ardhasama_patterns == {}
        assert empty.get_meter_info("anushtubh")["syllable_pattern"] == [8, 8, 8, 8]

    def test_udgata_has_unequal_padas(self, splitter):
        padas = [splitter.get_vishama_pattern("उद्गता", n)["syllables"] for n in (1, 2, 3, 4)]
        assert padas == [10, 10, 11, 13]
        assert splitter.get_vishama_pattern("उद्गता", 9) is None

    def test_meter_kinds(self, splitter):
        assert splitter.is_vishama_meter("उद्गता")
        assert not splitter.is_vishama_meter("अनुष्टुभ्")
        assert splitter.is_ardhasama_meter("अपरवक्त्र")
        assert not splitter.is_ardhasama_meter("उद्गता")

    def test_meter_info(self, splitter):
        udgata = splitter.get_meter_info("उद्गता")
        assert (udgata["type"], udgata["total_syllables"], udgata["pada_count"]) == ("viṣamavṛtta", 44, 4)
        assert udgata["padas"][1]["gana"] == "सजसल"
        assert splitter.get_meter_info("anushtubh") == {
            "name": "anushtubh",
            "type": "sama",
            "total_syllables": 32,
            "pada_count": 4,
            "syllable_pattern": [8, 8, 8, 8],
        }
        assert splitter.get_meter_info("nonexistent") is None

    @pytest.mark.parametrize(("name", "key"), [("अनुष्टुप्", "anushtubh"), ("Shloka", "anushtubh"), ("गायत्री", "gayatri")])
    def test_names_and_aliases_normalise(self, splitter, name, key):
        assert splitter._normalize_meter_name(name) == key

    def test_vishama_meters_get_ascii_keys(self, splitter):
        assert splitter._create_meter_key("उद्गता") == "udgata"
        assert "udgata" in splitter.get_available_meters()


class TestSyllables:
    def test_script_detection(self, splitter):
        assert splitter._detect_script(GITA_1_1) == "devanagari"
        assert splitter._detect_script("dharmakṣetre") == "iast"

    def test_counts_match_across_scripts(self, splitter):
        assert splitter.count_syllables(GITA_1_1) == 32
        assert splitter.count_syllables("धर्मक्षेत्रे") == splitter.count_syllables("dharmakṣetre") == 4

    def test_syllable_positions_cover_the_word(self, splitter):
        positions = splitter.get_syllables_with_positions("धर्मक्षेत्रे")
        assert [s for s, _start, _end in positions] == ["ध", "र्म", "क्षे", "त्रे"]
        assert positions[-1][2] == len("धर्मक्षेत्रे")


class TestSplitting:
    def test_gita_shloka_splits_into_four_whole_word_padas(self, splitter):
        result = splitter.split_verse(GITA_1_1, meter="anushtubh")
        assert result.success
        assert [p.text for p in result.padas] == [
            "धर्मक्षेत्रे कुरुक्षेत्रे",
            "समवेता युयुत्सवः",
            "मामकाः पाण्डवाश्चैव",
            "किमकुर्वत सञ्जय",
        ]
        assert [p.syllable_count for p in result.padas] == [8, 8, 8, 8]
        assert [p.position for p in result.padas] == [1, 2, 3, 4]

    def test_auto_split_finds_anushtubh_from_the_syllable_count(self, splitter):
        assert splitter.auto_split(GITA_1_1).meter == "anushtubh"

    def test_unknown_meter_reports_no_padas(self, splitter):
        result = splitter.split_verse(GITA_1_1, meter="nonexistent")
        assert result.meter_pattern == []
        assert result.padas == []

    def test_results_print_one_pada_per_line(self):
        result = SplitResult("x", "anushtubh", [8], [Pada("धर्मक्षेत्रे कुरुक्षेत्रे", 8, 1)], 8, True, "ok")
        assert "Pada 1: धर्मक्षेत्रे कुरुक्षेत्रे (8 syllables)" in str(result)
        assert str(Pada("समवेता", 4, 2)) == "Pada 2: समवेता (4 syllables)"
