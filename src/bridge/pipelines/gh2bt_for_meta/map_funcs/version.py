"""
Mapping releases for version metadata.

This module reconciles GitHub release tags with bio.tools version metadata.
It supports multiple common versioning styles (semantic versions, dates,
integers, ranges, and raw labels) and provides a safe comparison mechanism
to detect when existing bio.tools versions appear newer than the latest
GitHub release.
"""

from bridge.core.biotools import VersionType
from bridge.logging import get_user_logger
from bridge.pipelines.shared.version import any_bt_newer_than_gh

logger = get_user_logger()


def map_version(gh_latest_version_tag: str | None, bt_versions: list[VersionType] | None) -> list[VersionType] | None:
    """
    Map and reconcile GitHub release metadata and bio.tools version metadata.

    Ensures that the GitHub latest release tag is present in the bio.tools
    version list. If any existing bio.tools version appears newer than the
    GitHub latest (based on parsed version comparison), the bio.tools version
    list is reset to contain only the GitHub version.

    Policy:
    1. If GitHub provides no latest tag, existing bio.tools versions are preserved.
    2. If bio.tools has no versions, the GitHub version is adopted.
    3. If the GitHub version is already present, no change is made.
    4. If a newer bio.tools version is detected, a conflict is logged and the
       list is reset to the GitHub version only.
    5. Otherwise, the GitHub version is appended to the existing list.

    Parameters
    ----------
    gh_latest_version_tag : str | None
        Latest GitHub release tag, or ``None`` if unavailable.
    bt_versions : list[VersionType] | None
        Existing bio.tools versions.

    Returns
    -------
    list[VersionType] | None
        Updated list of bio.tools versions after reconciliation.
    """
    if not gh_latest_version_tag:
        # if no GitHub version, return bio.tools version, which may be None
        logger.unchanged("GitHub has no latest version tag, nothing to map")
        return bt_versions

    latest_version_tag_as_bt = VersionType(root=gh_latest_version_tag)

    if not bt_versions:
        # if no bio.tools version, return GitHub version as list
        logger.added(f"version '{gh_latest_version_tag}'")
        return [latest_version_tag_as_bt]

    # if GitHub version already present, nothing to do
    if any(v.root == latest_version_tag_as_bt.root for v in bt_versions):
        logger.exact(f"latest version '{gh_latest_version_tag}' already in bio.tools")
        return bt_versions

    # if any bt version appears newer than gh latest, log conflict and reset to gh only
    if any_bt_newer_than_gh(latest_version_tag_as_bt, bt_versions):
        logger.conflict(
            f"bio.tools version(s) '{bt_versions}' appear newer than GitHub latest version '{gh_latest_version_tag}'"
        )
        return [latest_version_tag_as_bt]

    # otherwise, append gh latest
    logger.added(f"version '{gh_latest_version_tag}' to existing bio.tools versions '{bt_versions}'")
    return bt_versions + [latest_version_tag_as_bt]
