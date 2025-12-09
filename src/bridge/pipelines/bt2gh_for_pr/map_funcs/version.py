"""
Mapping versions from bio.tools to GitHub.
"""

import logging

logger = logging.getLogger(__name__)


def map_version(gh_version: str | None, bt_version: list | None) -> str | None:
    """
    Map bio.tools version to GitHub version.
    """
    if not gh_version:
        logger.info("CONFLICT: GitHub version doesn't exist.")
        return None

    if not bt_version:
        return gh_version

    return gh_version
