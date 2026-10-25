"""Accuracy report for the 147-verse classical benchmark.

Prints four measures, from backend.pipeline.benchmarks.score_classical:

1. first line: the first line's top meter matches the label
2. every line: every line's top meter matches the label
3. individual lines: share of all lines whose top meter matches
4. whole verse: the holistic verse-level meter matches

backend/tests/test_corpus_accuracy.py holds the same figures as floors.

Usage, from the repository root:
    uv run python -m backend.evaluation.csv_accuracy          # first-line accuracy
    uv run python -m backend.evaluation.csv_accuracy --all    # all four measures
    uv run python -m backend.evaluation.csv_accuracy --all -v # and list the misses
"""

from __future__ import annotations

import argparse
import sys

from backend.config import settings
from backend.core.chanda import Chanda
from backend.pipeline.benchmarks import CLASSICAL_VERSE_ROWS, Tally, load_classical_benchmark, score_classical

MISSES_SHOWN = 5


def report(title: str, tally: Tally, verbose: bool, unit: str = "verses") -> None:
    print(title)
    print("-" * 60)
    print(f"   {unit.capitalize()} tested: {tally.total}")
    print(f"   Correct: {tally.correct}")
    print(f"   Accuracy: {100 * tally.rate:.1f}%")
    if verbose and tally.misses:
        print(f"\n   Misses ({len(tally.misses)}):")
        for i, (ref, expected, predicted) in enumerate(tally.misses[:MISSES_SHOWN], 1):
            print(f"      {i}. {ref}: expected '{expected}', got '{predicted or 'NO RESULT'}'")
        if len(tally.misses) > MISSES_SHOWN:
            print(f"      ... and {len(tally.misses) - MISSES_SHOWN} more")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Accuracy on the classical verse benchmark.")
    parser.add_argument("-v", "--verbose", action="store_true", help="list the first misses of each measure")
    parser.add_argument("--all", action="store_true", help="report every measure, not only the first line")
    args = parser.parse_args(argv)

    score = score_classical(Chanda(str(settings.DATA_DIR)), load_classical_benchmark(settings.DATA_DIR))

    print("=" * 75)
    print(f"CLASSICAL BENCHMARK ACCURACY (first {CLASSICAL_VERSE_ROWS} verse rows)")
    print("=" * 75)
    report("FIRST LINE (line 1 prediction)", score.first_line, args.verbose)
    if args.all:
        report("EVERY LINE (all lines must match)", score.every_line, args.verbose)
        report("INDIVIDUAL LINES", score.lines, args.verbose, unit="lines")
        report("WHOLE VERSE (holistic analysis)", score.whole_verse, args.verbose)

    return 0 if score.first_line.rate >= 0.9 else 1


if __name__ == "__main__":
    sys.exit(main())
