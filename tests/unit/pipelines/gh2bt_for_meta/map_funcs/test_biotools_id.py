"""
Unit tests for mapping GitHub repository name to bio.tools ID (map_biotools_id).
"""

from __future__ import annotations

import pytest

import bridge.pipelines.gh2bt_for_meta.map_funcs.biotools_id as mod


pytestmark = pytest.mark.asyncio


# --------------------------------------------------------------------
# map_biotools_id
# --------------------------------------------------------------------


@pytest.mark.parametrize(
    "gh_name, bt_id",
    [
        (None, None),
        (None, "existing-id"),
    ],
)
async def test_map_biotools_id_no_github_name_preserves_bt_id(gh_name, bt_id):
    out = await mod.map_biotools_id(gh_name=gh_name, bt_id=bt_id)
    assert out == bt_id


async def test_map_biotools_id_preserves_bt_id_when_strings_contain_each_other(monkeypatch):
    """
    If bt_id exists and gh/bt contain each other (case-insensitive),
    mapper should return the existing bt_id and never query availability.
    """
    monkeypatch.setattr(mod, "normalize_text", lambda s, **_: s or "")
    monkeypatch.setattr(mod, "str_contain_each_other", lambda a, b: True)

    calls = []

    async def _exists(_id: str) -> bool:
        calls.append(_id)
        return False

    monkeypatch.setattr(mod, "_matching_biotools_id_exists", _exists)

    out = await mod.map_biotools_id(gh_name="MyRepo", bt_id="myrepo")
    assert out == "myrepo"
    assert calls == []  # should not check bio.tools at all


async def test_map_biotools_id_uses_github_name_if_free(monkeypatch):
    monkeypatch.setattr(mod, "normalize_text", lambda s, **_: s.strip() if s else "")
    monkeypatch.setattr(mod, "str_contain_each_other", lambda a, b: False)

    async def _exists(_id: str) -> bool:
        return False  # nothing exists

    monkeypatch.setattr(mod, "_matching_biotools_id_exists", _exists)

    out = await mod.map_biotools_id(gh_name="  RepoName  ", bt_id="different")
    assert out == "RepoName"


async def test_map_biotools_id_generates_suffix_when_github_name_taken(monkeypatch):
    """
    If gh_norm exists, try gh_norm-1, gh_norm-2, ... until first free.
    """
    monkeypatch.setattr(mod, "normalize_text", lambda s, **_: s.strip() if s else "")
    monkeypatch.setattr(mod, "str_contain_each_other", lambda a, b: False)

    taken = {"Repo", "Repo-1", "Repo-2"}  # first free should be Repo-3
    checked = []

    async def _exists(_id: str) -> bool:
        checked.append(_id)
        return _id in taken

    monkeypatch.setattr(mod, "_matching_biotools_id_exists", _exists)

    out = await mod.map_biotools_id(gh_name="Repo", bt_id="something-else")
    assert out == "Repo-3"

    # Ensure it checked base + incremental candidates in order
    assert checked[:4] == ["Repo", "Repo-1", "Repo-2", "Repo-3"]


async def test_map_biotools_id_returns_none_when_no_suffix_available(monkeypatch):
    """
    If gh_norm and gh_norm-1..-99 are all taken, return None.
    """
    monkeypatch.setattr(mod, "normalize_text", lambda s, **_: s.strip() if s else "")
    monkeypatch.setattr(mod, "str_contain_each_other", lambda a, b: False)

    async def _exists(_id: str) -> bool:
        return True  # everything exists

    monkeypatch.setattr(mod, "_matching_biotools_id_exists", _exists)

    out = await mod.map_biotools_id(gh_name="Repo", bt_id="old")
    assert out is None


async def test_map_biotools_id_bt_id_none_still_uses_github_name_if_free(monkeypatch):
    monkeypatch.setattr(mod, "normalize_text", lambda s, **_: s.strip() if s else "")
    # bt_id None -> contain check is skipped anyway, but keep this sane
    monkeypatch.setattr(mod, "str_contain_each_other", lambda a, b: False)

    async def _exists(_id: str) -> bool:
        return False

    monkeypatch.setattr(mod, "_matching_biotools_id_exists", _exists)

    out = await mod.map_biotools_id(gh_name="Repo", bt_id=None)
    assert out == "Repo"


# --------------------------------------------------------------------
# _matching_biotools_id_exists
# --------------------------------------------------------------------


async def test_matching_biotools_id_exists_returns_false_on_404(monkeypatch):
    """
    compose_biotools_metadata raises httpx.HTTPStatusError with 404 => False
    """

    class _Resp:
        status_code = 404

    class _E(mod.httpx.HTTPStatusError):
        def __init__(self):
            super().__init__("nope", request=None, response=_Resp())

    async def _compose(*_args, **_kwargs):
        raise _E()

    monkeypatch.setattr(mod, "compose_biotools_metadata", _compose)

    assert await mod._matching_biotools_id_exists("anything") is False


async def test_matching_biotools_id_exists_returns_true_on_non_404_error(monkeypatch):
    """
    Any non-404 error => assume exists (True) to avoid false negatives.
    """

    class _Resp:
        status_code = 500

    class _E(mod.httpx.HTTPStatusError):
        def __init__(self):
            super().__init__("boom", request=None, response=_Resp())

    async def _compose(*_args, **_kwargs):
        raise _E()

    monkeypatch.setattr(mod, "compose_biotools_metadata", _compose)

    assert await mod._matching_biotools_id_exists("anything") is True


async def test_matching_biotools_id_exists_returns_true_when_metadata_not_none(monkeypatch):
    async def _compose(*_args, **_kwargs):
        return {"id": "x"}  # any non-None

    monkeypatch.setattr(mod, "compose_biotools_metadata", _compose)

    assert await mod._matching_biotools_id_exists("x") is True


async def test_matching_biotools_id_exists_returns_false_when_metadata_is_none(monkeypatch):
    async def _compose(*_args, **_kwargs):
        return None

    monkeypatch.setattr(mod, "compose_biotools_metadata", _compose)

    assert await mod._matching_biotools_id_exists("x") is False
