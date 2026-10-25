"""Run every dataset check and compare the result with known_issues.json.

    uv run python -m backend.pipeline.validate          # summary, exit 1 on a new defect
    uv run python -m backend.pipeline.validate --show   # also print every issue

CI runs the summary form in the Data quality step.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from backend.config import settings
from backend.pipeline.corpora import check_corpora
from backend.pipeline.issues import Issue, compare_with_baseline, count_by_rule, load_known_issues
from backend.pipeline.meter_tables import check_definition_tables

CHECKS: dict[str, Callable[[Path, Path], list[Issue]]] = {
    "meter_tables": lambda data_dir, _source_dir: check_definition_tables(data_dir),
    "corpora": check_corpora,
}


def run(data_dir: Path, source_dir: Path, baseline: dict[str, dict[str, int]], show: bool, out=sys.stdout) -> int:
    failed = False
    for name, check in CHECKS.items():
        issues = check(data_dir, source_dir)
        regressions, improvements = compare_with_baseline(count_by_rule(issues), baseline.get(name, {}))
        status = "FAIL" if regressions else "ok"
        print(f"{name}: {status}, {len(issues)} issues", file=out)
        for line in regressions + improvements:
            print(f"  {line}", file=out)
        if show:
            for issue in issues:
                print(f"    {issue}", file=out)
        failed = failed or bool(regressions)
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the meter tables and verse corpora.")
    parser.add_argument("--show", action="store_true", help="print every issue, not only the summary")
    args = parser.parse_args(argv)
    return run(settings.DATA_DIR, settings.BASE_DIR / "source", load_known_issues(), args.show)


if __name__ == "__main__":
    sys.exit(main())
