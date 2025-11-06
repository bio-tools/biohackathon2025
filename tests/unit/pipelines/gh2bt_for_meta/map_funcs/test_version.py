"""
Unit tests for mapping function map GitHub version to bio.tools version
"""

import pytest

from bridge.pipelines.gh2bt_for_meta.map_funcs.version import map_version


@pytest.mark.parametrize(
    "gh_version, bt_version, expected",
    [
        # Case 1: No GitHub version, bio.tools version exists
        (None, ["v1.0.0"], None),
        # Case 2: No GitHub version, no bio.tools version
        (None, None, None),
        # Case 3: GitHub version exists, no bio.tools version
        ("v2.0.0", None, ["v2.0.0"]),
        # Case 4: Both versions exist and match
        ("v1.0.0", ["v1.0.0"], ["v1.0.0"]),
        # Case 5: Both versions exist and conflict
        ("v2.0.0", ["v1.0.0"], ["v2.0.0"]),
        # Case 6: bio.tools version is newer than GitHub version
        ("v1.6.0", ["v1.1.0", "v2.0.0"], ["v1.6.0"]),
    ],
)
def test_map_version(gh_version, bt_version, expected):
    """
    Test map gh2bt version function.
    """
    result = map_version(gh_version, bt_version)
    assert result == expected
