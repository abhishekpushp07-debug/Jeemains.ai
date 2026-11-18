# Iteration101: unit tests for the server-side 3-way dream merge (dream.merge) - no DB, no network.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dream import merge, DreamsIn  # noqa: E402


def d(i, exam="jee"):
    return {"id": i, "exam": exam, "college": "TEST_" + i, "branch": "B", "need": 100, "note": "", "at": 1}


def test_empty_base_never_removes_account_dreams_and_respects_limit():
    current = [d(f"j{i}") for i in range(5)]
    out = merge(current, [], [d("legacy-j"), d("legacy-c", "comedk")])
    assert [x["id"] for x in out] == ["j0", "j1", "j2", "j3", "j4", "legacy-c"]


def test_removed_here_goes_other_device_add_stays():
    current = [d("a"), d("b"), d("other", "bitsat")]
    out = merge(current, ["a", "b"], [d("a")])
    assert [x["id"] for x in out] == ["a", "other"]


def test_added_here_joins_free_slot_and_updates_existing():
    current = [d("a")]
    mine = [dict(d("a"), need=200), d("new")]
    out = merge(current, ["a"], mine)
    assert [x["id"] for x in out] == ["a", "new"] and out[0]["need"] == 200


def test_missing_base_only_adds():
    assert DreamsIn(dreams=[]).base == []
    assert merge([d("a")], DreamsIn(dreams=[d("b")]).base, [d("b")]) == [d("a"), d("b")]
