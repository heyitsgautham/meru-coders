"""The Chanda engine must reproduce its committed output on 150 reference verses.

A failure lists every verse whose displayed meter changed. Refactors must keep
this test green without regenerating the snapshot; see
backend/tests/golden/engine_snapshot.py for how to regenerate it on purpose.
"""

import pytest

from backend.tests.golden import engine_snapshot as golden


@pytest.fixture(scope="module")
def expected():
    return golden.load_snapshot()


def test_snapshot_covers_150_verses_from_five_corpora(expected):
    assert len(expected["verses"]) == 150
    assert {verse["source"] for verse in expected["verses"]} == {
        "gita",
        "rigveda",
        "pragatha",
        "examples",
        "chandovallari",
    }


def test_verse_selection_matches_the_committed_corpora(expected):
    selected = golden.select_verses()
    assert [(v["id"], v["text"]) for v in selected] == [(v["id"], v["text"]) for v in expected["verses"]]


def test_engine_output_matches_the_golden_snapshot(chanda, expected):
    actual = {
        "configurations": expected["configurations"],
        "verses": [{**verse, "outputs": golden.snapshot_verse(chanda, verse["text"])} for verse in expected["verses"]],
    }
    changes = golden.diff_snapshots(expected, actual)
    assert not changes, "engine output changed:\n" + "\n".join(changes[:40])


def test_diff_reports_a_changed_meter():
    old = {"verses": [{"id": "001-gita", "outputs": {"verse:auto": {"meters": ["अनुष्टुभ्"], "sha256": "a"}}}]}
    new = {"verses": [{"id": "001-gita", "outputs": {"verse:auto": {"meters": ["त्रिष्टुभ्"], "sha256": "b"}}}]}
    assert golden.diff_snapshots(old, new) == ["001-gita [verse:auto] meters ['अनुष्टुभ्'] -> ['त्रिष्टुभ्']"]


def test_diff_reports_a_payload_only_change_and_a_missing_verse():
    old = {
        "verses": [
            {"id": "001-gita", "outputs": {"verse:auto": {"meters": ["x"], "sha256": "a"}}},
            {"id": "002-gita", "outputs": {"verse:auto": {"meters": ["y"], "sha256": "c"}}},
        ]
    }
    new = {"verses": [{"id": "001-gita", "outputs": {"verse:auto": {"meters": ["x"], "sha256": "b"}}}]}
    assert golden.diff_snapshots(old, new) == [
        "001-gita [verse:auto] same meters, different result payload",
        "002-gita: missing from the new snapshot",
    ]


def test_digest_ignores_key_order():
    assert golden.digest({"a": 1, "b": [1, 2]}) == golden.digest({"b": [1, 2], "a": 1})
    assert golden.digest({"a": 1}) != golden.digest({"a": 2})
