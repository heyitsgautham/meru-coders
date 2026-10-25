"""The record every pipeline check returns, and the baseline those records are compared with."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

KNOWN_ISSUES_PATH = Path(__file__).with_name("known_issues.json")


@dataclass(frozen=True)
class Issue:
    file: str
    line: int
    subject: str
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line} {self.subject}: {self.rule} ({self.detail})"


def count_by_rule(issues: list[Issue]) -> dict[str, int]:
    """Issue counts keyed ``file:rule``, the shape of the committed baseline."""
    counts = Counter(f"{issue.file}:{issue.rule}" for issue in issues)
    return dict(sorted(counts.items()))


def load_known_issues(path: Path = KNOWN_ISSUES_PATH) -> dict[str, dict[str, int]]:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_with_baseline(counts: dict[str, int], baseline: dict[str, int]) -> tuple[list[str], list[str]]:
    """Return (regressions, improvements) between current counts and the recorded baseline."""
    regressions, improvements = [], []
    for key in sorted(set(counts) | set(baseline)):
        now, before = counts.get(key, 0), baseline.get(key, 0)
        if now > before:
            regressions.append(f"{key}: {now} issues, baseline allows {before}")
        elif now < before:
            improvements.append(f"{key}: {now} issues, baseline records {before}; lower it in known_issues.json")
    return regressions, improvements
