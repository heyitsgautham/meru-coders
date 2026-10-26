"""The dataset build: one command that regenerates every derived file byte for byte, behind a validation gate."""

import shutil
from pathlib import Path

import pytest

from backend.config import settings
from backend.pipeline import build

BACKEND = settings.BASE_DIR
FIXTURE_REPOS = Path(__file__).resolve().parents[1] / "fixtures" / "rigveda_repos"
NO_REPOS = Path("/nonexistent-repos")
DERIVED = [artifact.path for artifact in build.ARTIFACTS]


@pytest.fixture
def workspace(tmp_path):
    """A backend tree whose inputs link to the real files and whose derived files are real copies."""
    root = tmp_path / "backend"
    root.mkdir()
    (root / "source").symlink_to(BACKEND / "source")
    (root / "data").mkdir()
    for path in (BACKEND / "data").iterdir():
        if path.name != "chroma_db":
            (root / "data" / path.name).symlink_to(path)
    (root / "evaluation" / "data").mkdir(parents=True)
    for relative in DERIVED:
        target = root / relative
        if target.is_symlink():
            target.unlink()
        shutil.copyfile(BACKEND / relative, target)
    return root


def statuses(results):
    return {result.artifact.path: result.status for result in results}


def test_the_committed_files_are_current():
    assert statuses(build.build(BACKEND, NO_REPOS, check=True)) == {
        "data/rigveda_with_meters_complete.csv": "up to date",
        "data/pragatha_pankti_verses.csv": "up to date",
        "evaluation/data/rigveda_authentic.py": "canonical form, inputs not cloned",
    }


def test_a_fresh_build_reproduces_the_committed_bytes_and_a_second_build_changes_nothing(workspace):
    for relative in DERIVED[:2]:
        (workspace / relative).unlink()

    first = statuses(build.build(workspace, NO_REPOS, check=False))
    second = statuses(build.build(workspace, NO_REPOS, check=False))

    assert first["data/pragatha_pankti_verses.csv"] == "written"
    assert second["data/pragatha_pankti_verses.csv"] == "up to date"
    for relative in DERIVED[:2]:
        assert (workspace / relative).read_bytes() == (BACKEND / relative).read_bytes()


def test_the_rigveda_ground_truth_builds_from_its_clones_and_is_stable(workspace):
    first = statuses(build.build(workspace, FIXTURE_REPOS, check=False))
    written = (workspace / "evaluation/data/rigveda_authentic.py").read_bytes()
    second = statuses(build.build(workspace, FIXTURE_REPOS, check=False))

    assert first["evaluation/data/rigveda_authentic.py"] == "written"
    assert second["evaluation/data/rigveda_authentic.py"] == "up to date"
    assert (workspace / "evaluation/data/rigveda_authentic.py").read_bytes() == written


def test_check_reports_a_hand_edited_artifact_without_rewriting_it(workspace):
    edited = workspace / "data/pragatha_pankti_verses.csv"
    edited.write_bytes(edited.read_bytes().replace(b"10,62,6", b"10,62,9", 1))

    result = statuses(build.build(workspace, NO_REPOS, check=True))

    assert result["data/pragatha_pankti_verses.csv"] == "out of date"
    assert b"10,62,9" in edited.read_bytes()


def test_a_new_defect_in_the_inputs_blocks_every_write(workspace):
    (workspace / "source").unlink()
    shutil.copytree(BACKEND / "source", workspace / "source")
    source = workspace / "source/rigveda-with-meters.csv"
    lines = source.read_bytes().split(b"\r\n")
    source.write_bytes(b"\r\n".join([*lines[:2], lines[1], *lines[2:]]))  # repeat the first rk
    (workspace / "data/pragatha_pankti_verses.csv").unlink()

    with pytest.raises(build.BuildError) as error:
        build.build(workspace, NO_REPOS, check=False)

    assert any("duplicate_rik" in problem for problem in error.value.problems)
    assert not (workspace / "data/pragatha_pankti_verses.csv").exists()


def test_the_command_exits_1_when_an_artifact_is_out_of_date(monkeypatch, workspace, capsys):
    (workspace / "data/rigveda_with_meters_complete.csv").write_bytes(b"stale")
    monkeypatch.setattr(settings, "BASE_DIR", workspace)

    assert build.main(["--check", "--repos", str(NO_REPOS)]) == 1
    assert "data/rigveda_with_meters_complete.csv: out of date" in capsys.readouterr().out
