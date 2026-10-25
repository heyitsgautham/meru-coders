"""Meter-name matching and scoring for the accuracy benchmarks, on stub engines and tiny fixtures."""

import csv

import pytest

from backend.pipeline import benchmarks as bm


class TestClassicalNames:
    def test_strip_diacritics_reads_devanagari_and_iast_alike(self):
        assert bm.strip_diacritics("वसन्ततिलका") == bm.strip_diacritics("Vasantatilakā") == "vasantatilaka"

    def test_family_merges_variants_and_csv_typos(self):
        assert bm.classical_family("Upendravajrā") == bm.classical_family("Upajātiḥ") == "upajati"
        assert bm.classical_family("pythvi") == "prthvi"

    @pytest.mark.parametrize(
        ("expected", "predicted", "ok"),
        [
            ("Indravajrā", "उपजाति", True),
            ("Śārdūlavikrīḍitam", "शार्दूलविक्रीडित", True),
            ("Mālinī", "मालिनी", True),
            ("Mālinī", "मन्दाक्रान्ता", False),
            ("Mālinī", None, False),
        ],
    )
    def test_classical_match(self, expected, predicted, ok):
        assert bm.classical_match(expected, predicted) is ok


class TestRigvedaNames:
    @pytest.mark.parametrize(
        ("label", "meter"),
        [("gāyatrī", "गायत्री"), ("Triṣṭup", "त्रिष्टुभ्"), ("jagatiī", "जगती"), ("pragāthaḥ", "प्रगाथ")],
    )
    def test_labels_map_to_engine_names(self, label, meter):
        assert bm.rigveda_meter(label) == meter

    def test_labels_without_diacritics_still_map(self):
        assert bm.rigveda_meter("tristup") == "त्रिष्टुभ्"
        assert bm.rigveda_meter("mahapanktih") == "महापङ्क्ति"

    @pytest.mark.parametrize("label", ["(1-7)paṅktiḥ", "", "ekapadā"])
    def test_ranges_and_unknown_labels_are_skipped(self, label):
        assert bm.rigveda_meter(label) is None

    @pytest.mark.parametrize(
        ("expected", "predicted", "result"),
        [
            ("गायत्री", "गायत्री", (True, True)),
            ("गायत्री", "निचृद्गायत्री", (False, True)),
            ("प्रगाथ", "बृहती", (False, True)),
            ("जगती", "त्रिष्टुभ्", (False, True)),
            ("गायत्री", "जगती", (False, False)),
            ("गायत्री", None, (False, False)),
        ],
    )
    def test_rigveda_match(self, expected, predicted, result):
        assert bm.rigveda_match(expected, predicted) == result


class TestTally:
    def test_rate_and_misses(self):
        tally = bm.Tally()
        tally.add(True, "1", "a", "a")
        tally.add(False, "2", "a", "b")
        assert (tally.correct, tally.total, tally.rate) == (1, 2, 0.5)
        assert tally.misses == [("2", "a", "b")]

    def test_empty_rate_is_zero(self):
        assert bm.Tally().rate == 0.0


def line(meter):
    return {"result": {"chanda": [(meter, ("",))] if meter else []}}


class StubChanda:
    """Answers identify_from_text from a table of verse text to per-line and whole-verse meters."""

    def __init__(self, answers, vedic=None):
        self.answers = answers
        self.vedic = vedic or {}

    def identify_from_text(self, text, verse=False):
        lines, whole = self.answers[text]
        if verse:
            return {"result": {"verse": [{"chanda": ([whole], 1)}] if whole else []}}
        return {"result": {"line": [line(m) for m in lines]}}

    def _identify_vedic_mode(self, text):
        return {"meter": self.vedic.get(text)}

    def identify_line(self, text):
        return {"found": True, "chanda": [("त्रिष्टुभ्", ("",))]}


def test_score_classical_counts_each_measure():
    verses = [
        bm.LabelledVerse("row 1", "a", "Mālinī"),
        bm.LabelledVerse("row 2", "b", "Mālinī"),
    ]
    engine = StubChanda({"a": (["मालिनी", "मालिनी"], "मालिनी"), "b": (["मालिनी", "शालिनी"], None)})
    score = bm.score_classical(engine, verses)
    assert (score.first_line.correct, score.first_line.total) == (2, 2)
    assert (score.every_line.correct, score.lines.correct, score.lines.total) == (1, 3, 4)
    assert score.every_line.misses == [("row 2", "Mālinī", "शालिनी")]
    assert (score.whole_verse.correct, score.whole_verse.misses) == (1, [("row 2", "Mālinī", None)])


def test_score_rigveda_falls_back_to_the_line_matcher():
    verses = [bm.LabelledVerse("1.1.1", "a", "गायत्री"), bm.LabelledVerse("1.1.2", "b", "जगती")]
    score = bm.score_rigveda(StubChanda({}, vedic={"a": "गायत्री"}), verses)
    assert (score.exact.correct, score.accepted.correct) == (1, 2)
    assert score.by_meter["जगती"].misses == [("1.1.2", "जगती", "त्रिष्टुभ्")]


def test_load_classical_benchmark_stops_after_the_verse_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(bm, "CLASSICAL_VERSE_ROWS", 2)
    with (tmp_path / bm.CLASSICAL_BENCHMARK).open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Shloka", "L/G", "Gana", "chanda"])
        writer.writerow(["", "", "", "मालिनी"])
        writer.writerow(["पद्यम् एकम्", "", "", "मालिनी"])
        writer.writerow(["short"])
        writer.writerow(["पद्यम् द्वितीयम्", "", "", "शालिनी"])
        writer.writerow(["मालिनी definition row", "", "", "मालिनी"])
    verses = bm.load_classical_benchmark(tmp_path)
    assert [(v.ref, v.expected) for v in verses] == [("row 1", "मालिनी"), ("row 2", "शालिनी")]


def test_load_rigveda_benchmark_skips_unusable_rows_and_samples(tmp_path):
    with (tmp_path / bm.RIGVEDA_BENCHMARK).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["mandala", "sukta", "rik", "verse_text", "meter"])
        writer.writeheader()
        writer.writerow({"mandala": 1, "sukta": 1, "rik": 1, "verse_text": "अ", "meter": "gāyatrī"})
        writer.writerow({"mandala": 1, "sukta": 1, "rik": 2, "verse_text": "आ", "meter": "(1-7)paṅktiḥ"})
        writer.writerow({"mandala": 1, "sukta": 1, "rik": 3, "verse_text": "", "meter": "gāyatrī"})
        writer.writerow({"mandala": 1, "sukta": 1, "rik": 4, "verse_text": "इ", "meter": "triṣṭup"})
        writer.writerow({"mandala": 1, "sukta": 1, "rik": 5, "verse_text": "ई", "meter": "jagatī"})
    assert [v.ref for v in bm.load_rigveda_benchmark(tmp_path)] == ["1.1.1", "1.1.4", "1.1.5"]
    assert [v.ref for v in bm.load_rigveda_benchmark(tmp_path, every=2)] == ["1.1.1", "1.1.5"]
