"""
Unit tests for bridge.handlers.extract_meta_from_repo.
"""

import importlib

import pytest

handler_mod = importlib.import_module("bridge.handlers.extract_meta_from_repo")


@pytest.mark.asyncio
async def test_extract_meta_from_repo_happy(monkeypatch):
    """
    Test that extract_meta_from_repo works end-to-end with mocked components.

    Raises
    ------
    AssertionError
        If the final output does not match the expected values.
    """

    async def fake_metadata_composer(**kwargs):
        return {"name": "tool-from-biotools"}

    async def fake_repo_composer(**kwargs):
        class Repo:
            default_branch = "main"

        return Repo()

    async def fake_pipeline(args):
        class Result:
            def model_dump_json(self, **kwargs):
                return '{"name":"tool-from-pipeline"}'

        return Result()

    def fake_get_schema_composer(schema):
        return fake_metadata_composer

    def fake_get_repo_components(repo_type):
        # (composer, provider)
        return fake_repo_composer, None

    def fake_get_pipeline(schema, repo_type, goal):
        class Args:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        return fake_pipeline, Args

    # patch the names that the handler module already imported
    monkeypatch.setattr(handler_mod, "get_schema_composer", fake_get_schema_composer)
    monkeypatch.setattr(handler_mod, "get_repo_components", fake_get_repo_components)
    monkeypatch.setattr(handler_mod, "get_pipeline", fake_get_pipeline)

    out = await handler_mod.extract_meta_from_repo(
        schema="biotools",
        repo_type="github",
        owner="bio-tools",
        repo="biohackathon2025",
    )

    assert '"tool-from-pipeline"' in out
