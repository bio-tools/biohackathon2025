"""
Unit tests for mapping GitHub license to bio.tools license.
"""

import pytest

from bridge.core.biotools import License
from bridge.pipelines.gh2bt_for_meta.map_funcs.license import map_license


@pytest.mark.parametrize(
    "gh_license, bt_license, expected",
    [
        # Case 1: No GitHub license, bio.tools license exists
        (None, License.MIT, License.MIT),
        # Case 2: No GitHub license, no bio.tools license
        (None, None, License.Not_licensed),
        # Case 3: GitHub license exists, no bio.tools license
        ("Apache-2.0", None, License.Apache_2_0),
        # Case 4: Both licenses exist and match
        ("GPL-3.0", License.GPL_3_0, License.GPL_3_0),
        # Case 5: Both licenses exist and conflict → GitHub wins
        ("BSD-3-Clause", License.MIT, License.BSD_3_Clause),
        # Case 6: GitHub license unrecognized, bio.tools exists → preserve bt
        ("NOT-A-REAL-SPDX", License.MIT, License.MIT),
        # Case 7: GitHub license unrecognized, no bio.tools license
        ("NOT-A-REAL-SPDX", None, License.Other),
    ],
)
def test_map_license(gh_license, bt_license, expected):
    """
    Test map_license reconciliation behavior.
    """
    result = map_license(gh_license, bt_license)
    assert result == expected
