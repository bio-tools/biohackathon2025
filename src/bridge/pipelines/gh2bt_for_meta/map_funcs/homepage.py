"""
Mapping functions for homepage metadata.
"""

from pydantic import AnyUrl

from bridge.core.biotools import UrlftpType
from bridge.logging import get_user_logger

logger = get_user_logger()


def map_homepage(gh_schema: dict[str, AnyUrl | str | None], bt_homepage: UrlftpType | None) -> UrlftpType | None:
    """
    Map GitHub homepage metadata to bio.tools homepage metadata.
    """
    gh_homepage = gh_schema["homepage"]
    gh_url = gh_schema["html_url"]
    # if both exist, check that they are the same
    if gh_homepage is not None and bt_homepage is not None:
        if str(gh_homepage).rstrip("/") != str(bt_homepage.root).rstrip("/"):
            logger.conflict(
                f"existing GitHub homepage '{gh_homepage}'" f" differs from bio.tools homepage '{bt_homepage.root}'"
            )
        return bt_homepage

    if gh_homepage is not None:
        # if there is a GitHub homepage, return it
        logger.added(f"homepage '{gh_homepage}'")
        return UrlftpType(root=str(gh_homepage))

    if bt_homepage is not None:
        # if there is an existing bio.tools homepage, return it
        logger.unchanged(f"homepage '{bt_homepage.root}'")
        return bt_homepage

    logger.added(f"homepage as GitHub repo url '{gh_url}'")
    return UrlftpType(root=str(gh_url))
