"""
Mapping functions for description metadata.

This module compares a repository's existing GitHub
description with the description registered in bio.tools, and, when useful,
propose a GitHub issue suggesting that the bio.tools description be adopted.
"""

from bridge.logging import get_user_logger

logger = get_user_logger()


def map_description(gh_description: str | None, bt_description: str | None) -> dict[str, str] | None:
    """
    Propose a GitHub issue to add a description based on bio.tools metadata.

    This function examines the description from a bio.tools entry and the
    current description of a GitHub repository. It decides whether it makes
    sense to open an issue suggesting that the bio.tools description be added
    to the repository.

    Decision logic
    --------------
    1. If `bt_description` (bio.tools description) is missing, nothing to do.
    2. If `bt_description` is identical to the GitHub description, nothing to do.
    3. If the repository already has a description that differs from
       `bt_description`, log a conflict and do not propose an issue.
    4. If the repository has no description set and `bt_description` is present,
       propose an issue suggesting that it be added.

    Parameters
    ----------
    gh_description : str | None
        The current description of the GitHub repository, or ``None`` if no
        description is set.
    bt_description : str | None
        The description from the corresponding bio.tools entry, or ``None`` if
        not available.

    Returns
    -------
    dict[str, str] | None
        A mapping with the issue title as key and the issue body as value,
        or ``None`` if no issue is to be created.
    """
    if bt_description is None:
        # if there is no bio.tools description, no need for the issue
        logger.note("bio.tools description is None, nothing to map.")
        return None

    if bt_description == gh_description:
        logger.exact("bio.tools description is the same as GitHub description, no need to map.")
        return None

    if gh_description is not None:
        logger.conflict("existing GitHub description differs from bio.tools description")
        return None

    logger.added(f"description: '{bt_description}'")
    return {
        "Add description from bio.tools metadata": (
            f"The bio.tools description is:\n\n{bt_description}\n\n"
            "Please consider adding this description to the GitHub repository."
        )
    }
