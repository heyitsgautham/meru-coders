"""Golden snapshot of the Chanda engine's output on 150 reference verses.

The verses come from five corpora: the Bhagavad Gita, the Rigveda, Rigvedic
Pragātha and Paṅkti verses, the meter examples served by ``/api/examples`` and
the Chandovallari classical meter list. Each verse runs through
``Chanda.identify_from_text`` in four configurations, and every result is
reduced to a SHA-256 of its canonical JSON plus the meter names it displays.

``backend/tests/test_engine_golden.py`` compares the engine against
``engine_snapshot.json``. Regenerate the file only for a change that is meant
to alter identification results, and review the meter diff it prints:

    uv run python -m backend.tests.golden.engine_snapshot --write
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

from backend.config import settings

SNAPSHOT_PATH = Path(__file__).with_name("engine_snapshot.json")
SOURCE_DIR = settings.BASE_DIR / "source"

# (verse, mode) pairs passed to identify_from_text for every verse.
CONFIGURATIONS: tuple[tuple[bool, str], ...] = (
    (True, "auto"),
    (False, "auto"),
    (True, "classical"),
    (True, "vedic"),
)


def config_key(verse: bool, mode: str) -> str:
    return f"{'verse' if verse else 'line'}:{mode}"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def select_verses(data_dir: Path = settings.DATA_DIR, source_dir: Path = SOURCE_DIR) -> list[dict[str, str]]:
    """Pick the 150 reference verses deterministically from the committed corpora."""
    picked: list[tuple[str, str]] = []

    gita = [row["verse_text"] for row in _read_csv(data_dir / "bhagavad_gita_verses.csv")]
    picked += [("gita", text) for text in gita[::14][:50]]

    rigveda = _read_csv(data_dir / "rigveda_with_meters_complete.csv")
    picked += [("rigveda", row["verse_text"]) for row in rigveda[::211][:50]]

    pragatha = _read_csv(data_dir / "pragatha_pankti_verses.csv")
    picked += [("pragatha", row["verse_text"]) for row in pragatha[::7][:20]]

    with (data_dir / "examples.json").open(encoding="utf-8") as f:
        examples = json.load(f)
    example_texts = [
        text for entry in examples.values() if isinstance(entry, dict) for text in entry.get("examples", [])
    ]
    picked += [("examples", text) for text in example_texts[:30]]

    with (source_dir / "chandovallari.csv").open(encoding="utf-8") as f:
        rows = list(csv.reader(f))[2:]
    classical = [row[0] for row in rows if row and row[0].strip()]
    picked += [("chandovallari", text) for text in classical[:: max(1, len(classical) // 23)][:23]]

    return [{"id": f"{i:03d}-{source}", "source": source, "text": text} for i, (source, text) in enumerate(picked)]


def displayed_meters(result: dict) -> list[str]:
    """The first meter name a user sees for each analysed line of one result."""
    lines = (result.get("result") or {}).get("line") or []
    return [((line.get("result") or {}).get("display_chanda") or "").split(" / ")[0] for line in lines]


def digest(result: dict) -> str:
    canonical = json.dumps(result, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def snapshot_verse(chanda, text: str) -> dict[str, dict[str, object]]:
    entry: dict[str, dict[str, object]] = {}
    for verse, mode in CONFIGURATIONS:
        result = chanda.identify_from_text(text, verse=verse, mode=mode)
        entry[config_key(verse, mode)] = {"meters": displayed_meters(result), "sha256": digest(result)}
    return entry


def build_snapshot(chanda) -> dict:
    verses = select_verses()
    return {
        "configurations": [config_key(v, m) for v, m in CONFIGURATIONS],
        "verses": [{**verse, "outputs": snapshot_verse(chanda, verse["text"])} for verse in verses],
    }


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_snapshot(snapshot: dict, path: Path = SNAPSHOT_PATH) -> None:
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1, separators=(",", ":")) + "\n", encoding="utf-8")


def diff_snapshots(expected: dict, actual: dict) -> list[str]:
    """Human-readable differences: changed meters first, then output-only changes."""
    changes: list[str] = []
    actual_by_id = {verse["id"]: verse for verse in actual["verses"]}
    for verse in expected["verses"]:
        other = actual_by_id.get(verse["id"])
        if other is None:
            changes.append(f"{verse['id']}: missing from the new snapshot")
            continue
        for key, old in verse["outputs"].items():
            new = other["outputs"].get(key)
            if new == old:
                continue
            if new is None or new["meters"] != old["meters"]:
                new_meters = None if new is None else new["meters"]
                changes.append(f"{verse['id']} [{key}] meters {old['meters']} -> {new_meters}")
            else:
                changes.append(f"{verse['id']} [{key}] same meters, different result payload")
    return changes


def main(argv: list[str] | None = None) -> int:
    from backend.core.chanda import Chanda

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="overwrite engine_snapshot.json with the current output")
    args = parser.parse_args(argv)

    snapshot = build_snapshot(Chanda(str(settings.DATA_DIR)))
    if SNAPSHOT_PATH.exists():
        for line in diff_snapshots(load_snapshot(), snapshot):
            print(line)
    if args.write:
        write_snapshot(snapshot)
        print(f"wrote {SNAPSHOT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
