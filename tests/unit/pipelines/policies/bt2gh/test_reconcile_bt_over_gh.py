"""
Unit tests for reconcile_bt_over_gh.

These tests focus strictly on reconciliation behavior, not logging.
"""

from __future__ import annotations

import pytest

import bridge.pipelines.policies.bt2gh as recon


pytestmark = pytest.mark.asyncio


async def _async_make_output(x):
    return f"out:{x}"


def _sync_make_output(x):
    return f"out:{x}"


def _make_recording_output(return_value_factory):
    """
    Build a make_output callable that records its single argument into `calls`.
    Returns (make_output, calls).
    """
    calls: list[str] = []

    def make_output(x):
        calls.append(x)
        return return_value_factory(x)

    return make_output, calls


@pytest.mark.parametrize(
    "case, gh_norm, bt_norm, make_output, equality_fn, expected, expected_calls",
    [
        # 1) bio.tools silent => None (no issue), never calls make_output
        ("bt silent (gh present)", "gh", None, _sync_make_output, None, None, []),
        ("bt silent (both None)", None, None, _sync_make_output, None, None, []),
        # 2) both present and equal => None, never calls make_output
        ("equal (sync)", "same", "same", _sync_make_output, None, None, []),
        ("equal (async)", "same", "same", _async_make_output, None, None, []),
        # 3) conflict => propose bt via make_output(bt_norm)
        ("conflict (sync)", "gh", "bt", _sync_make_output, None, "out:bt", ["bt"]),
        ("conflict (async)", "gh", "bt", _async_make_output, None, "out:bt", ["bt"]),
        # 4) gh missing but bt present => propose bt via make_output(bt_norm)
        ("gh missing (sync)", None, "bt", _sync_make_output, None, "out:bt", ["bt"]),
        ("gh missing (async)", None, "bt", _async_make_output, None, "out:bt", ["bt"]),
        # 5) custom equality_fn decides equality (treat as equal => None)
        ("custom equality => equal", "GH", "gh", _sync_make_output, lambda a, b: a.lower() == b.lower(), None, []),
        # equality_fn ignored if gh_norm is None (still should propose)
        ("equality_fn ignored when gh None", None, "bt", _sync_make_output, lambda a, b: False, "out:bt", ["bt"]),
        # 6) custom equality_fn forces conflict (treat as conflict => output uses bt_norm)
        ("custom equality => conflict", "GH", "gh", _sync_make_output, lambda a, b: False, "out:gh", ["gh"]),
    ],
)
async def test_reconcile_bt_over_gh(case, gh_norm, bt_norm, make_output, equality_fn, expected, expected_calls):
    # Wrap make_output with a recorder so we can assert call behavior in-table.
    # We keep the original make_output semantics (sync or async) by delegating to it.
    calls: list[str] = []

    async def _wrapped_make_output(x):
        calls.append(x)
        return (
            await make_output(x)
            if callable(getattr(make_output, "__await__", None))
            else (await make_output(x))  # this branch won't happen, but keeps type-checkers quiet
        )

    # Detect whether make_output is async by checking if calling it returns an awaitable.
    async def _maybe_call(x):
        res = make_output(x)
        if hasattr(res, "__await__"):
            return await res
        return res

    async def _recording_make_output(x):
        calls.append(x)
        return await _maybe_call(x)

    out = await recon.reconcile_bt_over_gh(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        make_output=_recording_make_output,
        log_label="field",
        equality_fn=equality_fn,
    )

    assert out == expected, case
    assert calls == expected_calls, case


@pytest.mark.parametrize(
    "case, gh_norm, bt_norm, equality_fn, expected, expected_calls",
    [
        ("bt silent", "anything", None, None, None, []),
        ("equal", "same", "same", None, None, []),
        ("conflict", "gh", "bt", None, {"x": "bt"}, ["bt"]),
        ("gh missing", None, "bt2", None, {"x": "bt2"}, ["bt2"]),
    ],
)
async def test_reconcile_bt_over_gh_with_dict_payload_and_call_tracking(
    case, gh_norm, bt_norm, equality_fn, expected, expected_calls
):
    make_output, calls = _make_recording_output(lambda x: {"x": x})

    out = await recon.reconcile_bt_over_gh(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        make_output=make_output,
        log_label="field",
        equality_fn=equality_fn,
    )

    assert out == expected, case
    assert calls == expected_calls, case
