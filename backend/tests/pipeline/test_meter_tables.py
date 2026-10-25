"""Rules for the meter definition CSVs, and the defects the committed tables still carry."""

import json
import re
from pathlib import Path

import pytest

from backend.config import settings
from backend.pipeline import meter_tables as mt

BASELINE = Path(mt.__file__).with_name("known_issues.json")


def row(name="इन्द्रवज्रा", pada="", gana="ततजगग", pattern="गगलगगललगलगग", syllables="11", matras="18"):
    return [name, pada, gana, pattern, syllables, matras, ""]


def rules(cells):
    return [issue.rule for issue in mt.check_row("chanda_sama.csv", 2, cells)]


def test_expand_gana_turns_each_gana_into_three_syllables():
    assert mt.expand_gana("य") == "लगग"
    assert mt.expand_gana("ततजगग") == "गगलगगललगलगग"
    assert mt.expand_gana("--लग") == "--लग"


def test_matra_count_weighs_guru_double():
    assert mt.matra_count("गगलगगललगलगग") == 18
    assert mt.matra_count("") == 0


def test_a_sound_row_has_no_issues():
    assert rules(row()) == []


def test_blank_rows_are_skipped_like_the_loader_does():
    assert rules(["", "", ""]) == []
    assert rules([]) == []


def test_latin_letters_in_the_gana_make_a_meter_unmatchable():
    assert rules(row(gana="ततजgg")) == ["gana_symbols"]


def test_raw_pattern_may_use_latin_l_and_g():
    assert rules(row(pattern="gglggllglgg")) == []


def test_pattern_with_other_symbols_is_reported():
    assert rules(row(pattern="ガガलगगललगलगग")) == ["pattern_symbols"]


def test_syllable_count_must_match_the_pattern_length():
    assert rules(row(syllables="12")) == ["syllable_count"]


def test_gana_must_expand_to_the_raw_pattern():
    assert rules(row(pattern="गगलगगललगलगल", matras="17")) == ["gana_expansion"]


def test_matra_count_must_match_the_pattern():
    assert rules(row(matras="17")) == ["matra_count"]


def test_wildcards_skip_the_exact_comparisons():
    assert rules(row(name="अनुष्टुभ्", gana="----लग--", pattern="----लग--", syllables="8", matras="3")) == []


def test_pada_numbers_stop_at_five():
    assert rules(row(pada="5")) == []
    assert rules(row(pada="6")) == ["pada"]


def test_rows_without_a_gana_column_are_reported():
    assert rules(["इन्द्रवज्रा", ""]) == ["missing_columns"]


def test_header_must_match(tmp_path):
    path = tmp_path / "chanda_sama.csv"
    path.write_text("name,pada,gana\nइन्द्रवज्रा,,ततजगग\n", encoding="utf-8")
    assert [issue.rule for issue in mt.check_file(path)] == ["header"]


def test_issue_reads_as_file_line_meter_rule():
    issue = mt.Issue("chanda_sama.csv", 7, "मालिनी", "syllable_count", "15 declared, pattern has 14")
    assert str(issue) == "chanda_sama.csv:7 मालिनी: syllable_count (15 declared, pattern has 14)"


@pytest.fixture(scope="module")
def committed_issues():
    return mt.check_definition_tables(settings.DATA_DIR)


def test_committed_tables_match_the_known_issue_baseline(committed_issues):
    """A new defect fails here; so does a fix, until known_issues.json records it."""
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))["meter_tables"]
    assert mt.count_by_rule(committed_issues) == baseline


def test_every_unmatchable_meter_is_an_imported_row(committed_issues):
    """The Latin gaṇa strings come from the ganesh.json and vṛttaratnākara imports, not hand-written rows."""
    unmatchable = [issue for issue in committed_issues if issue.rule == "gana_symbols"]
    assert unmatchable
    devanagari = re.compile("[\u0900-\u097f]")
    assert not [issue.meter for issue in unmatchable if devanagari.search(issue.meter)]
