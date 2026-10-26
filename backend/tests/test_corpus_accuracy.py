"""Accuracy floors on the labelled corpora; a change that loses a correctly identified verse fails here.

The floors are the counts the engine reaches today, kept in backend/pipeline/benchmarks.py
next to the scoring rules. Raise them when a change identifies more verses.
``uv run python -m backend.evaluation.csv_accuracy --all`` and ``rigveda_validation`` print the
same figures with every miss, and exit 1 below the same floors.
"""

import pytest

from backend.config import settings
from backend.pipeline import benchmarks

pytestmark = pytest.mark.corpus


@pytest.fixture(scope="module")
def classical(chanda):
    verses = benchmarks.load_classical_benchmark(settings.DATA_DIR)
    assert len(verses) == benchmarks.CLASSICAL_VERSE_ROWS
    return benchmarks.score_classical(chanda, verses)


@pytest.fixture(scope="module")
def rigveda(chanda):
    verses = benchmarks.load_rigveda_benchmark(settings.DATA_DIR)
    assert len(verses) == 9247
    return benchmarks.score_rigveda(chanda, verses)


@pytest.mark.parametrize("measure", list(benchmarks.CLASSICAL_FLOORS))
def test_classical_measures_hold_their_floors(classical, measure):
    tally = getattr(classical, measure)
    assert tally.correct >= benchmarks.CLASSICAL_FLOORS[measure], tally.misses


def test_classical_whole_verse_accuracy_is_at_least_94_6_percent(classical):
    """The README's headline figure: 139 of 147 verses identified as a whole."""
    percent = round(100 * classical.whole_verse.rate, 1)
    assert classical.whole_verse.total == 147
    assert percent >= benchmarks.WHOLE_VERSE_PERCENT_FLOOR, classical.whole_verse.misses


@pytest.mark.parametrize("measure", list(benchmarks.RIGVEDA_FLOORS))
def test_rigveda_measures_hold_their_floors(rigveda, measure):
    tally = getattr(rigveda, measure)
    assert tally.correct >= benchmarks.RIGVEDA_FLOORS[measure], f"{tally.correct} of {tally.total}"


@pytest.mark.parametrize(("meter", "floor"), [("गायत्री", 2157), ("त्रिष्टुभ्", 3605), ("अनुष्टुभ्", 636), ("जगती", 886)])
def test_rigveda_core_meters_exactly(rigveda, meter, floor):
    tally = rigveda.by_meter[meter]
    assert tally.correct >= floor, f"{meter}: {tally.correct} of {tally.total}"
