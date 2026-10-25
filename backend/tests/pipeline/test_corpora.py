"""Rules for the verse corpora and the dataset registry, on small fixtures and on the committed data."""

import csv
import json
import shutil

import pytest

from backend.config import settings
from backend.pipeline import corpora
from backend.pipeline.issues import count_by_rule, load_known_issues

SOURCE_DIR = settings.BASE_DIR / "source"


def rik(mandala="1", sukta="1", rik_no="1", text="अग्निमीळे पुरोहितं", meter="gāyatrī", pattern="गगलगलगगग", syllables=None):
    return {
        "mandala": mandala,
        "sukta": sukta,
        "rik": rik_no,
        "verse_text": text,
        "meter": meter,
        "lg_pattern": pattern,
        "syllable_count": str(len(pattern)) if syllables is None else syllables,
        "seer": "madhucchandāḥ",
        "divinity": "agniḥ",
    }


def rules(rows):
    return [issue.rule for issue in corpora.check_rigveda_rows("rv.csv", rows)]


def write_csv(path, rows, header=corpora.RIGVEDA_COLUMNS):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


class TestRigvedaRows:
    def test_a_sound_row_has_no_issues(self):
        assert rules([rik()]) == []

    def test_a_repeated_reference_is_reported_once(self):
        assert rules([rik(), rik(), rik()]) == ["duplicate_rik"]

    @pytest.mark.parametrize(("mandala", "sukta"), [("11", "1"), ("0", "1"), ("1", "x")])
    def test_references_must_be_positive_and_in_ten_mandalas(self, mandala, sukta):
        assert rules([rik(mandala=mandala, sukta=sukta)]) == ["reference"]

    def test_text_and_meter_are_required(self):
        assert rules([rik(text=" ", meter="")]) == ["empty_text", "empty_meter"]

    def test_pattern_is_written_in_laghu_and_guru(self):
        assert rules([rik(pattern="गगLग")]) == ["pattern_symbols"]

    def test_syllable_count_matches_the_pattern(self):
        assert rules([rik(syllables="7")]) == ["syllable_count"]

    def test_issue_line_numbers_count_the_header(self):
        issues = corpora.check_rigveda_rows("rv.csv", [rik(), rik(rik_no="2", meter="")])
        assert [(issue.line, issue.subject) for issue in issues] == [(3, "RV 1.1.2")]


class TestCompoundMeters:
    def test_pragatha_and_pankti_rows_are_kept(self):
        rows = [rik(meter="pragāthaḥ"), rik(rik_no="2", meter="mahāpaṅktiḥ"), rik(rik_no="3", meter="triṣṭup")]
        assert [row["rik"] for row in corpora.derive_pragatha_pankti(rows)] == ["1", "2"]

    def test_ranged_labels_count_as_compound(self):
        assert corpora.is_compound_meter("(1-7)paṅktiḥ")
        assert not corpora.is_compound_meter("gāyatrī")


@pytest.fixture
def corpus_dirs(tmp_path):
    """A copy of the corpus layout with three Rigveda rows, one of them a Pragātha."""
    data_dir, source_dir = tmp_path / "data", tmp_path / "source"
    data_dir.mkdir()
    source_dir.mkdir()
    rows = [rik(), rik(rik_no="2", meter="pragāthaḥ"), rik(rik_no="3", meter="triṣṭup")]
    write_csv(source_dir / corpora.RIGVEDA_SOURCE, rows)
    shutil.copy(source_dir / corpora.RIGVEDA_SOURCE, data_dir / corpora.RIGVEDA_COPY)
    write_csv(data_dir / corpora.PRAGATHA_PANKTI, [rows[1]])
    write_csv(data_dir / corpora.GITA, [{"verse_text": "धर्मक्षेत्रे कुरुक्षेत्रे"}], header=["verse_text"])
    (data_dir / corpora.EXAMPLES).write_text(json.dumps({"गायत्री": {"examples": ["अग्निमीळे"]}}), encoding="utf-8")
    write_csv(source_dir / "verses.csv", [{"sloka": "x", "chanda": "y"}], header=["sloka", "chanda"])
    registry = {"datasets": {"verses": {"filename": "verses.csv", "slokaColumn": "sloka", "chandasColumn": "chanda"}}}
    (source_dir / corpora.REGISTRY).write_text(json.dumps(registry), encoding="utf-8")
    return data_dir, source_dir


def corpus_rules(data_dir, source_dir):
    return [issue.rule for issue in corpora.check_corpora(data_dir, source_dir)]


class TestCorpusFiles:
    def test_a_consistent_layout_has_no_issues(self, corpus_dirs):
        assert corpus_rules(*corpus_dirs) == []

    def test_the_data_copy_must_match_the_source(self, corpus_dirs):
        data_dir, source_dir = corpus_dirs
        with (data_dir / corpora.RIGVEDA_COPY).open("a", encoding="utf-8") as f:
            f.write("1,1,4,नवः,gāyatrī,ग,1,x,y\n")
        assert corpus_rules(data_dir, source_dir) == ["copy_drift"]

    def test_compound_meter_file_must_hold_exactly_the_compound_rows(self, corpus_dirs):
        data_dir, source_dir = corpus_dirs
        write_csv(data_dir / corpora.PRAGATHA_PANKTI, [rik(rik_no="3", meter="triṣṭup")])
        assert corpus_rules(data_dir, source_dir) == ["missing_row", "extra_row"]

    def test_compound_meter_rows_must_match_the_rigveda(self, corpus_dirs):
        data_dir, source_dir = corpus_dirs
        write_csv(data_dir / corpora.PRAGATHA_PANKTI, [rik(rik_no="2", meter="pragāthaḥ", text="बदलम्")])
        assert corpus_rules(data_dir, source_dir) == ["row_drift"]

    def test_gita_verses_are_unique_and_non_empty(self, corpus_dirs):
        data_dir, source_dir = corpus_dirs
        verses = [{"verse_text": "एकम्"}, {"verse_text": "एकम्"}, {"verse_text": " "}]
        write_csv(data_dir / corpora.GITA, verses, header=["verse_text"])
        assert corpus_rules(data_dir, source_dir) == ["duplicate_verse", "empty_text"]

    def test_every_meter_in_examples_needs_a_verse(self, corpus_dirs):
        data_dir, source_dir = corpus_dirs
        examples = {
            "गायत्री": {"examples": []},
            "शालिनी": ["माथा", "पादौ"],
            "दण्डक": {"categories": {"लघु": {"examples": ["रामो राजमणिः"]}}},
        }
        (data_dir / corpora.EXAMPLES).write_text(json.dumps(examples), encoding="utf-8")
        issues = corpora.check_corpora(data_dir, source_dir)
        assert [(issue.rule, issue.subject) for issue in issues] == [("examples", "गायत्री")]

    def test_registry_files_and_columns_must_exist(self, corpus_dirs):
        data_dir, source_dir = corpus_dirs
        registry = {
            "datasets": {
                "verses": {"filename": "verses.csv", "slokaColumn": "text", "chandasColumn": "chanda"},
                "gone": {"filename": "gone.csv"},
                "merged": {"files": [{"filename": "verses.csv", "chandasColumn": "meter"}]},
            }
        }
        (source_dir / corpora.REGISTRY).write_text(json.dumps(registry), encoding="utf-8")
        issues = corpora.check_corpora(data_dir, source_dir)
        assert [(issue.rule, issue.subject) for issue in issues] == [
            ("missing_column", "verses"),
            ("missing_file", "gone"),
            ("missing_column", "merged"),
        ]


def test_committed_corpora_match_the_known_issue_baseline():
    issues = corpora.check_corpora(settings.DATA_DIR, SOURCE_DIR)
    assert count_by_rule(issues) == load_known_issues()["corpora"]
