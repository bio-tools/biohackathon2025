"""
Unit tests for match methods.
"""

import pytest

from bridge.pipelines.protocols.map import Method


@pytest.mark.parametrize(
    "item1, item2, expected",
    [
        ("abc", "abc", 1.0),
        ("abc", "def", 0.0),
        (["a", "b"], ["a", "b"], 1.0),
        (["a", "b"], ["a", "b", "c"], 0.0),  # exact match only
        (None, "abc", 0.0),
        ("abc", None, 0.0),
    ],
)
def test_match_exact(item1, item2, expected):
    """
    Assert expected bahviour of exact match method.
    """
    assert Method.EXACT.match_exact(item1, item2) == expected
