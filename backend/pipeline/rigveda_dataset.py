"""Build backend/evaluation/data/rigveda_authentic.py from two external corpora.

Inputs, cloned under one directory (``repos/`` at the repository root by default):

* ``Rigveda_api/data/rigveda.json``: verse texts, one object per ṛk with
  ``mandala``, ``hymn``, ``verse`` and ``sanskrit``.
* ``WSC2023/Anukramani/Mandala_<n>.txt``: the Anukramaṇī meter of every hymn,
  one dot-separated line per hymn with the meter in the fifth field.

Steps: parse the meter of each hymn, load and de-duplicate the verses, strip
Vedic accent marks, keep verses whose hymn has one of the seven major Vedic
meters, validate every record, and render the module. Rendering is
deterministic, so building twice from the same inputs writes the same bytes,
and ``--check`` exits 1 when the committed file differs from a fresh build.

    uv run python -m backend.pipeline.rigveda_dataset --repos repos
    uv run python -m backend.pipeline.rigveda_dataset --repos repos --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from backend.config import settings
from backend.pipeline.issues import Issue

OUTPUT_PATH = settings.BASE_DIR / "evaluation" / "data" / "rigveda_authentic.py"
DEFAULT_REPOS = settings.BASE_DIR.parent / "repos"
MIN_TEXT_LENGTH = 20


@dataclass(frozen=True)
class VedicMeter:
    devanagari: str
    syllables: int
    padas: str


_MAJOR_METERS = {
    'gāyatrī': VedicMeter('गायत्री', 24, '3×8'),
    'uṣṇik': VedicMeter('उष्णिक्', 28, '4×7'),
    'anuṣṭup': VedicMeter('अनुष्टुभ्', 32, '4×8'),
    'bṛhatī': VedicMeter('बृहती', 36, '4×9'),
    'paṅkti': VedicMeter('पङ्क्ति', 40, '5×8'),
    'triṣṭup': VedicMeter('त्रिष्टुभ्', 44, '4×11'),
    'jagatī': VedicMeter('जगती', 48, '4×12'),
}

# Remove these before comparing texts: udātta, anudātta, grave, acute and Vedic tone marks.
ACCENT_MARKS = ('॑', '॒', '॓', '॔', '᳐', '᳑', '᳒', '᳚')
RECORD_FIELDS = ('mandala', 'hymn', 'verse', 'text', 'meter', 'meter_iast', 'syllables', 'padas', 'source')
METER_WORD = re.compile(r'([a-zA-Zāīūṛḷṅñṭḍṇśṣḥṃ]+)(?:\s|,|$)')


def normalize_meter_name(name: str) -> str:
    """Lower-case meter name without diacritics or a final h, so 'Triṣṭup' and 'tristup' compare equal."""
    if not name:
        return ""
    name = unicodedata.normalize('NFD', name.lower().strip())
    name = ''.join(ch for ch in name if not unicodedata.combining(ch))
    return re.sub(r'h$', '', name)


MAJOR_METERS = {normalize_meter_name(iast): meter for iast, meter in _MAJOR_METERS.items()}


def major_meter(name: str) -> VedicMeter | None:
    return MAJOR_METERS.get(normalize_meter_name(name))


def parse_anukramani(lines: Iterable[str], mandala: int) -> dict[tuple[int, int], str]:
    """Primary meter of each hymn in one mandala's Anukramaṇī file; the first line is a header."""
    meters: dict[tuple[int, int], str] = {}
    for line in list(lines)[1:]:
        parts = line.strip().split('.')
        if len(parts) < 5 or not parts[0].strip().isdigit():
            continue
        # A meter field like "(1-6)jagatī,(7-9)triṣṭup" names several meters; keep the first.
        match = METER_WORD.search(parts[4])
        if match:
            meters[(mandala, int(parts[0]))] = match.group(1).lower()
    return meters


def read_anukramani(directory: Path) -> dict[tuple[int, int], str]:
    meters: dict[tuple[int, int], str] = {}
    for mandala in range(1, 11):
        path = directory / f'Mandala_{mandala}.txt'
        if path.exists():
            meters.update(parse_anukramani(path.read_text(encoding='utf-8').splitlines(), mandala))
    return meters


def clean_sanskrit_text(text: str) -> str:
    """Strip Vedic accent marks and collapse whitespace."""
    for mark in ACCENT_MARKS:
        text = (text or '').replace(mark, '')
    return ' '.join(text.split())


def unique_verses(raw: Iterable[dict]) -> list[dict]:
    """First occurrence of each (mandala, hymn, verse) with enough text, accents removed."""
    seen: set[tuple] = set()
    verses = []
    for entry in raw:
        key = (entry.get('mandala'), entry.get('hymn'), entry.get('verse'))
        sanskrit = entry.get('sanskrit', '')
        if not sanskrit or key in seen or len(sanskrit) <= MIN_TEXT_LENGTH:
            continue
        seen.add(key)
        verses.append({'mandala': key[0], 'hymn': key[1], 'verse': key[2], 'sanskrit': clean_sanskrit_text(sanskrit)})
    return verses


def merge(verses: Iterable[dict], hymn_meters: dict[tuple[int, int], str]) -> list[dict]:
    """One record per verse whose hymn has a major Vedic meter, in input order."""
    records = []
    for verse in verses:
        meter_iast = hymn_meters.get((verse['mandala'], verse['hymn']))
        meter = major_meter(meter_iast or '')
        if not meter:
            continue
        reference = f"{verse['mandala']}.{verse['hymn']}.{verse['verse']}"
        records.append(
            {
                'mandala': verse['mandala'],
                'hymn': verse['hymn'],
                'verse': verse['verse'],
                'text': verse['sanskrit'],
                'meter': meter.devanagari,
                'meter_iast': meter_iast,
                'syllables': meter.syllables,
                'padas': meter.padas,
                'source': f'RV {reference} (Rigveda_api + WSC2023)',
            }
        )
    return records


def validate_records(records: list[dict]) -> list[Issue]:
    """Structural problems that would make a record useless as ground truth."""
    issues = []
    seen: Counter[tuple] = Counter()
    for index, record in enumerate(records):
        subject = f"RV {record.get('mandala')}.{record.get('hymn')}.{record.get('verse')}"

        def issue(rule: str, detail: str, _index: int = index, _subject: str = subject) -> None:
            issues.append(Issue(OUTPUT_PATH.name, _index, _subject, rule, detail))

        missing = [name for name in RECORD_FIELDS if record.get(name) in (None, '')]
        if missing:
            issue('missing_field', ', '.join(missing))
            continue
        if not all(isinstance(record[name], int) and record[name] > 0 for name in ('mandala', 'hymn', 'verse')):
            issue('reference', 'mandala, hymn and verse must be positive integers')
        meter = major_meter(record['meter_iast'])
        if meter is None:
            issue('unknown_meter', record['meter_iast'])
        elif (meter.devanagari, meter.syllables, meter.padas) != (
            record['meter'],
            record['syllables'],
            record['padas'],
        ):
            issue('meter_fields', f"{record['meter']}, {record['syllables']}, {record['padas']} disagree")
        if "'" in record['text'] or '\\' in record['text']:
            issue('text_quote', 'the text cannot be written inside single quotes')
        key = (record['mandala'], record['hymn'], record['verse'])
        seen[key] += 1
        if seen[key] == 2:
            issue('duplicate_verse', 'the same verse appears twice')
    return issues


HEADER = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHENTIC Rigveda Test Verses with Ground Truth Meters

AUTO-GENERATED from:
- Verse texts: repos/Rigveda_api/data/rigveda.json
- Meter annotations: repos/WSC2023/Anukramani/

DO NOT EDIT MANUALLY - regenerate using:
    python backend/scripts/build_rigveda_dataset.py
"""

# ============================================================================
# AUTHENTIC RIGVEDA VERSES WITH GROUND TRUTH METERS
# ============================================================================

RIGVEDA_AUTHENTIC = [
'''

FOOTER = '''\
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_by_meter(meter_name):
    """Get verses by meter name."""
    return [
        v
        for v in RIGVEDA_AUTHENTIC
        if meter_name.lower() in v['meter'].lower() or meter_name.lower() in v['meter_iast'].lower()
    ]


def get_by_mandala(mandala):
    """Get verses by mandala number."""
    return [v for v in RIGVEDA_AUTHENTIC if v['mandala'] == mandala]


def summary():
    """Print dataset summary."""
    from collections import Counter

    meters = Counter(v['meter_iast'] for v in RIGVEDA_AUTHENTIC)

    print(f"\\nTotal verses: {len(RIGVEDA_AUTHENTIC)}")
    print("\\nBy meter:")
    for meter, count in meters.most_common():
        info = next((v for v in RIGVEDA_AUTHENTIC if v['meter_iast'] == meter), None)
        if info:
            print(f"  {info['meter']} ({meter}): {count} verses, {info['syllables']} syllables")


if __name__ == '__main__':
    summary()
'''


def render_record(record: dict) -> str:
    lines = ['    {']
    for name in RECORD_FIELDS:
        value = record[name]
        lines.append(f"        '{name}': {value if isinstance(value, int) else repr(value)},")
    lines.append('    },')
    return '\n'.join(lines) + '\n'


def render_module(records: list[dict]) -> str:
    """The generated module's source, formatted the way ruff formats it."""
    return HEADER + ''.join(render_record(record) for record in records) + FOOTER


def build(repos: Path) -> list[dict]:
    with (repos / 'Rigveda_api' / 'data' / 'rigveda.json').open(encoding='utf-8') as f:
        raw = json.load(f)
    return merge(unique_verses(raw), read_anukramani(repos / 'WSC2023' / 'Anukramani'))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Build rigveda_authentic.py from Rigveda_api and WSC2023.')
    parser.add_argument('--repos', type=Path, default=DEFAULT_REPOS, help='directory holding both clones')
    parser.add_argument('--check', action='store_true', help='compare with the committed file instead of writing')
    args = parser.parse_args(argv)

    records = build(args.repos)
    issues = validate_records(records)
    for issue in issues:
        print(issue, file=sys.stderr)
    if not records or issues:
        print(f'{len(records)} records, {len(issues)} invalid; nothing written', file=sys.stderr)
        return 1

    source = render_module(records)
    counts = Counter(record['meter_iast'] for record in records)
    print(f'{len(records)} verses: ' + ', '.join(f'{meter} {n}' for meter, n in counts.most_common()))
    if args.check:
        same = OUTPUT_PATH.read_text(encoding='utf-8') == source
        print(f'{OUTPUT_PATH.name} is {"up to date" if same else "out of date"}')
        return 0 if same else 1
    OUTPUT_PATH.write_text(source, encoding='utf-8')
    print(f'wrote {OUTPUT_PATH}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
