"""
Unit tests for bridge.handlers.extract_meta_from_repo.
"""

import importlib
from types import SimpleNamespace

import pytest

handler_mod = importlib.import_module("bridge.handlers.extract_meta_from_repo")


@pytest.mark.asyncio
async def test_extract_meta_from_repo_happy_no_identifier(monkeypatch):
    """
    Happy path:
    - no identifier -> existing_metadata=None
    - pipeline returns model-like result -> JSON string returned
    """

    metadata_called = {"count": 0}

    async def fake_metadata_composer(**kwargs):
        metadata_called["count"] += 1
        return {"name": "tool-from-biotools"}

    async def fake_repo_composer(**kwargs):
        # must provide repo.full_name because handler uses it
        return SimpleNamespace(repo=SimpleNamespace(full_name="bio-tools/biohackathon2025"))

    async def fake_pipeline(args):
        # sanity check: existing_metadata should be None when identifier is missing
        assert args.kwargs["existing_metadata"] is None

        class Result:
            def model_dump_json(self, **_kwargs):
                return '{"name":"tool-from-pipeline"}'

        return Result()

    def fake_get_schema_composer(_schema):
        return fake_metadata_composer

    class FakeRepoProvider:
        def clone_context(self, repo_full_name: str):
            assert repo_full_name == "bio-tools/biohackathon2025"

            class _Ctx:
                def __enter__(self):
                    return "/tmp/fake-clone"

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _Ctx()

    def fake_get_repo_components(_repo_type):
        return fake_repo_composer, FakeRepoProvider

    def fake_get_pipeline(_schema, _repo_type, _goal):
        class Args:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        return fake_pipeline, Args

    monkeypatch.setattr(handler_mod, "get_schema_composer", fake_get_schema_composer)
    monkeypatch.setattr(handler_mod, "get_repo_components", fake_get_repo_components)
    monkeypatch.setattr(handler_mod, "get_pipeline", fake_get_pipeline)

    out = await handler_mod.extract_meta_from_repo(
        schema="biotools",
        repo_type="github",
        owner="bio-tools",
        repo="biohackathon2025",
    )

    # metadata composer should NOT be called when identifier is absent
    assert metadata_called["count"] == 0
    assert '"tool-from-pipeline"' in out


@pytest.mark.asyncio
async def test_extract_meta_from_repo_happy_with_identifier(monkeypatch):
    """
    Happy path with identifier:
    - identifier present -> existing metadata composer called
    - existing_metadata passed into pipeline args
    """

    async def fake_metadata_composer(**kwargs):
        return {"name": "existing-tool"}

    async def fake_repo_composer(**kwargs):
        return SimpleNamespace(repo=SimpleNamespace(full_name="bio-tools/biohackathon2025"))

    async def fake_pipeline(args):
        assert args.kwargs["existing_metadata"] == {"name": "existing-tool"}

        class Result:
            def model_dump_json(self, **_kwargs):
                return '{"name":"tool-from-pipeline"}'

        return Result()

    def fake_get_schema_composer(_schema):
        return fake_metadata_composer

    class FakeRepoProvider:
        def clone_context(self, _repo_full_name: str):
            class _Ctx:
                def __enter__(self):
                    return "/tmp/fake-clone"

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _Ctx()

    def fake_get_repo_components(_repo_type):
        return fake_repo_composer, FakeRepoProvider

    def fake_get_pipeline(_schema, _repo_type, _goal):
        class Args:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        return fake_pipeline, Args

    monkeypatch.setattr(handler_mod, "get_schema_composer", fake_get_schema_composer)
    monkeypatch.setattr(handler_mod, "get_repo_components", fake_get_repo_components)
    monkeypatch.setattr(handler_mod, "get_pipeline", fake_get_pipeline)

    out = await handler_mod.extract_meta_from_repo(
        schema="biotools",
        repo_type="github",
        owner="bio-tools",
        repo="biohackathon2025",
        identifier="my-tool",
    )

    assert '"tool-from-pipeline"' in out
