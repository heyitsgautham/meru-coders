"""Checks for the verse corpora and the dataset registry.

Lineage of the files these checks cover:

* ``source/rigveda-with-meters.csv`` is the Rigveda with meter, seer and deity
  per ṛk. ``data/rigveda_with_meters_complete.csv`` is a byte-identical copy
  that the evaluation harnesses and the verse cache read.
* ``data/pragatha_pankti_verses.csv`` holds the Rigveda rows whose meter is a
  Pragātha or a Paṅkti, the compound meters the engine detects across verses.
* ``data/bhagavad_gita_verses.csv`` holds one Gita verse per row.
* ``data/examples.json`` holds the example verse per meter that /api/examples serves.
* ``source/dataset_sources.json`` is the registry behind /api/datasets.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from backend.pipeline.issues import Issue

RIGVEDA_COLUMNS = ["mandala", "sukta", "rik", "verse_text", "meter", "lg_pattern", "syllable_count", "seer", "divinity"]
RIGVEDA_SOURCE = "rigveda-with-meters.csv"
RIGVEDA_COPY = "rigveda_with_meters_complete.csv"
PRAGATHA_PANKTI = "pragatha_pankti_verses.csv"
GITA = "bhagavad_gita_verses.csv"
EXAMPLES = "examples.json"
REGISTRY = "dataset_sources.json"
COMPOUND_METER_MARKERS = ("pragāth", "paṅkti")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def rik_key(row: dict[str, str]) -> tuple[str, str, str]:
    return row["mandala"], row["sukta"], row["rik"]


def check_rigveda_rows(file: str, rows: list[dict[str, str]]) -> list[Issue]:
    """Rules every Rigveda row must satisfy; line numbers count the header as line 1."""
    issues: list[Issue] = []
    seen: Counter[tuple[str, str, str]] = Counter()
    for line, row in enumerate(rows, start=2):
        key = rik_key(row)
        subject = "RV " + ".".join(key)

        def issue(rule: str, detail: str, _subject: str = subject, _line: int = line) -> None:
            issues.append(Issue(file, _line, _subject, rule, detail))

        seen[key] += 1
        if seen[key] == 2:
            issue("duplicate_rik", "the same mandala, sukta and rik appear twice")
        if not all(part.isdigit() and int(part) > 0 for part in key) or not 1 <= int(key[0] or 0) <= 10:
            issue("reference", f"mandala {key[0]!r}, sukta {key[1]!r}, rik {key[2]!r}")
        if not row["verse_text"].strip():
            issue("empty_text", "no verse text")
        if not row["meter"].strip():
            issue("empty_meter", "no meter label")
        pattern = row["lg_pattern"]
        if set(pattern) - {"ल", "ग"}:
            issue("pattern_symbols", f"{pattern!r} is not written in ल and ग")
        if not row["syllable_count"].isdigit() or int(row["syllable_count"]) != len(pattern):
            issue("syllable_count", f"{row['syllable_count']} declared, pattern has {len(pattern)}")
    return issues


def is_compound_meter(meter: str) -> bool:
    return any(marker in meter for marker in COMPOUND_METER_MARKERS)


def derive_pragatha_pankti(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """The Rigveda rows of pragatha_pankti_verses.csv, in the file's order.

    The Pragātha rows come first, then the Paṅkti rows. Within each group the rows sort
    by mandala compared as text ("10" before "6"), then by sukta and rik as numbers.
    That is how the committed file was first written; keeping it lets the build
    reproduce the file byte for byte, and the golden snapshot samples it by position.
    """
    rows = list(rows)

    def order(row: dict[str, str]) -> tuple[str, int, int]:
        return row["mandala"], int(row["sukta"]), int(row["rik"])

    return [
        row for marker in COMPOUND_METER_MARKERS for row in sorted((r for r in rows if marker in r["meter"]), key=order)
    ]


def check_rigveda(data_dir: Path, source_dir: Path) -> list[Issue]:
    issues: list[Issue] = []
    header, rows = read_csv(source_dir / RIGVEDA_SOURCE)
    if header != RIGVEDA_COLUMNS:
        issues.append(Issue(RIGVEDA_SOURCE, 1, "header", "header", f"expected {RIGVEDA_COLUMNS}, found {header}"))
    issues.extend(check_rigveda_rows(RIGVEDA_SOURCE, rows))

    copy = data_dir / RIGVEDA_COPY
    if not copy.exists() or copy.read_bytes() != (source_dir / RIGVEDA_SOURCE).read_bytes():
        issues.append(Issue(RIGVEDA_COPY, 0, "file", "copy_drift", f"differs from source/{RIGVEDA_SOURCE}"))

    if not (data_dir / PRAGATHA_PANKTI).exists():
        issues.append(Issue(PRAGATHA_PANKTI, 0, "file", "missing_file", "run python -m backend.pipeline.build"))
        return issues
    _, compound = read_csv(data_dir / PRAGATHA_PANKTI)
    expected = {rik_key(row): row for row in derive_pragatha_pankti(rows)}
    actual = {rik_key(row): row for row in compound}
    for key in sorted(set(expected) - set(actual)):
        issues.append(Issue(PRAGATHA_PANKTI, 0, "RV " + ".".join(key), "missing_row", "compound meter row not copied"))
    for key in sorted(set(actual) - set(expected)):
        issues.append(Issue(PRAGATHA_PANKTI, 0, "RV " + ".".join(key), "extra_row", "not a compound meter row"))
    for key in sorted(set(actual) & set(expected)):
        if actual[key] != expected[key]:
            issues.append(Issue(PRAGATHA_PANKTI, 0, "RV " + ".".join(key), "row_drift", "differs from the Rigveda"))
    return issues


def check_gita(data_dir: Path) -> list[Issue]:
    header, rows = read_csv(data_dir / GITA)
    issues = []
    if header != ["verse_text"]:
        issues.append(Issue(GITA, 1, "header", "header", f"expected ['verse_text'], found {header}"))
    seen: set[str] = set()
    for line, row in enumerate(rows, start=2):
        text = (row.get("verse_text") or "").strip()
        if not text:
            issues.append(Issue(GITA, line, "verse", "empty_text", "no verse text"))
        elif text in seen:
            issues.append(Issue(GITA, line, text[:24], "duplicate_verse", "verse appears twice"))
        seen.add(text)
    return issues


def example_verses(entry: object) -> list[object]:
    """Example verses in one examples.json entry, in any of its three shapes."""
    if isinstance(entry, list):  # the verse's lines
        return ["\n".join(map(str, entry))] if entry else []
    if not isinstance(entry, dict):
        return []
    verses = list(entry.get("examples") or [])
    for category in (entry.get("categories") or {}).values():
        verses.extend(category.get("examples") or [])
    return verses


def check_examples(data_dir: Path) -> list[Issue]:
    with (data_dir / EXAMPLES).open(encoding="utf-8") as f:
        examples = json.load(f)
    issues = []
    for meter, entry in examples.items():
        verses = example_verses(entry)
        if not verses or not all(isinstance(v, str) and v.strip() for v in verses):
            issues.append(Issue(EXAMPLES, 0, meter, "examples", "needs at least one non-empty example verse"))
    return issues


def _registry_tables(dataset: dict) -> list[dict]:
    """One entry per CSV a registry dataset reads, merged datasets included."""
    if "files" in dataset:
        return dataset["files"]
    return [dataset]


def check_registry(source_dir: Path) -> list[Issue]:
    """Every registry entry names a file in backend/source/ that has the columns it declares."""
    with (source_dir / REGISTRY).open(encoding="utf-8") as f:
        registry = json.load(f)
    issues = []
    for dataset_id, dataset in registry.get("datasets", {}).items():
        for table in _registry_tables(dataset):
            filename = table.get("filename", "")
            path = source_dir / filename
            if not filename or not path.exists():
                issues.append(Issue(REGISTRY, 0, dataset_id, "missing_file", f"{filename!r} not in backend/source"))
                continue
            header, _ = read_csv(path)
            declared = {
                table.get("slokaColumn", dataset.get("slokaColumn")),
                table.get("chandasColumn", dataset.get("chandasColumn")),
                table.get("patternColumn", dataset.get("patternColumn")),
                *dataset.get("columns", {}).get("additional", []),
            } - {None}
            for column in sorted(declared - set(header)):
                issues.append(Issue(REGISTRY, 0, dataset_id, "missing_column", f"{filename} has no {column!r} column"))
    return issues


def check_corpora(data_dir: Path, source_dir: Path) -> list[Issue]:
    return [
        *check_rigveda(data_dir, source_dir),
        *check_gita(data_dir),
        *check_examples(data_dir),
        *check_registry(source_dir),
    ]
