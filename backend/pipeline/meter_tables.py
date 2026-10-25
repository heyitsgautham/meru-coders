"""Checks for the meter definition tables the engine loads at startup.

``Chanda.read_data`` builds its lookup tables from four CSVs in backend/data/.
Each row names a meter, optionally a pada number, and describes the pada as a
gaṇa string (य र त न भ ज स म plus ल and ग), its raw laghu-guru pattern, the
syllable count and the mātrā count. The engine matches only on the gaṇa
column, so a row whose gaṇa string holds anything else is loaded but can never
be identified. The other columns feed the pattern shown to users, and may be written in Latin
l and g as well as ल and ग.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

DEFINITION_FILES = ("chanda_sama.csv", "chanda_ardhasama.csv", "chanda_vishama.csv", "chanda_vedic.csv")
DEFINITION_HEADER = ["वृत्त", "पद", "लक्षण", "लक्षण (raw)", "अक्षरसङ्ख्या", "मात्रा", "यति"]

LAGHU, GURU = "ल", "ग"
GANA_PATTERNS = {
    "य": "लगग",
    "र": "गलग",
    "त": "गगल",
    "न": "ललल",
    "भ": "गलल",
    "ज": "लगल",
    "स": "ललग",
    "म": "गगग",
    LAGHU: LAGHU,
    GURU: GURU,
}
WILDCARD = "-"
# Rows imported from ganesh.json write the raw pattern in Latin l and g.
LATIN_PATTERN = str.maketrans({"l": LAGHU, "g": GURU})
# Vedic Paṅkti has five padas; classical meters have at most four.
ALLOWED_PADAS = {"", "1", "2", "3", "4", "5"}


@dataclass(frozen=True)
class Issue:
    file: str
    line: int
    meter: str
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line} {self.meter}: {self.rule} ({self.detail})"


def expand_gana(gana: str) -> str:
    """Laghu-guru pattern of a gaṇa string; a wildcard stays a wildcard."""
    return "".join(GANA_PATTERNS.get(symbol, symbol) for symbol in gana)


def matra_count(pattern: str) -> int:
    return pattern.count(LAGHU) + 2 * pattern.count(GURU)


def check_row(file: str, line: int, row: list[str]) -> list[Issue]:
    """Every rule a single definition row breaks; an empty list means the row is sound."""
    if not row or not row[0].strip():
        return []
    meter = row[0].strip()

    def issue(rule: str, detail: str) -> Issue:
        return Issue(file, line, meter, rule, detail)

    if len(row) < 3:
        return [issue("missing_columns", f"{len(row)} columns, the engine needs name, pada and gana")]

    cells = [cell.strip() for cell in row] + [""] * (len(DEFINITION_HEADER) - len(row))
    pada, gana, syllables, matras = cells[1], "".join(cells[2].split()), cells[4], cells[5]
    pattern = cells[3].translate(LATIN_PATTERN)
    issues: list[Issue] = []

    if pada not in ALLOWED_PADAS:
        issues.append(issue("pada", f"pada {pada!r}"))

    gana_ok = bool(gana) and set(gana) <= set(GANA_PATTERNS) | {WILDCARD}
    if gana and not gana_ok:
        stray = "".join(sorted(set(gana) - set(GANA_PATTERNS) - {WILDCARD}))
        issues.append(issue("gana_symbols", f"{gana!r} has {stray!r}, so the meter can never match"))

    pattern_ok = bool(pattern) and set(pattern) <= {LAGHU, GURU, WILDCARD}
    if pattern and not pattern_ok:
        issues.append(issue("pattern_symbols", f"{cells[3]!r} is not written in ल and ग or l and g"))

    if pattern_ok and syllables.isdigit() and int(syllables) != len(pattern):
        issues.append(issue("syllable_count", f"{syllables} declared, pattern has {len(pattern)}"))

    if gana_ok and pattern_ok and WILDCARD not in gana + pattern and expand_gana(gana) != pattern:
        issues.append(issue("gana_expansion", f"{gana!r} expands to {expand_gana(gana)!r}, pattern is {pattern!r}"))

    if pattern_ok and WILDCARD not in pattern and matras.isdigit() and int(matras) != matra_count(pattern):
        issues.append(issue("matra_count", f"{matras} declared, pattern counts {matra_count(pattern)}"))

    return issues


def check_file(path: Path) -> list[Issue]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return [Issue(path.name, 1, "", "header", "file is empty")]
    issues = []
    if rows[0] != DEFINITION_HEADER:
        issues.append(Issue(path.name, 1, "", "header", f"expected {DEFINITION_HEADER}, found {rows[0]}"))
    for line, row in enumerate(rows[1:], start=2):
        issues.extend(check_row(path.name, line, row))
    return issues


def check_definition_tables(data_dir: Path) -> list[Issue]:
    issues: list[Issue] = []
    for name in DEFINITION_FILES:
        issues.extend(check_file(data_dir / name))
    return issues


def count_by_rule(issues: list[Issue]) -> dict[str, int]:
    """Issue counts keyed ``file:rule``, the shape of the committed baseline."""
    counts = Counter(f"{issue.file}:{issue.rule}" for issue in issues)
    return dict(sorted(counts.items()))
