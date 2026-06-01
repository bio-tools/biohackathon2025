"""
Unit tests for reconcile_gh_ontop_bt.

These tests focus strictly on reconciliation behavior, not logging.
"""

from __future__ import annotations

import pytest

import bridge.pipelines.policies.gh2bt as recon


def _make_build_bt_from_norm():
    """
    build_bt_from_norm that makes a deterministic, comparable concrete BT value.
    We represent the concrete bio.tools value as a sorted tuple, so set ordering
    doesn't matter in assertions.
    """

    def build_bt_from_norm(bt_norm: set[str]):
        return tuple(sorted(bt_norm))

    return build_bt_from_norm


def _make_recording_build_bt_from_gh(return_value_factory):
    """
    Build a build_bt_from_gh callable that records its single argument into `calls`.
    Returns (build_bt_from_gh, calls).
    """
    calls: list[object] = []

    def build_bt_from_gh(x):
        calls.append(x)
        return return_value_factory(x)

    return build_bt_from_gh, calls


@pytest.mark.parametrize(
    "case, gh_norm, bt_norm, bt_value, build_bt_from_gh, expected, expected_calls",
    [
        # -------------------------
        # 1) GitHub silent => preserve bt_value, never calls build_bt_from_gh
        # -------------------------
        ("gh None => preserve", None, {"a"}, ("existing",), lambda x: {"x"}, ("existing",), []),
        ("gh empty set => preserve", set(), {"a"}, ("existing",), lambda x: {"x"}, ("existing",), []),
        ("gh empty list => preserve", [], {"a"}, ("existing",), lambda x: {"x"}, ("existing",), []),
        # -------------------------
        # 2) build_bt_from_gh is None => treat gh_norm as already-bt-norm
        # -------------------------
        ("build_bt_from_gh None + bt missing => build from gh", {"a", "b"}, None, None, None, ("a", "b"), []),
        ("build_bt_from_gh None + bt empty => build from gh", {"a"}, set(), None, None, ("a",), []),
        (
            "build_bt_from_gh None + bt present => union and build",
            {"b", "c"},
            {"a", "b"},
            ("keep-me",),
            None,
            ("a", "b", "c"),
            [],
        ),
        # -------------------------
        # 3) build_bt_from_gh returns None/empty => preserve bt_value
        # -------------------------
        ("cannot map gh => preserve (None)", {"x"}, {"a"}, ("existing",), lambda _x: None, ("existing",), [{"x"}]),
        (
            "cannot map gh => preserve (empty set)",
            {"x"},
            {"a"},
            ("existing",),
            lambda _x: set(),
            ("existing",),
            [{"x"}],
        ),
        # -------------------------
        # 4) bt missing/empty => add ALL gh-derived values (build_bt_from_norm called on gh-derived)
        # -------------------------
        ("bt None => build from gh-derived", {"x"}, None, None, lambda _x: {"a", "b"}, ("a", "b"), [{"x"}]),
        ("bt empty => build from gh-derived", {"x"}, set(), None, lambda _x: {"a"}, ("a",), [{"x"}]),
        # -------------------------
        # 5) bt present + gh-derived subset => exact => preserve bt_value
        # -------------------------
        (
            "gh-derived already present => preserve",
            {"x"},
            {"a", "b"},
            ("preserve-this",),
            lambda _x: {"a"},
            ("preserve-this",),
            [{"x"}],
        ),
        (
            "gh-derived equals bt_norm => preserve",
            {"x"},
            {"a"},
            ("preserve-this",),
            lambda _x: {"a"},
            ("preserve-this",),
            [{"x"}],
        ),
        # -------------------------
        # 6) bt present + gh-derived adds new values => build union
        # -------------------------
        (
            "gh-derived adds new => build union",
            {"x"},
            {"a"},
            ("old-bt",),
            lambda _x: {"a", "b", "c"},
            ("a", "b", "c"),
            [{"x"}],
        ),
        ("gh-derived disjoint => build union", {"x"}, {"a"}, ("old-bt",), lambda _x: {"b"}, ("a", "b"), [{"x"}]),
    ],
)
async def test_reconcile_gh_ontop_bt(case, gh_norm, bt_norm, bt_value, build_bt_from_gh, expected, expected_calls):
    build_bt_from_norm = _make_build_bt_from_norm()

    # Wrap build_bt_from_gh so we can assert call behavior in-table (or keep None).
    calls: list[object] = []
    if build_bt_from_gh is None:
        recording_build_bt_from_gh = None
    else:

        def recording_build_bt_from_gh(x):
            calls.append(x)
            return build_bt_from_gh(x)

    out = await recon.reconcile_gh_ontop_bt(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        bt_value=bt_value,
        build_bt_from_gh=recording_build_bt_from_gh,
        build_bt_from_norm=build_bt_from_norm,
        log_label="field",
    )

    assert out == expected, case
    assert calls == expected_calls, case


async def test_reconcile_gh_ontop_bt_build_bt_from_norm_called_with_exact_union_set():
    """
    Stronger check: ensure build_bt_from_norm receives exactly bt_norm ∪ gh_from_bt,
    and that gh_from_bt itself (or bt_norm) isn't accidentally mutated.
    """
    bt_norm = {"a", "b"}
    gh_norm = {"whatever"}

    # gh maps to {"b", "c"} => union should be {"a", "b", "c"}
    build_bt_from_gh, gh_calls = _make_recording_build_bt_from_gh(lambda _x: {"b", "c"})

    captured_norms: list[set[str]] = []

    def build_bt_from_norm(norm: set[str]):
        captured_norms.append(set(norm))  # copy to ensure later mutations won't affect us
        return tuple(sorted(norm))

    out = await recon.reconcile_gh_ontop_bt(
        gh_norm=set(gh_norm),
        bt_norm=set(bt_norm),
        bt_value=("preserve?",),
        build_bt_from_gh=build_bt_from_gh,
        build_bt_from_norm=build_bt_from_norm,
        log_label="field",
    )

    assert out == ("a", "b", "c")
    assert gh_calls == [set(gh_norm)]
    assert captured_norms == [{"a", "b", "c"}]


async def test_reconcile_gh_ontop_bt_when_no_additions_does_not_call_build_bt_from_norm():
    """
    If gh-derived values are already present (nr_added == 0), function should
    return bt_value and MUST NOT call build_bt_from_norm.
    """
    bt_norm = {"a", "b"}
    bt_value = ("keep",)

    def build_bt_from_gh(_x):
        return {"a"}  # subset => no additions

    build_bt_from_norm_calls: list[set[str]] = []

    def build_bt_from_norm(norm: set[str]):
        build_bt_from_norm_calls.append(set(norm))
        return tuple(sorted(norm))

    out = await recon.reconcile_gh_ontop_bt(
        gh_norm={"x"},
        bt_norm=set(bt_norm),
        bt_value=bt_value,
        build_bt_from_gh=build_bt_from_gh,
        build_bt_from_norm=build_bt_from_norm,
        log_label="field",
    )

    assert out == bt_value
    assert build_bt_from_norm_calls == []
