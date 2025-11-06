"""
Mapping releases for version metadata.
"""

import logging

logger = logging.getLogger(__name__)

# TODO: consider semantic versioning comparison
# TODO: multiple versions and releases
# TODO: latest release?


def map_version(gh_version: str | None, bt_version: str | None) -> str | None:
    """
    Map GitHub releases metadata to bio.tools version metadata.

    Use cases:
    - Existing GitHub version, no bio.tools version: add version to bio.tools
    - No GitHub version, existing bio.tools version: note missing GitHub version
        - create issue
        - what to do in bio.tools?
    - No GitHub version, no bio.tools version: no action
    - Existing GitHub version and bio.tools version, exact match: no action
    - Existing GitHub version and bio.tools version, conflict: update bio.tools

    Parameters
    ----------
    gh_version : str
        Github repository version (tag name).
    bt_version : str
        bio.tools record version.

    Returns
    -------
    str
        Original or updated version.
    """
    if gh_version is None:
        # if no GitHub version, return bio.tools version, which may be None
        if bt_version:
            logger.info(f"NOTE: GitHub has no version tag, but bio.tools has version '{bt_version}'")
        return bt_version

    if bt_version is None:
        # if no bio.tools version, return GitHub version
        logger.info(f"ADDED: version '{gh_version}'")
        return gh_version

    if bt_version != gh_version:
        # if both versions exist, but they are not the same, return GitHub Version
        logger.info(f"CONFLICT: overwrite existing bio.tools version '{bt_version}' with GitHub version '{gh_version}'")
        return gh_version

    # both versions exist and are the same
    logger.info(f"EXACT MATCH: version '{bt_version}'")
    return bt_version
