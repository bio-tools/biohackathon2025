"""
Unit tests for compose_github_repo.

Public behavior covered:
- requires owner/repo via @require_args (missing args -> raises)
- wires GitHubIngestor(owner, repo) into GitHubRepoTransformer and returns transformed model
- propagates exceptions from transformer/ingestion (no logging assertions)
"""

from __future__ import annotations

from dataclasses import dataclass
import pytest

# Adjust import to your actual module path
import bridge.builders.github.github_composer as mod


# -----------------------------
# Stubs
# -----------------------------


@dataclass
class _GitHubRepoModel:
    owner: str
    repo: str


class _DummyIngestor:
    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo


class _DummyTransformer:
    def __init__(self, ingestor):
        self.ingestor = ingestor
        self.transform_calls = 0

    async def transform(self):
        self.transform_calls += 1
        return _GitHubRepoModel(owner=self.ingestor.owner, repo=self.ingestor.repo)


# -----------------------------
# Tests
# -----------------------------


@pytest.mark.asyncio
async def test_compose_github_repo_wires_ingestor_and_transformer(monkeypatch):
    created = {}

    def _ingestor_factory(owner, repo):
        ing = _DummyIngestor(owner, repo)
        created["ingestor"] = ing
        return ing

    def _transformer_factory(ingestor):
        tr = _DummyTransformer(ingestor)
        created["transformer"] = tr
        return tr

    monkeypatch.setattr(mod, "GitHubIngestor", _ingestor_factory)
    monkeypatch.setattr(mod, "GitHubRepoTransformer", _transformer_factory)
    monkeypatch.setattr(mod, "GitHubRepoModel", _GitHubRepoModel)  # typing only; safe

    out = await mod.compose_github_repo(owner="org", repo="r")

    assert created["ingestor"].owner == "org"
    assert created["ingestor"].repo == "r"
    assert created["transformer"].ingestor is created["ingestor"]
    assert created["transformer"].transform_calls == 1
    assert isinstance(out, _GitHubRepoModel)
    assert (out.owner, out.repo) == ("org", "r")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kwargs",
    [
        {},  # missing both
        {"owner": "org"},  # missing repo
        {"repo": "r"},  # missing owner
        {"owner": None, "repo": "r"},  # owner None should count as missing in require_args
        {"owner": "org", "repo": None},  # repo None should count as missing in require_args
    ],
)
async def test_compose_github_repo_requires_owner_and_repo(kwargs):
    # Exact exception type/message depends on require_args implementation;
    # keep this as a "must raise" contract.
    with pytest.raises(Exception):
        await mod.compose_github_repo(**kwargs)


@pytest.mark.asyncio
async def test_compose_github_repo_propagates_transform_errors(monkeypatch):
    class _BoomTransformer:
        def __init__(self, ingestor):
            self.ingestor = ingestor

        async def transform(self):
            raise RuntimeError("kaboom")

    monkeypatch.setattr(mod, "GitHubIngestor", lambda owner, repo: _DummyIngestor(owner, repo))
    monkeypatch.setattr(mod, "GitHubRepoTransformer", lambda ing: _BoomTransformer(ing))

    with pytest.raises(RuntimeError, match="kaboom"):
        await mod.compose_github_repo(owner="org", repo="r")
