"""
Mapping versions from bio.tools to GitHub.
"""

from bridge.core.biotools import VersionType
from bridge.logging import get_user_logger
from bridge.pipelines.shared.version import any_bt_newer_than_gh, find_latest_bt_version

logger = get_user_logger()


def map_version(gh_latest_version_tag: str | None, bt_versions: list[VersionType] | None) -> dict[str, str] | None:
    """
    Propose a GitHub issue to make a GitHub release based on bio.tools version metadata, if needed.
    """
    if not bt_versions:
        logger.unchanged("No bio.tools version found, nothing to map.")
        return None

    bt_latest_version = find_latest_bt_version(bt_versions)
    if bt_latest_version is None:
        logger.unchanged("No comparable bio.tools version found, nothing to map.")
        return None

    if not gh_latest_version_tag:
        logger.conflict("GitHub has no latest release tag while bio.tools has versions defined.")
        return {
            "Create GitHub release": (
                f"The latest bio.tools version is '{bt_latest_version.root}'. "
                "No GitHub release is found. "
                "Please consider creating a corresponding GitHub release."
            )
        }

    latest_version_tag_as_bt = VersionType(root=gh_latest_version_tag)
    if any_bt_newer_than_gh(latest_version_tag_as_bt, bt_versions):
        logger.conflict(f"bio.tools version(s) appear newer than GitHub latest version '{gh_latest_version_tag}'")
        return {
            "Create GitHub release": (
                f"The latest bio.tools version '{bt_latest_version.root}' is newer than "
                f"the latest GitHub release '{gh_latest_version_tag}'. "
                "Please consider creating a corresponding GitHub release."
            )
        }

    logger.exact("GitHub latest release is up to date with bio.tools versions.")
    return None
