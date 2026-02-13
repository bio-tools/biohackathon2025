"""
Unit tests for mapping GitHub repository name to bio.tools ID (map_biotools_id).

Public-behavior tests only:
- We test map_biotools_id()
- We do NOT test private helpers directly
"""

from __future__ import annotations

import pytest
import httpx

import bridge.pipelines.gh2bt_for_meta.map_funcs.biotools_id as mod
from bridge.core.biotools import BiotoolsIdType

pytestmark = pytest.mark.asyncio


def _http_404():
    req = httpx.Request("GET", "https://example.org")
    resp = httpx.Response(404, request=req)
    return httpx.HTTPStatusError("Not found", request=req, response=resp)


def _http_500():
    req = httpx.Request("GET", "https://example.org")
    resp = httpx.Response(500, request=req)
    return httpx.HTTPStatusError("Server error", request=req, response=resp)


@pytest.mark.parametrize(
    "gh_name, bt_id, expected_root",
    [
        (None, None, None),
        (None, BiotoolsIdType("existing-id"), "existing-id"),
    ],
)
async def test_map_biotools_id_no_github_name_preserves_bt_id(monkeypatch, gh_name, bt_id, expected_root):
    # Should not call out at all when gh_name is None
    calls = []

    async def _compose(*_a, **_kw):
        calls.append((_a, _kw))
        return None

    monkeypatch.setattr(mod, "compose_biotools_metadata", _compose)

    out = await mod.map_biotools_id(gh_name=gh_name, bt_id=bt_id)

    if expected_root is None:
        assert out is None
    else:
        assert out is not None
        assert out.root == expected_root

    assert calls == []


async def test_map_biotools_id_preserves_bt_id_when_names_contain_each_other(monkeypatch):
    # When gh/bt contain each other, should return bt_id without checking availability.
    calls = []

    async def _compose(*_a, **_kw):
        calls.append((_a, _kw))
        return None

    monkeypatch.setattr(mod, "compose_biotools_metadata", _compose)

    bt_id = BiotoolsIdType("myrepo")
    out = await mod.map_biotools_id(gh_name="MyRepo", bt_id=bt_id)

    assert out == bt_id
    assert calls == []


async def test_map_biotools_id_uses_github_name_if_free(monkeypatch):
    # ID considered "free" when compose_biotools_metadata raises 404
    async def _compose(*_a, **_kw):
        raise _http_404()

    monkeypatch.setattr(mod, "compose_biotools_metadata", _compose)

    out = await mod.map_biotools_id(gh_name="  RepoName  ", bt_id=BiotoolsIdType("different"))

    assert out is not None
    assert out.root == "RepoName"


async def test_map_biotools_id_generates_suffix_when_github_name_taken(monkeypatch):
    # Repo exists, Repo-1 exists, Repo-2 exists, Repo-3 is free
    def exists_ids():
        return {"Repo", "Repo-1", "Repo-2"}

    async def _compose(*_a, **kw):
        ident = kw.get("identifier")
        if ident in exists_ids():
            return {"id": ident}
        raise _http_404()

    monkeypatch.setattr(mod, "compose_biotools_metadata", _compose)

    out = await mod.map_biotools_id(gh_name="Repo", bt_id=BiotoolsIdType("something-else"))

    assert out is not None
    assert out.root == "Repo-3"


async def test_map_biotools_id_returns_none_when_no_suffix_available(monkeypatch):
    # Everything "exists" (either returns non-None OR errors non-404)
    # Policy: non-404 => assume exists, so we can simulate with HTTP 500
    async def _compose(*_a, **_kw):
        raise _http_500()

    monkeypatch.setattr(mod, "compose_biotools_metadata", _compose)

    out = await mod.map_biotools_id(gh_name="Repo", bt_id=BiotoolsIdType("old"))
    assert out is None


async def test_map_biotools_id_bt_id_none_still_uses_github_name_if_free(monkeypatch):
    async def _compose(*_a, **_kw):
        raise _http_404()

    monkeypatch.setattr(mod, "compose_biotools_metadata", _compose)

    out = await mod.map_biotools_id(gh_name="Repo", bt_id=None)

    assert out is not None
    assert out.root == "Repo"
