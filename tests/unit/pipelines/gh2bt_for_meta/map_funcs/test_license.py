"""
Unit tests for mapping function map GitHub license to bio.tools license
"""

import pytest

from bridge.pipelines.gh2bt_for_meta.map_funcs.license import map_license


@pytest.mark.parametrize(
    "gh_license, bt_license, expected",
    [
        # Case 1: No GitHub license, bio.tools license exists
        (None, "MIT", "MIT"),
        # Case 2: No GitHub license, no bio.tools license
        (None, None, None),
        # Case 3: GitHub license exists, no bio.tools license
        ("Apache-2.0", None, "Apache-2.0"),
        # Case 4: Both licenses exist and match
        ("GPL-3.0", "GPL-3.0", "GPL-3.0"),
        # Case 5: Both licenses exist and conflict
        ("BSD-3-Clause", "MIT", "BSD-3-Clause"),
    ],
)
def test_map_license(gh_license, bt_license, expected):
    """
    Test map gh2bt license function.
    """
    result = map_license(gh_license, bt_license)
    assert result == expected
