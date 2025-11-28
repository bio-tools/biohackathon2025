"""
Mapping functions for description metadata.
"""

# TODO: add logging


def map_description(gh_description: str | None, bt_description: str | None) -> dict[str, str] | None:
    """
    Suggest a GitHub issue when a bio.tools description exists but the repository lacks one.

    Behaviour:
    - If bio.tools does **not** provide a description, no issue is suggested.
    - If the GitHub repository already has a description, no issue is suggested.
    - Only when bio.tools has a description **and** GitHub does not, an
      issue is proposed, with a fixed title and a body that embeds the
      bio.tools description and politely asks maintainers to add it.

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
