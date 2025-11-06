"""
Mapping functions for license metadata.
"""

import logging

logger = logging.getLogger(__name__)


def map_license(gh_license: str, bt_license: str) -> str | None:
    """
    Map GitHub license metadata to bio.tools license metadata.

    Use cases:
    - Existing GitHub license, no bio.tools license: add license to bio.tools
    - No GitHub license, existing bio.tools license: note missing GitHub license
    - No GitHub license, no bio.tools license: no action
    - Existing GitHub license and bio.tools license, exact match: no action
    - Existing GitHub license and bio.tools license, conflict: update bio.tools

    Parameters
    ----------
    gh_license : str
        Github repository license (SPDX ID).
    bt_license : str
        bio.tools record license.

    Returns
    -------
    str
        Original or updated license.
    """
    if gh_license is None:
        # if no GitHub license, return bio.tools license, which may be None
        if bt_license:
            logger.info(f"NOTE: GitHub has no license SPDX ID, but bio.tools has license '{bt_license}'")
        return bt_license

    if bt_license is None:
        # if no bio.tools license, return GitHub license
        logger.info(f"ADDED: license '{gh_license}'")
        return gh_license

    if bt_license != gh_license:
        # if both licenses exist, but they are not the same, return GitHub License
        logger.info(f"CONFLICT: overwrite existing bio.tools license '{bt_license}' with GitHub license '{gh_license}'")
        return gh_license

    # both licenses exist and are the same
    logger.info(f"EXACT MATCH: license '{bt_license}'")
    return bt_license
