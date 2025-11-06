"""
Mapping releases for version metadata.
"""

import logging

logger = logging.getLogger(__name__)


def map_version(gh_version: str | None, bt_version: list | None) -> str | None:
    """
    Map GitHub releases smetadata to bio.tools version metadata.
    """
    if not gh_version:
        # if no GitHub version, return bio.tools version, which may be None
        if bt_version:
            logger.info(f"CONFLICT: GitHub has no version tag, but bio.tools has version '{bt_version}'")
        return None

    if not bt_version:
        # if no bio.tools version, return GitHub version as list
        logger.info(f"ADDED: version '{gh_version}'")
        return [gh_version]

    if gh_version not in bt_version:
        # TODO: consider ordering
        if any(bt > gh_version for bt in bt_version):
            # if any version in bt_version is newer than gh_version, consider conflict
            logger.warning(
                f"CONFLICT: bio.tools version(s) '{bt_version}' is/are newer than GitHub latest version '{gh_version}'"
            )
            return [gh_version]
        # if both versions exist, but GitHub version not in bio.tools, add it
        logger.info(f"ADDED: version '{gh_version}' to existing bio.tools versions '{bt_version}'")
        return bt_version + [gh_version]

    logger.info(f"MATCH: latest version '{bt_version}' already in bio.tools")
    return bt_version
