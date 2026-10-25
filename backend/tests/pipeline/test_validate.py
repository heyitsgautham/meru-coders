"""The validate command fails only on defects beyond the recorded baseline."""

import io
from pathlib import Path

import pytest

from backend.pipeline import validate
from backend.pipeline.issues import Issue, compare_with_baseline

ISSUE = Issue("chanda_sama.csv", 9, "मालिनी", "syllable_count", "15 declared, pattern has 14")


@pytest.fixture
def one_issue(monkeypatch):
    monkeypatch.setattr(validate, "CHECKS", {"meter_tables": lambda data_dir, source_dir: [ISSUE]})


def run(baseline, show=False):
    out = io.StringIO()
    code = validate.run(Path("data"), Path("source"), {"meter_tables": baseline}, show, out=out)
    return code, out.getvalue()


def test_issues_within_the_baseline_pass(one_issue):
    code, out = run({"chanda_sama.csv:syllable_count": 1})
    assert code == 0
    assert out == "meter_tables: ok, 1 issues\n"


def test_a_new_issue_fails(one_issue):
    code, out = run({})
    assert code == 1
    assert "meter_tables: FAIL" in out
    assert "chanda_sama.csv:syllable_count: 1 issues, baseline allows 0" in out


def test_a_fixed_issue_asks_for_a_lower_baseline_without_failing(one_issue):
    code, out = run({"chanda_sama.csv:syllable_count": 2})
    assert code == 0
    assert "lower it in known_issues.json" in out


def test_show_prints_each_issue(one_issue):
    _, out = run({"chanda_sama.csv:syllable_count": 1}, show=True)
    assert str(ISSUE) in out


def test_compare_with_baseline_covers_keys_on_either_side():
    regressions, improvements = compare_with_baseline({"a:x": 2, "b:y": 1}, {"a:x": 1, "c:z": 3})
    assert regressions == ["a:x: 2 issues, baseline allows 1", "b:y: 1 issues, baseline allows 0"]
    assert improvements == ["c:z: 0 issues, baseline records 3; lower it in known_issues.json"]


def test_the_committed_data_passes():
    assert validate.main([]) == 0
