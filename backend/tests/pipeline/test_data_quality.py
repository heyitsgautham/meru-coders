"""Data-quality gates on the committed datasets: schema, row counts, the gana alphabet and duplicates.

These run on the real files in every CI run. A change to a dataset that alters its shape
or size has to change the matching number here in the same commit, so it is reviewed.

Known defects are not hidden. The gana-alphabet check is marked xfail(strict=True), so it
shows as an expected failure until the rows are fixed, and a separate test fails as soon
as the number of bad rows grows past the count recorded in known_issues.json.
"""

from collections import Counter
from pathlib import Path

import pytest

from backend.config import settings
from backend.pipeline import benchmarks, corpora, meter_tables
from backend.pipeline.issues import load_known_issues

DATA = settings.DATA_DIR
SOURCE = settings.BASE_DIR / "source"


def csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    return corpora.read_csv(path)


# ---------------------------------------------------------------- schema and row counts


@pytest.mark.parametrize(
    ("file", "rows"),
    [("chanda_sama.csv", 1506), ("chanda_ardhasama.csv", 170), ("chanda_vishama.csv", 199), ("chanda_vedic.csv", 28)],
)
def test_meter_definition_tables_have_their_schema_and_size(file, rows):
    header, body = csv_rows(DATA / file)
    assert header == meter_tables.DEFINITION_HEADER
    assert len(body) == rows


def test_every_meter_row_has_a_name_apart_from_blank_spacer_lines():
    """Sama has one all-empty line and vishama 15; the engine skips them. Anything else needs a name."""
    blank_lines = {}
    for file in meter_tables.DEFINITION_FILES:
        _, body = csv_rows(DATA / file)
        unnamed = [row for row in body if not row["वृत्त"].strip()]
        assert all(not any(value.strip() for value in row.values()) for row in unnamed), (
            f"{file}: a row has data but no name"
        )
        blank_lines[file] = len(unnamed)
    assert blank_lines == {
        "chanda_sama.csv": 1,
        "chanda_ardhasama.csv": 0,
        "chanda_vishama.csv": 15,
        "chanda_vedic.csv": 0,
    }


@pytest.mark.parametrize(
    ("file", "header", "rows"),
    [("chanda_jaati.csv", ["अक्षरसंख्या", "जाति"], 27), ("chanda_matra.csv", ["वृत्त", "मात्रा", "पर्यायवाचि"], 9)],
)
def test_jaati_and_matra_tables_have_their_schema_and_size(file, header, rows):
    found, body = csv_rows(DATA / file)
    assert found == header
    assert len(body) == rows


@pytest.mark.parametrize(
    ("path", "rows"),
    [
        (SOURCE / corpora.RIGVEDA_SOURCE, 10383),
        (DATA / corpora.RIGVEDA_COPY, 10383),
        (DATA / corpora.PRAGATHA_PANKTI, 676),
    ],
)
def test_rigveda_files_have_their_schema_and_size(path, rows):
    header, body = csv_rows(path)
    assert header == corpora.RIGVEDA_COLUMNS
    assert len(body) == rows


def test_gita_has_its_schema_and_size():
    header, body = csv_rows(DATA / corpora.GITA)
    assert header == ["verse_text"]
    assert len(body) == 696


def test_classical_benchmark_has_147_labelled_verses():
    verses = benchmarks.load_classical_benchmark(DATA)
    assert len(verses) == benchmarks.CLASSICAL_VERSE_ROWS == 147
    assert all(verse.text.strip() for verse in verses)
    # Row 6 has a verse but no meter label; the published figures count it as a miss.
    assert [verse.ref for verse in verses if not verse.expected] == ["row 6"]


# ---------------------------------------------------------------- duplicates


def test_no_rk_appears_twice_in_the_rigveda():
    _, rows = csv_rows(SOURCE / corpora.RIGVEDA_SOURCE)
    repeated = [key for key, n in Counter(map(corpora.rik_key, rows)).items() if n > 1]
    assert repeated == []


def test_no_gita_verse_appears_twice():
    _, rows = csv_rows(DATA / corpora.GITA)
    repeated = [text[:30] for text, n in Counter(row["verse_text"].strip() for row in rows).items() if n > 1]
    assert repeated == []


def test_the_classical_benchmark_repeats_only_its_one_known_verse():
    """Rows 4 and 67 hold the same Bhujaṅgaprayāta verse; the published 147-verse figures count both."""
    verses = benchmarks.load_classical_benchmark(DATA)
    repeated = {verse.text for verse in verses if sum(other.text == verse.text for other in verses) > 1}
    assert len(repeated) <= 1
    assert all(text.startswith("न तातो न माता") for text in repeated)


# ---------------------------------------------------------------- the gana alphabet

GANA_ISSUES = "gana_symbols"


def gana_alphabet_violations() -> Counter[str]:
    issues = meter_tables.check_definition_tables(DATA)
    return Counter(issue.file for issue in issues if issue.rule == GANA_ISSUES)


@pytest.mark.xfail(
    strict=True,
    reason="known defect: 1,204 imported rows write the gana column outside the alphabet "
    "(Latin l/g in sama and ardhasama, pada labels in vishama); fixing them changes engine output",
)
def test_every_gana_uses_only_the_gana_alphabet():
    assert sum(gana_alphabet_violations().values()) == 0


def test_rows_outside_the_gana_alphabet_do_not_grow_past_the_recorded_count():
    recorded = {
        key.split(":")[0]: count
        for key, count in load_known_issues()["meter_tables"].items()
        if key.endswith(f":{GANA_ISSUES}")
    }
    assert sum(recorded.values()) == 1204
    found = gana_alphabet_violations()
    grown = {file: (found[file], recorded.get(file, 0)) for file in found if found[file] > recorded.get(file, 0)}
    assert grown == {}, f"new rows outside the gana alphabet (found, recorded): {grown}"


def test_the_curated_devanagari_rows_are_all_clean():
    """The rows the engine can match carry only य र त न भ ज स म ल ग and '-'."""
    allowed = set(meter_tables.GANA_PATTERNS) | {meter_tables.WILDCARD}
    for file in meter_tables.DEFINITION_FILES:
        _, rows = csv_rows(DATA / file)
        devanagari = [row["लक्षण"] for row in rows if row["लक्षण"] and not any(c.isascii() for c in row["लक्षण"])]
        stray = {gana for gana in devanagari if set(gana) - allowed and "द" not in gana}
        assert stray == set(), f"{file}: {sorted(stray)[:5]}"
