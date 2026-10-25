"""The Rigveda ground-truth build: parsing, merging, validation and byte-stable rendering."""

import importlib
from pathlib import Path

import pytest

from backend.pipeline import rigveda_dataset as rd

FIXTURE_REPOS = Path(__file__).resolve().parents[1] / "fixtures" / "rigveda_repos"


def test_normalize_meter_name_drops_case_diacritics_and_a_final_h():
    assert rd.normalize_meter_name("Triṣṭup") == rd.normalize_meter_name("tristup") == "tristup"
    assert rd.normalize_meter_name("paṅktiḥ") == "pankti"
    assert rd.normalize_meter_name("") == ""


def test_parse_anukramani_keeps_the_first_meter_of_each_hymn():
    lines = [
        "sukta.verses.rsi.devata.chandas",
        "1.1-9.madhucchandāḥ.agniḥ.gāyatrī",
        "2.1-9.medhātithiḥ.indraḥ.(1-6)jagatī,(7-9)triṣṭup",
        "x.1.r.d.gāyatrī",
        "3.too.short",
    ]
    assert rd.parse_anukramani(lines, mandala=4) == {(4, 1): "gāyatrī", (4, 2): "jagatī"}


def test_clean_sanskrit_text_strips_accents_and_spaces():
    assert rd.clean_sanskrit_text("अ॒ग्निमी॑ळे  पु॒रोहि॑तं ") == "अग्निमीळे पुरोहितं"
    assert rd.clean_sanskrit_text("") == ""


def test_unique_verses_keeps_the_first_long_enough_copy():
    raw = [
        {"mandala": 1, "hymn": 1, "verse": 1, "sanskrit": "अग्निमीळे पुरोहितं यज्ञस्य"},
        {"mandala": 1, "hymn": 1, "verse": 1, "sanskrit": "अग्निमीळे पुरोहितं यज्ञस्य देवम्"},
        {"mandala": 1, "hymn": 1, "verse": 2, "sanskrit": "होतारं"},
        {"mandala": 1, "hymn": 1, "verse": 2, "sanskrit": "अग्निः पूर्वेभिर्ऋषिभिः"},
    ]
    verses = rd.unique_verses(raw)
    assert [(v["verse"], v["sanskrit"]) for v in verses] == [
        (1, "अग्निमीळे पुरोहितं यज्ञस्य"),
        (2, "अग्निः पूर्वेभिर्ऋषिभिः"),
    ]


def test_build_merges_fixture_corpora_into_records():
    records = rd.build(FIXTURE_REPOS)
    assert [(r["mandala"], r["hymn"], r["verse"], r["meter"], r["meter_iast"]) for r in records] == [
        (1, 1, 1, "गायत्री", "gāyatrī"),
        (1, 1, 2, "गायत्री", "gāyatrī"),
        (1, 2, 1, "जगती", "jagatī"),
        (2, 1, 1, "त्रिष्टुभ्", "triṣṭup"),
    ]
    assert records[0]["text"] == "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम् ।"
    assert records[0]["source"] == "RV 1.1.1 (Rigveda_api + WSC2023)"
    assert (records[3]["syllables"], records[3]["padas"]) == (44, "4×11")
    assert rd.validate_records(records) == []


def good_record(**changes):
    record = {
        "mandala": 1,
        "hymn": 1,
        "verse": 1,
        "text": "अग्निमीळे पुरोहितं",
        "meter": "गायत्री",
        "meter_iast": "gāyatrī",
        "syllables": 24,
        "padas": "3×8",
        "source": "RV 1.1.1 (Rigveda_api + WSC2023)",
    }
    return {**record, **changes}


@pytest.mark.parametrize(
    ("record", "rule"),
    [
        (good_record(text=""), "missing_field"),
        (good_record(hymn=0), "reference"),
        (good_record(meter_iast="virāṭ"), "unknown_meter"),
        (good_record(syllables=23), "meter_fields"),
        (good_record(text="it's"), "text_quote"),
    ],
)
def test_validate_records_reports_each_rule(record, rule):
    assert [issue.rule for issue in rd.validate_records([record])] == [rule]


def test_validate_records_reports_a_duplicate_verse_once():
    issues = rd.validate_records([good_record(), good_record(), good_record()])
    assert [issue.rule for issue in issues] == ["duplicate_verse"]


def test_rendered_module_round_trips_through_import(tmp_path, monkeypatch):
    records = rd.build(FIXTURE_REPOS)
    (tmp_path / "rendered_rigveda.py").write_text(rd.render_module(records), encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("rendered_rigveda")
    assert module.RIGVEDA_AUTHENTIC == records
    assert [v["verse"] for v in module.get_by_meter("jagatī")] == [1]
    assert len(module.get_by_mandala(1)) == 3


def test_main_writes_once_and_check_reports_drift(tmp_path, monkeypatch, capsys):
    output = tmp_path / "rigveda_authentic.py"
    monkeypatch.setattr(rd, "OUTPUT_PATH", output)

    assert rd.main(["--repos", str(FIXTURE_REPOS)]) == 0
    first = output.read_bytes()
    assert rd.main(["--repos", str(FIXTURE_REPOS)]) == 0
    assert output.read_bytes() == first, "a second build must write the same bytes"

    assert rd.main(["--repos", str(FIXTURE_REPOS), "--check"]) == 0
    output.write_text(first.decode("utf-8").replace("गायत्री", "जगती", 1), encoding="utf-8")
    assert rd.main(["--repos", str(FIXTURE_REPOS), "--check"]) == 1
    assert "out of date" in capsys.readouterr().out


def test_main_refuses_to_write_invalid_records(tmp_path, monkeypatch):
    output = tmp_path / "rigveda_authentic.py"
    monkeypatch.setattr(rd, "OUTPUT_PATH", output)
    monkeypatch.setattr(rd, "build", lambda repos: [good_record(meter_iast="virāṭ")])
    assert rd.main(["--repos", str(FIXTURE_REPOS)]) == 1
    assert not output.exists()


def test_committed_dataset_is_what_the_renderer_writes():
    """rigveda_authentic.py is generated; re-rendering its records must reproduce it byte for byte."""
    from backend.evaluation.data.rigveda_authentic import RIGVEDA_AUTHENTIC

    assert rd.render_module(RIGVEDA_AUTHENTIC) == rd.OUTPUT_PATH.read_text(encoding="utf-8")
    assert rd.validate_records(RIGVEDA_AUTHENTIC) == []
    assert len(RIGVEDA_AUTHENTIC) == 153
