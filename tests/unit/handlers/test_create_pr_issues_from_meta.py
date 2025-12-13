"""
Unit tests for create_pr_issues_from_meta handler.
"""

import importlib
from types import SimpleNamespace

import pytest

handler_mod = importlib.import_module("bridge.handlers.create_pr_issues_from_meta")


@pytest.mark.asyncio
async def test_create_pr_issues_from_meta_happy(monkeypatch):
    """
    Happy path:
    - pipeline returns file changes + issues
    - allow_issues=True
    → PR created and issues created
    """

    async def fake_metadata_composer(**kwargs):
        return {"name": "tool-from-biotools"}

    async def fake_repo_composer(**kwargs):
        return SimpleNamespace(repo=SimpleNamespace(default_branch="main"))

    async def fake_pipeline(_args):
        return (
            {"README.md": "# updated\n"},
            {"Broken metadata": "Something needs fixing."},
        )

    def fake_get_schema_composer(_schema):
        return fake_metadata_composer

    def fake_get_pipeline(_schema, _repo_type, _goal):
        class Args:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        return fake_pipeline, Args

    class FakeRepoProvider:
        async def fork(self, owner, repo):
            return SimpleNamespace(full_name="fakeuser/fakerepo", owner="fakeuser")

        def clone_context(self, _repo_full_name):
            class _Ctx:
                def __enter__(self):
                    return "/tmp/fake-clone"

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _Ctx()

        def apply_changes_and_push(self, repo_path, branch_name, file_changes):
            assert branch_name.startswith("update/")

        async def create_pull_request(self, **_kwargs):
            return {"html_url": "https://github.com/x/y/pull/1"}

        async def create_issue(self, **_kwargs):
            return {"html_url": "https://github.com/x/y/issues/1"}

    def fake_get_repo_components(_repo_type):
        return fake_repo_composer, FakeRepoProvider

    monkeypatch.setattr(handler_mod, "get_schema_composer", fake_get_schema_composer)
    monkeypatch.setattr(handler_mod, "get_repo_components", fake_get_repo_components)
    monkeypatch.setattr(handler_mod, "get_pipeline", fake_get_pipeline)

    result = await handler_mod.create_pr_issues_from_meta(
        schema="biotools",
        repo_type="github",
        owner="bio-tools",
        repo="biohackathon2025",
        identifier="my-tool",
        allow_issues=True,
    )

    assert result["pr"]["html_url"].endswith("/pull/1")
    assert isinstance(result["issues"], list)
    assert len(result["issues"]) == 1


@pytest.mark.asyncio
async def test_create_pr_issues_from_meta_no_pr_when_no_changes(monkeypatch):
    """
    If pipeline returns no file changes:
    → no PR created
    """

    async def fake_metadata_composer(**kwargs):
        return {"name": "tool-from-biotools"}

    async def fake_repo_composer(**kwargs):
        return SimpleNamespace(repo=SimpleNamespace(default_branch="main"))

    async def fake_pipeline(_args):
        return ({}, {})

    def fake_get_schema_composer(_schema):
        return fake_metadata_composer

    def fake_get_pipeline(_schema, _repo_type, _goal):
        class Args:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        return fake_pipeline, Args

    class FakeRepoProvider:
        async def fork(self, owner, repo):
            return SimpleNamespace(full_name="fakeuser/fakerepo", owner="fakeuser")

        def clone_context(self, _repo_full_name):
            class _Ctx:
                def __enter__(self):
                    return "/tmp/fake-clone"

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _Ctx()

        def apply_changes_and_push(self, *_args, **_kwargs):
            raise AssertionError("Should not push when no file changes")

        async def create_pull_request(self, *_args, **_kwargs):
            raise AssertionError("Should not create PR when no file changes")

        async def create_issue(self, *_args, **_kwargs):
            raise AssertionError("Should not create issues")

    def fake_get_repo_components(_repo_type):
        return fake_repo_composer, FakeRepoProvider

    monkeypatch.setattr(handler_mod, "get_schema_composer", fake_get_schema_composer)
    monkeypatch.setattr(handler_mod, "get_repo_components", fake_get_repo_components)
    monkeypatch.setattr(handler_mod, "get_pipeline", fake_get_pipeline)

    result = await handler_mod.create_pr_issues_from_meta(
        schema="biotools",
        repo_type="github",
        owner="bio-tools",
        repo="biohackathon2025",
        identifier="my-tool",
    )

    assert result["pr"] is None
    assert result["issues"] is None
