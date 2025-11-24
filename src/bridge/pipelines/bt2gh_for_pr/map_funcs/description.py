"""
Mapping functions for description metadata.
"""

# TODO: add logging


def map_description(gh_description: str | None, bt_description: str | None) -> dict[str, str] | None:
    """
    Map bio.tools description metadata to GitHub description metadata.

    Returns
    -------
    dict[str, str] | None
        A dictionary with issue title as key and issue body as value, or None if no issue is needed.
    """
    if bt_description is None:
        # if there is no bio.tools description, no need for the issue
        return None

    if gh_description is not None:
        # if there is already a GitHub description, no need for the issue
        return None

    return {
        "Add description from bio.tools metadata": (
            f"The bio.tools description is:\n\n{bt_description}\n\n"
            "Please consider adding this description to the GitHub repository."
        )
    }
