"""
TODO
"""

from bridge.core.biotools import License as BTLicense
from bridge.core.github_repo import License as GHLicense
from bridge.pipelines.utils import find_matching_enum_member


def map_license(gh_license: GHLicense | None, bt_license: BTLicense | None) -> dict[str, str] | None:
    """
    TODO
    """
    find_matching_enum_member(gh_license.spdx_id, BTLicense) if gh_license else None

    return {"a": "b"}  # TODO: implement license mapping logic
