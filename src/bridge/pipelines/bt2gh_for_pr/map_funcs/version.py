"""
Mapping versions from bio.tools to GitHub.
"""

from bridge.core.biotools import VersionType
from bridge.logging import get_user_logger

logger = get_user_logger()


def map_version(gh_version: str | None, bt_version: list[VersionType] | None) -> dict[str, str] | None:
    """
    Map bio.tools version to GitHub version.
    """
    if not gh_version:
        logger.unchanged("No GitHub version found, nothing to map.")
        return None

    # if not bt_version:
    #     return gh_version
    return {}
