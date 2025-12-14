"""
Unit tests for argument validation in handler functions.
"""

import importlib

import pytest

create_mod = importlib.import_module("bridge.handlers.create_pr_issues_from_meta")
extract_mod = importlib.import_module("bridge.handlers.extract_meta_from_repo")


@pytest.mark.asyncio
async def test_create_pr_issues_from_meta_missing_args():
    """
    create_pr_issues_from_meta should raise ValueError when required args are missing.
    """
    with pytest.raises(ValueError) as exc:
        await create_mod.create_pr_issues_from_meta(schema="biotools", repo_type="github")

    msg = str(exc.value)
    assert "Missing required args" in msg
    assert "owner" in msg
    assert "repo" in msg
    assert "identifier" in msg


@pytest.mark.asyncio
async def test_extract_meta_from_repo_missing_args():
    """
    extract_meta_from_repo should raise ValueError when required args are missing.
    """
    with pytest.raises(ValueError) as exc:
        await extract_mod.extract_meta_from_repo(schema="biotools", repo_type="github")

    msg = str(exc.value)
    assert "Missing required args" in msg
    assert "owner" in msg
    assert "repo" in msg
