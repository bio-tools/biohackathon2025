from __future__ import annotations

import pytest
from types import SimpleNamespace

import bridge.pipelines.gh2bt_for_meta.main as mod

# Use the real bio.tools types to keep output values realistic
from bridge.core.biotools import (
    BiotoolsIdType,
    UrlftpType,
    VersionType,
    License as BioToolsLicense,
    LanguageEnum,
)

pytestmark = pytest.mark.asyncio

from ..dummy.dummy_biotools import DummyBioToolsTool
from ..dummy.dummy_github import DummyGitHubRepoModel


class _Runner:
    """Async runner to simulate mapper.map[*].run()."""

    def __init__(self, value):
        self.value = value
        self.calls = 0

    async def run(self):
        self.calls += 1
        return self.value


@pytest.fixture()
def patch_mapper(monkeypatch):
    """
    Patch MapGitHub2BioTools so tests are deterministic and don't touch IO.
    """
    state: dict[str, object] = {}

    def _factory(*, repo, metadata, repo_path):
        state["repo"] = repo
        state["metadata"] = metadata
        state["repo_path"] = repo_path

        mapper = SimpleNamespace(map=state["map"])
        return mapper

    monkeypatch.setattr(mod, "MapGitHub2BioTools", _factory)
    return state


def _args(*, repo_model, repo_path="/tmp/repo", existing_metadata=None):
    """
    Deliberately NOT constructing GitHubToBiotoolsForMetaPipelineArgs (Pydantic),
    because these are unit tests for pipeline behavior, not input validation.
    """
    return SimpleNamespace(
        repo_model=repo_model,
        repo_path=repo_path,
        existing_metadata=existing_metadata,
    )


async def test_run_passes_repo_and_existing_metadata_into_mapper_and_builds_model(patch_mapper):
    gh_repo = DummyGitHubRepoModel()
    existing = DummyBioToolsTool()

    runners = {
        "biotools_id": _Runner(BiotoolsIdType(root="new-tool-id")),
        "name": _Runner("New Tool Name"),
        "description": _Runner("Mapped description"),
        "homepage": _Runner(UrlftpType(root="https://example.org/new-home")),
        "maturity": _Runner(existing.maturity),
        "language": _Runner([LanguageEnum.Python]),
        "license": _Runner(BioToolsLicense.MIT),
        "version": _Runner([VersionType(root="2.0.0")]),
        "documentation": _Runner(existing.documentation),
        "publication": _Runner(existing.publication),
    }
    patch_mapper["map"] = runners

    out = await mod.run(_args(repo_model=gh_repo, existing_metadata=existing))

    # mapper wiring
    assert patch_mapper["repo"] is gh_repo
    assert patch_mapper["metadata"] is existing
    assert patch_mapper["repo_path"] == "/tmp/repo"

    # output model fields
    assert out.biotoolsID.root == "new-tool-id"
    assert out.name == "New Tool Name"
    assert out.description == "Mapped description"
    assert out.homepage.root == "https://example.org/new-home"
    assert out.license == BioToolsLicense.MIT
    assert out.version[0].root == "2.0.0"
    assert out.language == [LanguageEnum.Python]

    # each map key awaited once
    for r in runners.values():
        assert r.calls == 1


async def test_run_sets_placeholder_description_when_mapper_returns_none(patch_mapper):
    gh_repo = DummyGitHubRepoModel()

    runners = {
        "biotools_id": _Runner(BiotoolsIdType(root="tool-id")),
        "name": _Runner("Tool Name"),
        "description": _Runner(None),  # triggers fallback
        "homepage": _Runner(UrlftpType(root="https://example.org")),
        "maturity": _Runner(None),
        "language": _Runner([LanguageEnum.Python]),
        "license": _Runner(BioToolsLicense.MIT),
        "version": _Runner([VersionType(root="1.2.3")]),
        "documentation": _Runner(None),
        "publication": _Runner(None),
    }
    patch_mapper["map"] = runners

    out = await mod.run(_args(repo_model=gh_repo))

    assert out.description == "***Please change this description***"
    assert out.name == "Tool Name"
    assert out.biotoolsID.root == "tool-id"

    for r in runners.values():
        assert r.calls == 1


async def test_run_works_when_existing_metadata_is_none(patch_mapper):
    """
    Minimal smoke test: no existing metadata should still build a model.
    """
    gh_repo = DummyGitHubRepoModel()

    runners = {
        "biotools_id": _Runner(BiotoolsIdType(root="tool-id")),
        "name": _Runner("Tool Name"),
        "description": _Runner("A valid description."),
        "homepage": _Runner(UrlftpType(root="https://example.org")),
        "maturity": _Runner(None),
        "language": _Runner([LanguageEnum.Python]),
        "license": _Runner(BioToolsLicense.MIT),
        "version": _Runner([VersionType(root="1.2.3")]),
        "documentation": _Runner(None),
        "publication": _Runner(None),
    }
    patch_mapper["map"] = runners

    out = await mod.run(_args(repo_model=gh_repo, existing_metadata=None))
    assert out.name == "Tool Name"
