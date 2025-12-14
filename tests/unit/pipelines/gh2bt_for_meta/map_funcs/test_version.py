"""
Unit tests for mapping function map GitHub version to bio.tools version.
"""

import pytest

from bridge.core.biotools import VersionType
from bridge.pipelines.gh2bt_for_meta.map_funcs.version import map_version


def VT(s: str) -> VersionType:
    """Helper: construct a VersionType from a string."""
    return VersionType(root=s)


"""
Unit tests for mapping function map GitHub version to bio.tools version.

Covers multiple versioning styles supported by the shared parser:
- semantic versions (with optional v-prefix)
- dates
- integers
- ranges
- raw labels (incomparable)
"""

import pytest

from bridge.core.biotools import VersionType
from bridge.pipelines.gh2bt_for_meta.map_funcs.version import map_version


def VT(s: str) -> VersionType:
    return VersionType(root=s)


@pytest.mark.parametrize(
    "gh_version, bt_versions, expected",
    [
        # --- GitHub silent: preserve bt as-is ---
        (None, [VT("v1.0.0")], [VT("v1.0.0")]),
        (None, [VT("2025-12-13")], [VT("2025-12-13")]),
        (None, None, None),
        ("", [VT("v1.0.0")], [VT("v1.0.0")]),  # falsy string treated as missing
        # --- No bt versions: adopt GitHub ---
        ("v2.0.0", None, [VT("v2.0.0")]),
        ("2025-12-13", [], [VT("2025-12-13")]),
        ("42", None, [VT("42")]),
        ("1.0 - 2.0", None, [VT("1.0 - 2.0")]),
        ("release-candidate", None, [VT("release-candidate")]),
        # --- Exact presence: unchanged ---
        ("v1.0.0", [VT("v1.0.0")], [VT("v1.0.0")]),
        ("2025-12-13", [VT("2025-12-13")], [VT("2025-12-13")]),
        ("42", [VT("42")], [VT("42")]),
        ("1.0 - 2.0", [VT("1.0 - 2.0")], [VT("1.0 - 2.0")]),
        ("release-candidate", [VT("release-candidate")], [VT("release-candidate")]),
        # --- Comparable, bt NOT newer: append GH ---
        ("v2.0.0", [VT("v1.0.0")], [VT("v1.0.0"), VT("v2.0.0")]),
        ("2025-12-13", [VT("2025-01-01")], [VT("2025-01-01"), VT("2025-12-13")]),
        ("10", [VT("9")], [VT("9"), VT("10")]),
        # range is compared by its upper bound; 1.0-2.0 is not newer than 2.5
        ("2.5", [VT("1.0 - 2.0")], [VT("1.0 - 2.0"), VT("2.5")]),
        # --- Comparable, bt newer: reset to GH only ---
        ("v1.6.0", [VT("v1.1.0"), VT("v2.0.0")], [VT("v1.6.0")]),
        ("2025-06-01", [VT("2025-12-13")], [VT("2025-06-01")]),
        ("9", [VT("10")], [VT("9")]),
        # range upper bound (3.0) newer than gh (2.5) => reset
        ("2.5", [VT("1.0 - 3.0")], [VT("2.5")]),
        # --- Incomparable kinds: "newer" check ignored, so append GH ---
        ("v1.2.3", [VT("2025-12-13")], [VT("2025-12-13"), VT("v1.2.3")]),  # DATE vs SEMVER
        ("2025-12-13", [VT("v1.2.3")], [VT("v1.2.3"), VT("2025-12-13")]),  # SEMVER vs DATE
        ("v1.2.3", [VT("release-candidate")], [VT("release-candidate"), VT("v1.2.3")]),  # RAW vs SEMVER
        ("release-candidate", [VT("v1.2.3")], [VT("v1.2.3"), VT("release-candidate")]),  # SEMVER vs RAW
    ],
)
def test_map_version_multiple_versioning_styles(gh_version, bt_versions, expected):
    """
    Test map_version reconciliation behavior across many versioning styles.
    """
    result = map_version(gh_version, bt_versions)
    assert result == expected
