"""
Map bio.tools metadata to GitHub README, add badges.
"""

from typing import Any


def map_readme(gh_readme: str | None, bt_params: dict[str, Any]) -> dict[str, str]:
    """
    Docstring for map_readme
    """
    if gh_readme is None:
        pass  # TODO: generate a default README
    return {"readme": gh_readme}
