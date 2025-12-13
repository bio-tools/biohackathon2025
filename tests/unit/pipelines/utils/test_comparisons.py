"""
Unit tests for string containment utility functions.
"""

import pytest

from bridge.pipelines.utils.comparisons import str_contain_each_other


@pytest.mark.parametrize(
    "str1, str2, expected",
    [
        # Exact match
        ("abc", "abc", True),
        # One contains the other
        ("bio.tools", "tools", True),
        ("tools", "bio.tools", True),
        # Case-insensitive containment
        ("BioTools", "biotools", True),
        ("GitHub", "hub", True),
        # Partial overlap but no containment
        ("analysis", "ally", False),
        # Completely different strings
        ("python", "java", False),
        # One-character containment
        ("a", "alphabet", True),
        ("alphabet", "z", False),
        # Whitespace is treated literally
        ("machine learning", "learning", True),
        ("machinelearning", "machine learning", False),
    ],
)
def test_str_contain_each_other(str1, str2, expected):
    """
    Test case-insensitive mutual string containment.
    """
    assert str_contain_each_other(str1, str2) is expected
