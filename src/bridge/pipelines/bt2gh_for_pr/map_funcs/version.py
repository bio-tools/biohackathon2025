"""
Mapping versions from bio.tools to GitHub.

This module compares bio.tools version metadata against GitHub release tags,
and, when appropriate, proposes a GitHub issue suggesting the creation of a
corresponding GitHub release.
"""

from bridge.core.biotools import VersionType
from bridge.logging import get_user_logger
from bridge.pipelines.shared.version import any_bt_newer_than_gh, find_latest_bt_version

logger = get_user_logger()


def map_version(gh_latest_version_tag: str | None, bt_versions: list[VersionType] | None) -> dict[str, str] | None:
    """
    Propose a GitHub issue to make a GitHub release based on bio.tools version metadata, if needed.

    The function checks whether the latest bio.tools version is newer than
    the latest GitHub release tag. If so, it proposes an issue to create a
    corresponding GitHub release. If GitHub has no latest release tag while
    bio.tools has versions defined, it also proposes an issue. If no action
    is needed, it returns None.

    Parameters
    ----------
    gh_latest_version_tag : str | None
        Latest GitHub release tag, or ``None`` if unavailable.
    bt_versions : list[VersionType] | None
        Existing bio.tools versions.

    Returns
    -------
    dict[str, str] | None
        A mapping with the issue title as key and the issue body as value,
        or ``None`` if no issue is to be created.
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
