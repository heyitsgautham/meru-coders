"""Accuracy report for the Rigveda: the engine's Vedic mode against the Anukramaṇī meter labels.

Scoring comes from backend.pipeline.benchmarks.score_rigveda. A prediction is
exact when it names the labelled meter, and accepted when it names a meter of
the same family or a part of a compound meter such as Pragātha.
backend/tests/test_corpus_accuracy.py holds the same figures as floors, and
``python -m backend.pipeline.validate`` checks the corpus itself.

Usage, from the repository root:
    uv run python -m backend.evaluation.rigveda_validation         # whole Rigveda, about 10 seconds
    uv run python -m backend.evaluation.rigveda_validation -n 500  # first 500 labelled riks
    uv run python -m backend.evaluation.rigveda_validation -v      # also list misses per meter
"""

from __future__ import annotations

import argparse
import sys

from backend.config import settings
from backend.core.chanda import Chanda
from backend.pipeline.benchmarks import RIGVEDA_BENCHMARK, load_rigveda_benchmark, missed_floors, score_rigveda

MISSES_SHOWN = 5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vedic-mode accuracy on the labelled Rigveda.")
    parser.add_argument("-v", "--verbose", action="store_true", help="list the first misses of each meter")
    parser.add_argument("-n", "--limit", type=int, help="score only the first N labelled riks")
    args = parser.parse_args(argv)

    verses = load_rigveda_benchmark(settings.DATA_DIR)[: args.limit]
    score = score_rigveda(Chanda(data_path=str(settings.DATA_DIR)), verses)
    total = score.exact.total
    family_only = score.accepted.correct - score.exact.correct
    misses = total - score.accepted.correct

    print("=" * 60)
    print(f"RIGVEDA VALIDATION ({RIGVEDA_BENCHMARK})")
    print("=" * 60)
    print(f"Riks scored:     {total:>6}")
    print(f"Exact meter:     {score.exact.correct:>6} ({100 * score.exact.rate:.2f}%)")
    print(f"Family or part:  {family_only:>6} ({100 * family_only / total if total else 0:.2f}%)")
    print(f"Misses:          {misses:>6} ({100 * misses / total if total else 0:.2f}%)")
    print(f"Accepted:        {score.accepted.correct:>6} ({100 * score.accepted.rate:.2f}%)")

    print("\n" + "-" * 60)
    print(f"{'Meter':<20} {'Riks':>8} {'Exact':>8} {'Acc%':>8}")
    print("-" * 60)
    for meter, tally in sorted(score.by_meter.items(), key=lambda item: item[1].total, reverse=True):
        print(f"{meter:<20} {tally.total:>8} {tally.correct:>8} {100 * tally.rate:>7.1f}%")
        if args.verbose:
            for ref, _expected, predicted in tally.misses[:MISSES_SHOWN]:
                print(f"    RV {ref}: predicted {predicted or 'nothing'}")

    if args.limit:
        return 0  # the floors count the whole corpus
    missed = missed_floors(score)
    for line in missed:
        print(f"BELOW FLOOR {line}")
    print("All accuracy floors hold." if not missed else f"{len(missed)} floor(s) missed.")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
