"""
Unit tests for reconcile_gh_over_bt.

These tests focus strictly on reconciliation behavior, not logging.
"""

from __future__ import annotations

import pytest

import bridge.pipelines.policies.gh2bt as recon


def _bt_prefix(x):
    return f"bt:{x}"


@pytest.mark.parametrize(
    "case, gh_norm, bt_norm, bt_value, build_bt_from_gh, equality_fn, expected",
    [
        (
            "github silent -> preserve bt_value",
            None,
            "whatever",
            "existing-bt",
            _bt_prefix,
            None,
            "existing-bt",
        ),
        (
            "bt missing -> build from github",
            "MIT",
            None,
            None,
            _bt_prefix,
            None,
            "bt:MIT",
        ),
        (
            "cannot build bt from github -> preserve bt_value",
            "something",
            None,
            "keep-this",
            lambda _x: None,
            None,
            "keep-this",
        ),
        (
            "equal -> preserve existing bt_value",
            "same",
            "same",
            "keep-bt",
            lambda x: x,
            None,
            "keep-bt",
        ),
        (
            "conflict -> github wins (overwrite)",
            "new",
            "old",
            "old-bt",
            _bt_prefix,
            None,
            "bt:new",
        ),
        (
            "custom equality_fn used (treat as equal) -> preserve bt_value",
            ["py", "c++"],
            {"c++", "py"},
            ["preserve-this"],
            lambda gh: set(gh),
            lambda built_bt, bt_norm: built_bt == bt_norm,
            ["preserve-this"],
        ),
    ],
)
def test_reconcile_gh_over_bt(case, gh_norm, bt_norm, bt_value, build_bt_from_gh, equality_fn, expected):
    result = recon.reconcile_gh_over_bt(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        bt_value=bt_value,
        build_bt_from_gh=build_bt_from_gh,
        log_label="field",
        equality_fn=equality_fn,
    )
    assert result == expected, case
