"""
Unit tests for reconcile_bt_ontop_gh.

These tests focus strictly on reconciliation behavior, not logging.
"""

from __future__ import annotations

import pytest

import bridge.pipelines.policies.bt2gh as recon


def _make_recording_output():
    """
    Return (make_output, calls) where calls captures the set passed in.
    """
    calls: list[set[str]] = []

    def make_output(missing: set[str]):
        calls.append(set(missing))  # copy for safety
        # Return something deterministic to assert on
        return {"missing": sorted(missing)}

    return make_output, calls


@pytest.mark.parametrize(
    "case, gh_norm, bt_norm, expected_output, expected_calls",
    [
        # -------------------------
        # 1) bio.tools silent => None
        # -------------------------
        ("bt None", {"a"}, None, None, []),
        ("bt empty", {"a"}, set(), None, []),
        ("bt None, gh None", None, None, None, []),
        ("bt empty, gh empty", set(), set(), None, []),
        # -------------------------
        # 2) gh silent => propose ALL bt terms
        # -------------------------
        ("gh None", None, {"a", "b"}, {"missing": ["a", "b"]}, [{"a", "b"}]),
        ("gh empty", set(), {"a"}, {"missing": ["a"]}, [{"a"}]),
        # -------------------------
        # 3) both present
        # -------------------------
        ("all present => None", {"a", "b"}, {"a"}, None, []),
        ("some missing => propose missing only", {"a"}, {"a", "b", "c"}, {"missing": ["b", "c"]}, [{"b", "c"}]),
        ("none present => propose all (difference)", {"x"}, {"a", "b"}, {"missing": ["a", "b"]}, [{"a", "b"}]),
        # -------------------------
        # Corner: gh has extras, should ignore them
        # -------------------------
        ("gh superset => None", {"a", "b", "c"}, {"a", "b"}, None, []),
    ],
)
def test_reconcile_bt_ontop_gh(case, gh_norm, bt_norm, expected_output, expected_calls):
    make_output, calls = _make_recording_output()

    out = recon.reconcile_bt_ontop_gh(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        make_output=make_output,
        log_label="topics",
    )

    assert out == expected_output, case
    assert calls == expected_calls, case


def test_reconcile_bt_ontop_gh_passes_exact_missing_set_to_make_output():
    """
    Stronger check: ensure the set given to make_output is exactly (bt - gh),
    not bt itself, and not something mutated later.
    """
    bt = {"edam-a", "edam-b", "edam-c"}
    gh = {"edam-b"}

    captured: list[set[str]] = []

    def make_output(missing: set[str]):
        captured.append(set(missing))
        return missing  # return the set to make assertion easy

    out = recon.reconcile_bt_ontop_gh(
        gh_norm=set(gh),
        bt_norm=set(bt),
        make_output=make_output,
        log_label="edam terms",
    )

    assert out == {"edam-a", "edam-c"}
    assert captured == [{"edam-a", "edam-c"}]
