"""Labelled verse sets and the scoring the accuracy reports and tests share.

Two benchmarks:

* Classical: the first 147 rows of ``data/page 1-47 chanda list - complete.csv``
  are real verses labelled with a classical meter. The rows after them define
  meters rather than quote verses, so they are not scored.
* Rigveda: ``data/rigveda_with_meters_complete.csv`` labels every ṛk with its
  Vedic meter from the Anukramaṇī. Rows labelled with a verse range such as
  ``(1-7)paṅktiḥ`` and meters outside ``RIGVEDA_METER_NAMES`` are skipped.

A prediction counts as correct when it names the expected meter or a meter of
the same family; the family tables encode which meters share a syllable pattern
or overlap in the Rigveda data.
"""

from __future__ import annotations

import csv
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

CLASSICAL_BENCHMARK = "page 1-47 chanda list - complete.csv"
CLASSICAL_VERSE_ROWS = 147

# Accuracy floors: the counts the engine reaches today. tests/test_corpus_accuracy.py asserts them,
# and csv_accuracy.py and rigveda_validation.py exit 1 below them. Raise them when the engine improves.
CLASSICAL_FLOORS = {"first_line": 146, "every_line": 134, "lines": 485, "whole_verse": 139}
# The published headline: 139 of 147 whole verses, 94.6% to one decimal place.
WHOLE_VERSE_PERCENT_FLOOR = 94.6
RIGVEDA_FLOORS = {"exact": 8067, "accepted": 9009}
RIGVEDA_BENCHMARK = "rigveda_with_meters_complete.csv"

# Classical meters with the same or a near-identical pattern, keyed by their
# diacritic-free IAST name. The CSV's own misspellings map here as well.
CLASSICAL_FAMILIES = {
    'anustup': 'anustubh',
    'anustubh': 'anustubh',
    'rsabhagajavilasita': 'anustubh',
    'pythvi': 'prthvi',
    'prthvi': 'prthvi',
    'prthi': 'prthvi',
    'sardulavkridita': 'sardula',
    'sardulavikriditam': 'sardula',
    'sardulavikridita': 'sardula',
    'meghavisphurjita': 'sardula',
    'sardulalaltiam': 'sardula',
    'upajatih': 'upajati',
    'upajati': 'upajati',
    'indravajra': 'upajati',
    'upendravajra': 'upajati',
    'ihamrgi': 'upajati',
    'sumukhi': 'upajati',
    'vamsasthavilam': 'vamsastha',
    'vamsasthavila': 'vamsastha',
    'vamsastha': 'vamsastha',
    'indravamsa': 'vamsastha',
    'bhujangaprayatam': 'vamsastha',
    'bhujangaprayata': 'vamsastha',
    'candravartma': 'vamsastha',
    'vasantatilakam': 'vasantatilaka',
    'vasantatilaka': 'vasantatilaka',
    'tunaka': 'tunaka',
    'camara': 'tunaka',
    'tunakam': 'tunaka',
    'pancacamaram': 'pancacamara',
    'pancacamara': 'pancacamara',
    'рancacamaram': 'pancacamara',  # Cyrillic р in the CSV
    'srih': 'nari',
    'stri': 'nari',
    'nari': 'nari',
    'sragdhara': 'sragdhara',
    'pancakavali': 'sragdhara',
    'mandakranta': 'mandakranta',
    'atisayini': 'mandakranta',
    'praharsini': 'praharsini',
    'kalahamsa': 'praharsini',
    'bhujangasangata': 'bhujanga',
    'bhujagasisubhrta': 'bhujanga',
}

# Rigveda meter labels (IAST, as the corpus writes them) to the engine's Devanagari names.
RIGVEDA_METER_NAMES = {
    # Standard Vedic meters (7 major)
    'gāyatrī': 'गायत्री',
    'gayatri': 'गायत्री',
    'uṣṇik': 'उष्णिक्',
    'uṣnik': 'उष्णिक्',
    'usnik': 'उष्णिक्',
    'anuṣṭup': 'अनुष्टुभ्',
    'anuṣṭubh': 'अनुष्टुभ्',
    'anustup': 'अनुष्टुभ्',
    'bṛhatī': 'बृहती',
    'brhati': 'बृहती',
    'paṅktiḥ': 'पङ्क्ति',
    'paṅkti': 'पङ्क्ति',
    'pankti': 'पङ्क्ति',
    'triṣṭup': 'त्रिष्टुभ्',
    'triṣṭubh': 'त्रिष्टुभ्',
    'tristup': 'त्रिष्टुभ्',
    'jagatī': 'जगती',
    'jagati': 'जगती',
    'jagatiī': 'जगती',  # Typo in dataset
    # Extended Vedic meters
    'virāṭ': 'विराट्',
    'virat': 'विराट्',
    'pragāthaḥ': 'प्रगाथ',
    'pragātha': 'प्रगाथ',
    'mahāpaṅktiḥ': 'महापङ्क्ति',
    'mahāpaṅkti': 'महापङ्क्ति',
    'atyaṣṭiḥ': 'अत्यष्टि',
    'atyaṣṭi': 'अत्यष्टि',
    'atyaṣtiḥ': 'अत्यष्टि',  # Alternate spelling
    'aṣṭiḥ': 'अष्टि',
    'aṣṭi': 'अष्टि',
    'jyotiḥ': 'ज्योतिस्',
    'jyotis': 'ज्योतिस्',
    'śakvarī': 'शक्वरी',
    'atiśakvarī': 'अतिशक्वरी',
    'kakup': 'ककुभ्',
    'kakubh': 'ककुभ्',
    'atijagatī': 'अतिजगती',
    'atijagati': 'अतिजगती',
    'dhṛtiḥ': 'धृति',
    'dhṛti': 'धृति',
    'kṛtiḥ': 'कृति',
    'kṛti': 'कृति',
    'ādhṛtiḥ': 'आधृति',
    'ādhṛti': 'आधृति',
    # Dvipadā variants
    'dvipadā virāṭ': 'द्विपदा विराट्',
    'dvipadā triṣṭup': 'द्विपदा त्रिष्टुभ्',
    'dvipadā': 'द्विपदा',
    # Other variants
    'prastārapaṅktiḥ': 'प्रस्तारपङ्क्ति',
    'abhisāriṇī': 'अभिसारिणी',
    'vardhamānā': 'वर्धमाना',
    'tanuśirā': 'तनुशिरा',
    'pipīlikamadhyā': 'पिपीलिकमध्या',
    'nyaṅkurāriṇī': 'न्यङ्कुरारिणी',
    'naṣṭarūpī': 'नष्टरूपी',
    'mahābṛhatī': 'महाबृहती',
    'kakumnyaṅkuśirā': 'ककुभ्न्यङ्कुशिरा',
    'atinicṛt': 'अतिनिचृत्',
    'pura uṣṇik': 'पुर उष्णिक्',
}

# Vedic meters that the engine may report for one another without counting as a miss.
RIGVEDA_FAMILIES = {
    'गायत्री': ['गायत्री', 'निचृद्गायत्री', 'भुरिग्गायत्री'],
    'उष्णिक्': ['उष्णिक्', 'पुर उष्णिक्', 'ककुभ्'],
    'अनुष्टुभ्': ['अनुष्टुभ्', 'श्लोक'],
    'बृहती': ['बृहती', 'महाबृहती', 'प्रगाथ', 'पङ्क्ति'],
    'पङ्क्ति': ['पङ्क्ति', 'महापङ्क्ति', 'प्रस्तारपङ्क्ति', 'प्रगाथ', 'बृहती'],
    'त्रिष्टुभ्': ['त्रिष्टुभ्', 'द्विपदा त्रिष्टुभ्', 'निचृत् त्रिष्टुभ्'],
    'जगती': ['जगती', 'अतिजगती', 'निचृत् जगती', 'ज्योतिस्'],
    'विराट्': ['विराट्', 'द्विपदा विराट्'],
    'ककुभ्': ['ककुभ्', 'उष्णिक्'],
}

# Compound or overlapping meters the engine identifies through their parts.
RIGVEDA_COMPOSITES = {
    'प्रगाथ': ['बृहती', 'पङ्क्ति', 'सतोबृहती', 'उष्णिक्', 'अनुष्टुभ्', 'प्रगाथ', 'त्रिष्टुभ्', 'जगती'],
    'विराट्': ['विराट्', 'उष्णिक्', 'बृहती', 'पङ्क्ति', 'त्रिष्टुभ्', 'गायत्री', 'अनुष्टुभ्', 'द्विपदा त्रिष्टुभ्', 'जगती'],
    'द्विपदा विराट्': ['विराट्', 'गायत्री', 'द्विपदा विराट्', 'उष्णिक्'],
    'द्विपदा त्रिष्टुभ्': ['त्रिष्टुभ्', 'पङ्क्ति', 'द्विपदा त्रिष्टुभ्', 'गायत्री'],
    'महापङ्क्ति': ['पङ्क्ति', 'जगती', 'त्रिष्टुभ्', 'महापङ्क्ति'],
    'ज्योतिस्': ['जगती', 'त्रिष्टुभ्', 'पङ्क्ति', 'ज्योतिस्'],
    'ककुभ्': ['ककुभ्', 'उष्णिक्', 'बृहती', 'अनुष्टुभ्'],
    'बृहती': ['बृहती', 'पङ्क्ति', 'प्रगाथ', 'अनुष्टुभ्', 'उष्णिक्'],
    'पङ्क्ति': ['पङ्क्ति', 'बृहती', 'प्रगाथ', 'त्रिष्टुभ्'],
    'जगती': ['जगती', 'त्रिष्टुभ्', 'अतिजगती'],
    'त्रिष्टुभ्': ['त्रिष्टुभ्', 'जगती', 'पङ्क्ति'],
    'अत्यष्टि': ['अत्यष्टि', 'जगती', 'त्रिष्टुभ्'],
    'अष्टि': ['अष्टि', 'जगती', 'त्रिष्टुभ्'],
    'अतिजगती': ['अतिजगती', 'जगती', 'त्रिष्टुभ्'],
    'शक्वरी': ['शक्वरी', 'जगती', 'त्रिष्टुभ्'],
    'अतिशक्वरी': ['अतिशक्वरी', 'जगती'],
}


@dataclass(frozen=True)
class LabelledVerse:
    ref: str
    text: str
    expected: str
    label: str = ''


@dataclass
class Tally:
    correct: int = 0
    total: int = 0
    misses: list[tuple[str, str, str | None]] = field(default_factory=list)

    def add(self, ok: bool, ref: str, expected: str, predicted: str | None) -> None:
        self.total += 1
        if ok:
            self.correct += 1
        else:
            self.misses.append((ref, expected, predicted))

    @property
    def rate(self) -> float:
        return self.correct / self.total if self.total else 0.0


# --------------------------------------------------------------------------- #
# Classical benchmark


def strip_diacritics(name: str) -> str:
    """Lower-case IAST without diacritics, transliterating Devanagari first."""
    name = name.lower().strip()
    try:
        name = transliterate(name, sanscript.DEVANAGARI, sanscript.IAST)
    except Exception:  # noqa: BLE001 - leave names the transliterator cannot read unchanged
        pass
    name = unicodedata.normalize('NFD', name)
    return ''.join(ch for ch in name if not unicodedata.combining(ch))


def classical_family(name: str) -> str:
    plain = strip_diacritics(name)
    return CLASSICAL_FAMILIES.get(plain, plain)


def classical_match(expected: str, predicted: str | None) -> bool:
    if not predicted:
        return False
    a, b = classical_family(expected), classical_family(predicted)
    return a == b or a in b or b in a


def load_classical_benchmark(data_dir: Path) -> list[LabelledVerse]:
    verses = []
    with (data_dir / CLASSICAL_BENCHMARK).open(encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 4:
                continue
            text, expected = row[0].strip(), row[3].strip()
            if not text or expected.lower() == 'chanda':
                continue
            verses.append(LabelledVerse(ref=f'row {len(verses) + 1}', text=text, expected=expected))
            if len(verses) == CLASSICAL_VERSE_ROWS:
                break
    return verses


def top_meter(line_result: dict | None) -> str | None:
    """The first meter name the engine lists for one analysed line."""
    chanda = (line_result or {}).get('result', {}).get('chanda')
    return chanda[0][0] if chanda else None


def verse_meter(result: dict) -> str | None:
    """The first meter name of the holistic verse-level result."""
    verses = result.get('result', {}).get('verse') or []
    if verses and verses[0].get('chanda') and verses[0]['chanda'][0]:
        return verses[0]['chanda'][0][0]
    return None


@dataclass
class ClassicalScore:
    first_line: Tally = field(default_factory=Tally)
    every_line: Tally = field(default_factory=Tally)
    lines: Tally = field(default_factory=Tally)
    whole_verse: Tally = field(default_factory=Tally)


def score_classical(chanda, verses: list[LabelledVerse]) -> ClassicalScore:
    score = ClassicalScore()
    for verse in verses:
        by_line = chanda.identify_from_text(verse.text, verse=False)
        lines = by_line.get('result', {}).get('line') or []
        predictions = [top_meter(line) for line in lines]

        first = predictions[0] if predictions else None
        score.first_line.add(classical_match(verse.expected, first), verse.ref, verse.expected, first)

        hits = [classical_match(verse.expected, p) for p in predictions]
        for hit, predicted in zip(hits, predictions, strict=True):
            score.lines.add(hit, verse.ref, verse.expected, predicted)
        wrong = next((p for hit, p in zip(hits, predictions, strict=True) if not hit), None)
        score.every_line.add(bool(hits) and all(hits), verse.ref, verse.expected, wrong)

        whole = verse_meter(chanda.identify_from_text(verse.text, verse=True))
        score.whole_verse.add(classical_match(verse.expected, whole), verse.ref, verse.expected, whole)
    return score


# --------------------------------------------------------------------------- #
# Rigveda benchmark


def _plain(name: str) -> str:
    for marked, plain in (
        ('ṭ', 't'),
        ('ṣ', 's'),
        ('ṇ', 'n'),
        ('ī', 'i'),
        ('ā', 'a'),
        ('ṛ', 'r'),
        ('ṅ', 'n'),
        ('ḥ', 'h'),
    ):
        name = name.replace(marked, plain)
    return name


_PLAIN_RIGVEDA_NAMES = {_plain(label): meter for label, meter in RIGVEDA_METER_NAMES.items()}


def rigveda_meter(label: str) -> str | None:
    """Engine meter name for a Rigveda label, or None for verse ranges and unknown meters."""
    label = label.strip().lower()
    if not label or label.startswith('('):
        return None
    return RIGVEDA_METER_NAMES.get(label) or _PLAIN_RIGVEDA_NAMES.get(_plain(label))


def rigveda_family(meter: str) -> str:
    for family, members in RIGVEDA_FAMILIES.items():
        if meter in members:
            return family
    return meter


def rigveda_match(expected: str, predicted: str | None) -> tuple[bool, bool]:
    """(exact, accepted): accepted also covers family members and composite parts."""
    if not predicted:
        return False, False
    if expected == predicted:
        return True, True
    if predicted in RIGVEDA_COMPOSITES.get(expected, ()):
        return False, True
    if rigveda_family(expected) == rigveda_family(predicted):
        return False, True
    return False, any(expected in members and predicted in members for members in RIGVEDA_FAMILIES.values())


def load_rigveda_benchmark(data_dir: Path, every: int = 1) -> list[LabelledVerse]:
    """Labelled ṛks, keeping every ``every``-th usable row."""
    verses = []
    with (data_dir / RIGVEDA_BENCHMARK).open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            text, label = row['verse_text'].strip(), row['meter'].strip()
            meter = rigveda_meter(label)
            if text and meter:
                ref = f"{row['mandala']}.{row['sukta']}.{row['rik']}"
                verses.append(LabelledVerse(ref=ref, text=text, expected=meter, label=label))
    return verses[::every]


def predict_vedic(chanda, text: str) -> str | None:
    """Vedic-mode meter, falling back to the line matcher's first meter."""
    predicted = chanda._identify_vedic_mode(text).get('meter')
    if predicted:
        return predicted
    line = chanda.identify_line(text)
    if line.get('found') and line.get('chanda'):
        first = line['chanda'][0]
        return first[0] if isinstance(first, tuple) else first
    return None


@dataclass
class RigvedaScore:
    exact: Tally = field(default_factory=Tally)
    accepted: Tally = field(default_factory=Tally)
    by_meter: dict[str, Tally] = field(default_factory=lambda: defaultdict(Tally))


def score_rigveda(chanda, verses: list[LabelledVerse]) -> RigvedaScore:
    score = RigvedaScore()
    for verse in verses:
        predicted = predict_vedic(chanda, verse.text)
        exact, accepted = rigveda_match(verse.expected, predicted)
        score.exact.add(exact, verse.ref, verse.expected, predicted)
        score.accepted.add(accepted, verse.ref, verse.expected, predicted)
        score.by_meter[verse.expected].add(exact, verse.ref, verse.expected, predicted)
    return score


def missed_floors(score: ClassicalScore | RigvedaScore) -> list[str]:
    """Every accuracy floor the score falls below, as readable lines; empty when all hold."""
    floors = CLASSICAL_FLOORS if isinstance(score, ClassicalScore) else RIGVEDA_FLOORS
    missed = [
        f"{name}: {getattr(score, name).correct} of {getattr(score, name).total}, floor {floor}"
        for name, floor in floors.items()
        if getattr(score, name).correct < floor
    ]
    if isinstance(score, ClassicalScore) and round(100 * score.whole_verse.rate, 1) < WHOLE_VERSE_PERCENT_FLOOR:
        missed.append(f"whole_verse: {100 * score.whole_verse.rate:.1f}%, floor {WHOLE_VERSE_PERCENT_FLOOR}%")
    return missed
