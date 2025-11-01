"""
Unit tests for bridge.handlers.create_pr_from_meta.
"""

import importlib
from types import SimpleNamespace

import pytest

handler_mod = importlib.import_module("bridge.handlers.create_pr_from_meta")


@pytest.mark.asyncio
async def test_create_pr_from_meta_happy(monkeypatch):
    """
    Test that create_pr_from_meta works end-to-end with mocked components.

    Raises
    ------
    AssertionError
        If the final output does not match the expected values.
    """

    async def fake_metadata_composer(**kwargs):
        return {"name": "tool-from-biotools"}

    async def fake_repo_composer(**kwargs):
        # what handler expects from repo_model: .default_branch
        return SimpleNamespace(default_branch="main")

    async def fake_pipeline(args):
        # pipeline returns dict of file changes
        return {"README.md": "# updated from pipeline\n"}

    def fake_get_schema_composer(schema):
        return fake_metadata_composer

    def fake_get_pipeline(schema, repo_type, goal):
        class Args:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        return fake_pipeline, Args

    class FakeRepoProvider:
        def __init__(self):
            self.applied = False
            self.pr_created = False

        async def fork(self, owner: str, repo: str):
            # handler expects .full_name and .owner
            return SimpleNamespace(full_name="fakeuser/fakerepo", owner="fakeuser", repo="fakerepo")

        def clone_context(self, repo_full_name: str):
            class _Ctx:
                def __enter__(self):
                    return "/tmp/fake-clone"

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _Ctx()

        def apply_changes_and_push(self, repo_path: str, branch_name: str, file_changes: dict):
            assert repo_path == "/tmp/fake-clone"
            assert branch_name == "update"
            assert "README.md" in file_changes
            self.applied = True

        async def create_pull_request(self, owner, repo, title, body, head_branch, base_branch):
            self.pr_created = True
            return {"html_url": "https://github.com/x/y/pull/1"}

    def fake_get_repo_components(repo_type):
        # (composer, provider-factory)
        return fake_repo_composer, FakeRepoProvider

    monkeypatch.setattr(handler_mod, "get_schema_composer", fake_get_schema_composer)
    monkeypatch.setattr(handler_mod, "get_repo_components", fake_get_repo_components)
    monkeypatch.setattr(handler_mod, "get_pipeline", fake_get_pipeline)

    result = await handler_mod.create_pr_from_meta(
        schema="biotools",
        repo_type="github",
        owner="bio-tools",
        repo="biohackathon2025",
        identifier="my-tool",
    )

    assert result["html_url"] == "https://github.com/x/y/pull/1"
