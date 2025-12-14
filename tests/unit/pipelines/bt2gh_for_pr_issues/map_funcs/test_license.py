"""
Unit tests for mapping bio.tools license to GitHub PR payload (map_license).
"""

from __future__ import annotations

import pytest

import bridge.pipelines.bt2gh_for_pr_issues.map_funcs.license as mod
from bridge.core.biotools import License as BTLicense

pytestmark = pytest.mark.asyncio

FILENAME = "LICENSE.txt"


def _gh_license(spdx_id: str):
    """
    Create a minimal GHLicense-like object with .spdx_id.
    We avoid importing the real GH model to keep tests stable.
    """

    class _GH:
        def __init__(self, spdx_id: str):
            self.spdx_id = spdx_id

    return _GH(spdx_id)


def _fake_spdx(text: str):
    class _SPDX:
        def __init__(self, t: str):
            self.licenseText = t

    return _SPDX(text)


def _payload_text(out: dict[str, str] | None) -> str:
    assert out is not None
    assert list(out.keys()) == [FILENAME]
    return out[FILENAME]


@pytest.mark.parametrize(
    "gh_spdx_id, bt_license, spdx_text, spdx_raises, expect_pr",
    [
        # -----------------------------
        # bio.tools silent => no PR
        # -----------------------------
        (None, None, "TEXT", False, False),
        ("MIT", None, "TEXT", False, False),
        # -----------------------------
        # both present and equal => no PR
        # (gh_norm is resolved via find_matching_enum_member to BTLicense)
        # -----------------------------
        ("MIT", BTLicense.MIT, "MIT FULL TEXT", False, False),
        ("Apache-2.0", BTLicense.Apache_2_0, "APACHE FULL TEXT", False, False),
        # -----------------------------
        # GitHub present but different => code still proposes bt license PR
        # -----------------------------
        ("MIT", BTLicense.Apache_2_0, "APACHE FULL TEXT", False, True),
        # GitHub license unknown/unmapped => treated as gh_norm None -> propose bt
        ("NOT-A-REAL-SPDX", BTLicense.MIT, "MIT FULL TEXT", False, True),
        # -----------------------------
        # GitHub missing + bio.tools present => propose
        # -----------------------------
        (None, BTLicense.MIT, "MIT FULL TEXT", False, True),
        # -----------------------------
        # SPDX retrieval failure => make_pr returns None => policy returns None
        # -----------------------------
        (None, BTLicense.MIT, "", True, False),
        ("MIT", BTLicense.Apache_2_0, "", True, False),
    ],
)
async def test_map_license(
    monkeypatch,
    gh_spdx_id,
    bt_license,
    spdx_text,
    spdx_raises,
    expect_pr,
):
    async def _compose_spdx_license_metadata(spdx_id: str):
        if spdx_raises:
            raise RuntimeError("boom")
        return _fake_spdx(spdx_text)

    monkeypatch.setattr(mod, "compose_spdx_license_metadata", _compose_spdx_license_metadata)

    gh_license = _gh_license(gh_spdx_id) if gh_spdx_id is not None else None
    out = await mod.map_license(gh_license=gh_license, bt_license=bt_license)

    if not expect_pr:
        assert out is None
        return

    # should be a single-file PR payload
    assert out is not None
    body = _payload_text(out)
    assert body == spdx_text


async def test_map_license_calls_spdx_with_bt_spdx_id(monkeypatch):
    """
    When proposing, it should fetch SPDX text using bt_license.value.
    """
    seen = {"spdx_id": None}

    async def _compose_spdx_license_metadata(spdx_id: str):
        seen["spdx_id"] = spdx_id
        return _fake_spdx("X")

    monkeypatch.setattr(mod, "compose_spdx_license_metadata", _compose_spdx_license_metadata)

    out = await mod.map_license(gh_license=None, bt_license=BTLicense.MIT)
    assert out == {FILENAME: "X"}
    assert seen["spdx_id"] == BTLicense.MIT.value


async def test_map_license_proposes_even_when_github_has_different_license(monkeypatch):
    """
    Conflicts still produce a PR payload under the current policy.
    """

    async def _compose_spdx_license_metadata(_spdx_id: str):
        return _fake_spdx("APACHE FULL")

    monkeypatch.setattr(mod, "compose_spdx_license_metadata", _compose_spdx_license_metadata)

    out = await mod.map_license(gh_license=_gh_license("MIT"), bt_license=BTLicense.Apache_2_0)
    assert out == {FILENAME: "APACHE FULL"}
