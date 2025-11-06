"""
Map functions for the homepage data in the from bio.tools to GitHub.
"""

import logging

from bridge.core.biotools import UrlftpType

logger = logging.getLogger(__name__)


def map_homepage(gh_schema: list[UrlftpType | None], bt_homepage: UrlftpType | None) -> dict[str, str] | None:
    """
    Map bio.tools homepage metadata to GitHub homepage metadata.


    Parameters
    ----------
    gh_schema : list[UrlftpType | None]
        The GitHub schema containing existing homepage information.
        Needs to include:
        - "homepage": The existing GitHub homepage URL.
        - "html_url": The GitHub repository URL.
    bt_homepage : UrlftpType | None
        The bio.tools homepage URL.

    Returns
    -------
    dict[str, str] | None
        A dictionary with issue title as key and issue body as value, or None if no issue is needed.
    """
    gt_homepage = gh_schema.get("homepage")
    gh_hp = str(gt_homepage).rstrip("/") if gt_homepage else None
    gh_url = gh_schema["html_url"]
    bt_hp = str(bt_homepage).rstrip("/") if bt_homepage else None

    if bt_hp is None:
        logger.info("NOTE: bio.tools homepage is None, nothing to map.")
        return None

    if bt_hp == gh_url:
        logger.info("NOTE: bio.tools homepage is the same as GitHub URL, no need to map.")
        return None

    if gh_hp is not None:
        if gh_hp != bt_hp:
            logger.info(f"CONFLICT: existing GitHub homepage '{gh_hp}' differs from bio.tools homepage '{bt_hp}'")
            return None

    logger.info(f"ADDED: homepage '{bt_hp}'")
    return {
        "Add homepage from bio.tools metadata": (
            f"The bio.tools homepage is:\n\n{bt_hp}\n\n"
            "Please consider adding this homepage to the GitHub repository."
        )
    }
