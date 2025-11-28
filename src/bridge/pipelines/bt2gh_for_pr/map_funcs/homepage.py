"""
Map homepage URL from bio.tools metadata to a GitHub repository.

This module compares the homepage URL recorded in bio.tools with the homepage
(and HTML URL) of a GitHub repository, and decides whether an issue should be
opened to suggest updating the repository's homepage.
"""

from pydantic import AnyUrl

from bridge.core.biotools import UrlftpType
from bridge.logging import get_user_logger

logger = get_user_logger()


def map_homepage(gh_schema: dict[AnyUrl | str | None], bt_homepage: UrlftpType | None) -> dict[str, str] | None:
    """
    Propose a GitHub issue to add a homepage based on bio.tools metadata.

    This function examines the homepage URL from bio.tools and the existing
    homepage/HTML URL of a GitHub repository and decides whether it makes
    sense to open an issue suggesting the addition of the bio.tools homepage
    to the repository settings.

    Decision logic
    --------------
    1. If `bt_homepage` (bio.tools homepage) is missing, nothing to do.
    2. If `bt_homepage` is the same as the repository's HTML URL
       (e.g. https://github.com/org/repo), nothing to do.
    3. If the repository already has a homepage set and it differs from
       `bt_homepage`, log a conflict and do not propose an issue.
    4. If the repository has no homepage set and `bt_homepage` is present
       and different from the HTML URL, propose an issue to add it.

    Parameters
    ----------
    gh_schema : dict[AnyUrl | str | None]
        A dictionary containing existing GitHub repository data.
        Expected keys:
        - "homepage": the configured GitHub homepage URL, or None/empty if unset.
        - "html_url": the canonical GitHub repository URL.
    bt_homepage : UrlftpType | None
        The homepage URL defined in the bio.tools metadata, or None if
        no homepage is provided.

    Returns
    -------
    dict[str, str] | None
        A mapping with the issue title as key and the issue body as value,
        or ``None`` if no issue is to be created.
    """
    gt_homepage = gh_schema.get("homepage")
    gh_hp = str(gt_homepage).rstrip("/") if gt_homepage else None
    gh_url = gh_schema["html_url"]
    bt_hp = str(bt_homepage).rstrip("/") if bt_homepage else None

    if bt_hp is None:
        logger.note("bio.tools homepage is None, nothing to map.")
        return None

    if bt_hp == gh_url:
        logger.exact("bio.tools homepage is the same as GitHub URL, no need to map.")
        return None

    if gh_hp is not None:
        if gh_hp != bt_hp:
            logger.conflict(f"existing GitHub homepage '{gh_hp}' differs from bio.tools homepage '{bt_hp}'")
            return None

    logger.added(f"homepage '{bt_hp}'")
    return {
        "Add homepage from bio.tools metadata": (
            f"The bio.tools homepage is:\n\n{bt_hp}\n\n"
            "Please consider adding this homepage to the GitHub repository."
        )
    }
