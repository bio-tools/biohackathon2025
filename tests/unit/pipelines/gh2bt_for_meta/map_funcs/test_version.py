"""
Unit tests for mapping function map GitHub version to bio.tools version.
"""

import pytest

from bridge.core.biotools import VersionType
from bridge.pipelines.gh2bt_for_meta.map_funcs.version import map_version


def VT(s: str) -> VersionType:
    """Helper: construct a VersionType from a string."""
    return VersionType(root=s)


@pytest.mark.parametrize(
    "gh_version, bt_versions, expected",
    [
        # Case 1: No GitHub version, bio.tools versions exist -> preserve
        (None, [VT("v1.0.0")], [VT("v1.0.0")]),
        ("", [VT("v1.0.0")], [VT("v1.0.0")]),  # falsy string treated as "no GitHub version"
        # Case 2: No GitHub version, no bio.tools versions
        (None, None, None),
        # Case 3: GitHub version exists, no bio.tools versions -> adopt GitHub version
        ("v2.0.0", None, [VT("v2.0.0")]),
        ("v2.0.0", [], [VT("v2.0.0")]),
        # Case 4: GitHub version already present -> unchanged
        ("v1.0.0", [VT("v1.0.0")], [VT("v1.0.0")]),
        # Case 5: GitHub version not present, bt not newer -> append
        ("v2.0.0", [VT("v1.0.0")], [VT("v1.0.0"), VT("v2.0.0")]),
        # Case 6: bio.tools contains a newer comparable version -> reset to GitHub only
        ("v1.6.0", [VT("v1.1.0"), VT("v2.0.0")], [VT("v1.6.0")]),
        # Case 7: bt versions incomparable to GitHub -> ignore "newer" check and append
        (
            "v1.2.3",
            [VT("2025-12-13"), VT("release-candidate")],
            [VT("2025-12-13"), VT("release-candidate"), VT("v1.2.3")],
        ),
    ],
)
def test_map_version(gh_version, bt_versions, expected):
    """
    Test map_version reconciliation behavior.
    """
    result = map_version(gh_version, bt_versions)
    assert result == expected
