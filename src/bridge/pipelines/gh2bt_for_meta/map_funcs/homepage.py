"""
Mapping functions for homepage metadata.
"""

from bridge.core.biotools import UrlftpType


def map_homepage(gh_schema: list[UrlftpType | None], bt_homepage: UrlftpType | None) -> UrlftpType | None:
    """
    Map GitHub homepage metadata to bio.tools homepage metadata.
    """
    gh_homepage = gh_schema["homepage"]
    gh_url = gh_schema["html_url"]
    # if both exist, check that they are the same
    if gh_homepage is not None and bt_homepage is not None:
        if str(gh_homepage).rstrip("/") != str(bt_homepage.root).rstrip("/"):
            print(3)
            raise ValueError(f"Conflict between GitHub homepage '{gh_homepage}' and bio.tools homepage '{bt_homepage}'")
        return bt_homepage

    if gh_homepage is not None:
        # if there is a GitHub homepage, return it
        print(1)
        print(gh_homepage)
        return str(gh_homepage)

    if bt_homepage is not None:
        # if there is an existing bio.tools homepage, return it
        print(2)
        print(bt_homepage)
        return str(bt_homepage)
    print(3)
    return str(gh_url)
