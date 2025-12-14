"""
Unit tests for GitHubRepoTransformer.

Covers:
- calls ingestor.fetch()
- builds a GitHubRepoModel from raw dict parts
- handles None for optional sections
- preserves readme
- normalizes empty-string/falsey homepage to None
"""

from __future__ import annotations

from dataclasses import dataclass
import pytest

# Adjust to your real module path
import bridge.builders.github.github_transformer as mod


pytestmark = pytest.mark.asyncio


# -----------------------------
# Minimal stubs (avoid pydantic / generated model requirements)
# -----------------------------


@dataclass
class _FullRepository:
    raw: dict

    def __init__(self, **kwargs):
        self.raw = dict(kwargs)


@dataclass
class _Release:
    raw: dict

    def __init__(self, **kwargs):
        self.raw = dict(kwargs)


@dataclass
class _GitHubPages:
    raw: dict

    def __init__(self, **kwargs):
        self.raw = dict(kwargs)


@dataclass
class _Language:
    raw: dict

    def __init__(self, **kwargs):
        self.raw = dict(kwargs)


@dataclass
class _GitHubRepoModel:
    repo: _FullRepository
    latest_release: _Release | None
    github_pages: _GitHubPages | None
    readme: str | None
    languages: _Language | None


class _DummyIngestor:
    def __init__(self, owner: str, repo: str, payload: dict):
        self.owner = owner
        self.repo = repo
        self._payload = payload
        self.fetch_calls = 0

    async def fetch(self) -> dict:
        self.fetch_calls += 1
        return self._payload


@pytest.fixture()
def patch_models(monkeypatch):
    """
    Patch the transformer module to use tiny stubs instead of generated models.
    """
    monkeypatch.setattr(mod, "FullRepository", _FullRepository)
    monkeypatch.setattr(mod, "Release", _Release)
    monkeypatch.setattr(mod, "GitHubPages", _GitHubPages)
    monkeypatch.setattr(mod, "Language", _Language)
    monkeypatch.setattr(mod, "GitHubRepoModel", _GitHubRepoModel)


# -----------------------------
# Tests
# -----------------------------


async def test_transform_builds_model_from_all_sections(patch_models):
    payload = {
        "repo": {"name": "repo", "homepage": "https://example.org", "html_url": "https://github.com/o/r"},
        "latest_release": {"tag_name": "v1.2.3"},
        "github_pages": {"html_url": "https://o.github.io/r"},
        "readme": "# Title\n",
        "languages": {"Python": 123},
    }
    ing = _DummyIngestor("o", "r", payload)
    tr = mod.GitHubRepoTransformer(ingestor=ing)

    out = await tr.transform()

    assert ing.fetch_calls == 1
    assert isinstance(out, _GitHubRepoModel)

    assert isinstance(out.repo, _FullRepository)
    assert out.repo.raw["name"] == "repo"
    assert out.repo.raw["homepage"] == "https://example.org"

    assert isinstance(out.latest_release, _Release)
    assert out.latest_release.raw["tag_name"] == "v1.2.3"

    assert isinstance(out.github_pages, _GitHubPages)
    assert out.github_pages.raw["html_url"].endswith("/r")

    assert out.readme == "# Title\n"

    assert isinstance(out.languages, _Language)
    assert out.languages.raw["Python"] == 123


@pytest.mark.parametrize(
    "latest_release, github_pages, languages",
    [
        (None, None, None),
        ({"tag_name": "v0.1.0"}, None, None),
        (None, {"html_url": "https://x"}, None),
        (None, None, {"Python": 1}),
    ],
)
async def test_transform_handles_optional_sections_being_none(patch_models, latest_release, github_pages, languages):
    payload = {
        "repo": {"name": "repo", "homepage": "https://example.org", "html_url": "https://github.com/o/r"},
        "latest_release": latest_release,
        "github_pages": github_pages,
        "readme": None,
        "languages": languages,
    }
    ing = _DummyIngestor("o", "r", payload)
    tr = mod.GitHubRepoTransformer(ingestor=ing)

    out = await tr.transform()

    assert isinstance(out.repo, _FullRepository)
    assert out.readme is None

    if latest_release is None:
        assert out.latest_release is None
    else:
        assert isinstance(out.latest_release, _Release)

    if github_pages is None:
        assert out.github_pages is None
    else:
        assert isinstance(out.github_pages, _GitHubPages)

    if languages is None:
        assert out.languages is None
    else:
        assert isinstance(out.languages, _Language)


@pytest.mark.parametrize("homepage_value", ["", None, False])
async def test_transform_normalizes_falsey_homepage_to_none(patch_models, homepage_value):
    payload = {
        "repo": {"name": "repo", "homepage": homepage_value, "html_url": "https://github.com/o/r"},
        "latest_release": None,
        "github_pages": None,
        "readme": None,
        "languages": None,
    }
    ing = _DummyIngestor("o", "r", payload)
    tr = mod.GitHubRepoTransformer(ingestor=ing)

    out = await tr.transform()

    assert out.repo.raw["homepage"] is None
