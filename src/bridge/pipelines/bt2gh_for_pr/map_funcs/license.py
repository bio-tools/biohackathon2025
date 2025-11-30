"""
TODO
"""

from bridge.core.biotools import License as BTLicense
from bridge.core.github_repo import License as GHLicense


def map_license(gh_license: GHLicense | None, bt_license: BTLicense | None) -> dict[str, str] | None:
    """
    TODO
    """
    return {"a": "b"}  # TODO: implement license mapping logic
