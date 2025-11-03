"""
Unit tests for bridge.utils.require_args.

These tests verify that the require_args decorator enforces required keyword
arguments for asynchronous functions.
"""

import pytest

from bridge.utils import require_args


@pytest.mark.asyncio
async def test_require_args_happy_path():
    """
    Test that the require_args decorator allows function execution when all
    required arguments are provided.

    Raises
    ------
    AssertionError
        If the function does not return the expected result.
    """

    @require_args("a", "b")
    async def fn(**kwargs):
        return kwargs["a"] + kwargs["b"]

    assert await fn(a=1, b=2) == 3


@pytest.mark.asyncio
async def test_require_args_missing():
    """
    Test that the require_args decorator raises a ValueError when required arguments
    are missing.

    Returns
    -------
    ValueError
        If the function is called without the required arguments.
    """

    @require_args("a")
    async def fn(**kwargs):
        return 1

    with pytest.raises(ValueError, match="Missing required args: a"):
        await fn()
