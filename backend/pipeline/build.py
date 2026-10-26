"""Regenerate every derived dataset in the repository, or check that the committed copies are current.

    uv run python -m backend.pipeline.build            # validate the inputs, then write every artifact
    uv run python -m backend.pipeline.build --check    # write nothing; exit 1 if a committed artifact differs

Each artifact is a pure function of committed inputs, rendered with fixed ordering and
line endings, so building twice writes the same bytes and an unchanged input leaves its
artifact untouched. The build first runs the dataset checks from ``validate``; if any
input carries a defect beyond ``known_issues.json`` it writes nothing.

| Artifact | Built from |
|---|---|
| data/rigveda_with_meters_complete.csv | a byte copy of source/rigveda-with-meters.csv |
| data/pragatha_pankti_verses.csv | the Pragātha and Paṅkti rows of that file |
| evaluation/data/rigveda_authentic.py | the Rigveda_api and WSC2023 clones under --repos |

The third input lives outside the repository. Without the clones the build cannot
regenerate it, so it re-renders the committed records instead, which still proves the file
is in canonical form, and says so. ``tests/pipeline/test_rigveda_dataset.py`` builds it from
small fixture copies of both sources.

The meter tables (data/chanda_*.csv) are not built here: they are curated by hand, and the
one-off import scripts in backend/scripts no longer reproduce them.
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from backend.config import settings
from backend.pipeline import corpora, rigveda_dataset
from backend.pipeline.issues import Issue, compare_with_baseline, count_by_rule, load_known_issues
from backend.pipeline.validate import CHECKS


@dataclass(frozen=True)
class Artifact:
    path: str  # relative to the backend directory
    inputs: str
    # Returns the artifact's bytes, or None when its inputs are not available here.
    render: Callable[[Path, Path], bytes | None]


def _rigveda_rows(backend: Path) -> list[dict[str, str]]:
    return corpora.read_csv(backend / "source" / corpora.RIGVEDA_SOURCE)[1]


def render_csv(fieldnames: list[str], rows: list[dict[str, str]]) -> bytes:
    """CSV the way the committed corpora are written: csv module defaults, CRLF line endings."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _rigveda_copy(backend: Path, _repos: Path) -> bytes:
    return (backend / "source" / corpora.RIGVEDA_SOURCE).read_bytes()


def _pragatha_pankti(backend: Path, _repos: Path) -> bytes:
    return render_csv(corpora.RIGVEDA_COLUMNS, corpora.derive_pragatha_pankti(_rigveda_rows(backend)))


def _committed_rigveda_records(path: Path) -> list[dict]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "RIGVEDA_AUTHENTIC" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"{path} defines no RIGVEDA_AUTHENTIC list")


def _rigveda_authentic(backend: Path, repos: Path) -> bytes | None:
    if not (repos / "Rigveda_api").is_dir() or not (repos / "WSC2023").is_dir():
        return None
    records = rigveda_dataset.build(repos)
    issues = rigveda_dataset.validate_records(records)
    if not records or issues:
        raise BuildError([str(issue) for issue in issues] or ["no Rigveda records built"])
    return rigveda_dataset.render_module(records).encode("utf-8")


ARTIFACTS = (
    Artifact("data/" + corpora.RIGVEDA_COPY, "source/" + corpora.RIGVEDA_SOURCE, _rigveda_copy),
    Artifact("data/" + corpora.PRAGATHA_PANKTI, "source/" + corpora.RIGVEDA_SOURCE, _pragatha_pankti),
    Artifact("evaluation/data/rigveda_authentic.py", "repos/Rigveda_api, repos/WSC2023", _rigveda_authentic),
)


class BuildError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def gate(backend: Path) -> list[str]:
    """Defects in the inputs beyond the recorded baseline; the build writes nothing while any remain."""
    baseline = load_known_issues()
    problems: list[str] = []
    for name, check in CHECKS.items():
        issues: list[Issue] = check(backend / "data", backend / "source")
        if name == "corpora":
            # The derived files are rebuilt below, so drift in them is not an input defect.
            issues = [issue for issue in issues if issue.file not in {corpora.RIGVEDA_COPY, corpora.PRAGATHA_PANKTI}]
        regressions, _ = compare_with_baseline(count_by_rule(issues), baseline.get(name, {}))
        problems += [f"{name}: {line}" for line in regressions]
    return problems


@dataclass(frozen=True)
class Result:
    artifact: Artifact
    status: str  # "up to date", "out of date", "written", or "canonical form, inputs not cloned"


def build(backend: Path, repos: Path, check: bool) -> list[Result]:
    problems = gate(backend)
    if problems:
        raise BuildError(problems)
    results = []
    for artifact in ARTIFACTS:
        target = backend / artifact.path
        fresh = artifact.render(backend, repos)
        if fresh is None:
            # Inputs live outside the repository: prove the committed file is what the renderer writes.
            canonical = rigveda_dataset.render_module(_committed_rigveda_records(target)).encode("utf-8")
            same = target.read_bytes() == canonical
            results.append(Result(artifact, "canonical form, inputs not cloned" if same else "out of date"))
            continue
        current = target.read_bytes() if target.exists() else None
        if current == fresh:
            results.append(Result(artifact, "up to date"))
        elif check:
            results.append(Result(artifact, "out of date"))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(fresh)
            results.append(Result(artifact, "written"))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate the derived datasets, or check they are current.")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if an artifact is out of date")
    parser.add_argument(
        "--repos",
        type=Path,
        default=rigveda_dataset.DEFAULT_REPOS,
        help="directory holding the Rigveda_api and WSC2023 clones",
    )
    args = parser.parse_args(argv)
    try:
        results = build(settings.BASE_DIR, args.repos, args.check)
    except BuildError as error:
        print("inputs failed validation; nothing written:", file=sys.stderr)
        for problem in error.problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    for result in results:
        print(f"{result.artifact.path}: {result.status} (from {result.artifact.inputs})")
    return 1 if any(result.status == "out of date" for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
