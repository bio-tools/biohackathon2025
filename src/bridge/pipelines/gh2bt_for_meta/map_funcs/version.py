"""
Mapping releases for version metadata.
"""

from bridge.core.biotools import VersionType
from bridge.logging import get_user_logger

logger = get_user_logger()


def map_version(gh_latest_version_tag: str | None, bt_versions: list[VersionType] | None) -> list[VersionType] | None:
    """
    Map GitHub releases smetadata to bio.tools version metadata.
    """
    latest_version_tag_as_bt = [VersionType(root=gh_latest_version_tag)]

    if not gh_latest_version_tag:
        # if no GitHub version, return bio.tools version, which may be None
        logger.conflict("GitHub has no latest version tag, nothing to map")
        return bt_versions

    if not bt_versions:
        # if no bio.tools version, return GitHub version as list
        logger.added(f"version '{gh_latest_version_tag}'")
        return latest_version_tag_as_bt

    if gh_latest_version_tag not in bt_versions:
        if any(bt > gh_latest_version_tag for bt in bt_versions):
            # if any version in bt_version is newer than gh_version, consider conflict
            logger.conflict(
                f"bio.tools version(s) '{bt_versions}' is/are newer than"
                f" GitHub latest version '{gh_latest_version_tag}'"
            )
            return latest_version_tag_as_bt
        # if both versions exist, but GitHub version not in bio.tools, add it
        logger.added(f"version '{gh_latest_version_tag}' to existing bio.tools versions '{bt_versions}'")
        return bt_versions + latest_version_tag_as_bt

    logger.exact(f"latest version '{bt_versions}' already in bio.tools")
    return bt_versions
