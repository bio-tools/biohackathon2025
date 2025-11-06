"""
Mapping functions for homepage metadata.
"""

from pydantic import AnyUrl

from bridge.core.biotools import UrlftpType


def map_homepage(gh_homepage: AnyUrl | None, bt_homepage: UrlftpType | None) -> UrlftpType | None:
    """
    Map GitHub homepage metadata to bio.tools homepage metadata.
    """
    if gh_homepage is None:
        # if there is no GitHub homepage, return the existing bio.tools homepage (which may also be None)
        return bt_homepage

    if bt_homepage is None:
        # if there is no existing bio.tools homepage, use the GitHub homepage
        return UrlftpType(str(gh_homepage))

    # if both exist, check that they are the same
    if str(gh_homepage).rstrip("/") != str(bt_homepage.root).rstrip("/"):
        raise ValueError(f"Conflict between GitHub homepage '{gh_homepage}' and bio.tools homepage '{bt_homepage}'")

    return bt_homepage
