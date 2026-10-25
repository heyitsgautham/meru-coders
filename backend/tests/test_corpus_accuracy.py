"""Accuracy floors on the labelled corpora; a change that loses a correctly identified verse fails here.

The floors are the counts the engine reaches today. Raise them when a change
identifies more verses. The benchmarks and the matching rules live in
backend/pipeline/benchmarks.py; ``uv run python backend/evaluation/csv_accuracy.py``
and ``rigveda_validation.py`` print the same figures with every miss.
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


def test_classical_first_line(classical):
    assert classical.first_line.correct >= 146, classical.first_line.misses


def test_classical_every_line_of_the_verse(classical):
    assert classical.every_line.correct >= 134, classical.every_line.misses


def test_classical_individual_lines(classical):
    assert (classical.lines.correct, classical.lines.total) >= (485, 499), classical.lines.misses


def test_classical_whole_verse(classical):
    assert classical.whole_verse.correct >= 139, classical.whole_verse.misses


def test_rigveda_exact_meter(rigveda):
    assert rigveda.exact.correct >= 8067, f"{rigveda.exact.correct} of {rigveda.exact.total}"


def test_rigveda_meter_or_family(rigveda):
    assert rigveda.accepted.correct >= 9009, f"{rigveda.accepted.correct} of {rigveda.accepted.total}"


@pytest.mark.parametrize(("meter", "floor"), [("गायत्री", 2157), ("त्रिष्टुभ्", 3605), ("अनुष्टुभ्", 636), ("जगती", 886)])
def test_rigveda_core_meters_exactly(rigveda, meter, floor):
    tally = rigveda.by_meter[meter]
    assert tally.correct >= floor, f"{meter}: {tally.correct} of {tally.total}"
