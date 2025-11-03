"""
Unit tests for argument validation in handler functions.
"""

import importlib

import pytest

create_mod = importlib.import_module("bridge.handlers.create_pr_from_meta")
extract_mod = importlib.import_module("bridge.handlers.extract_meta_from_repo")


@pytest.mark.asyncio
async def test_create_pr_from_meta_missing_args():
    """
    Test that create_pr_from_meta raises ValueError when required args are missing.

    Raises
    ------
    ValueError
        If required arguments are not provided.
    """
    with pytest.raises(ValueError, match="Missing required args: owner, repo, identifier"):
        await create_mod.create_pr_from_meta(schema="biotools", repo_type="github")


@pytest.mark.asyncio
async def test_extract_meta_from_repo_missing_args():
    """
    Test that extract_meta_from_repo raises ValueError when required args are missing.

    Raises
    ------
    ValueError
        If required arguments are not provided.
    """
    with pytest.raises(ValueError, match="Missing required args: owner, repo"):
        await extract_mod.extract_meta_from_repo(schema="biotools", repo_type="github")
