"""
Map description metadata from bio.tools to GitHub.

This module compares the description recorded in bio.tools with the
description configured on a GitHub repository and, when appropriate,
proposes a GitHub issue suggesting that the bio.tools description be
adopted. It applies a bio.tools-over-GitHub policy that only suggests
changes when bio.tools provides a description and the repository has
no conflicting description set.
"""

from bridge.logging import get_user_logger
from bridge.pipelines.policies.bt2gh import reconcile_bt_over_gh
from bridge.pipelines.utils import normalize_text

logger = get_user_logger()


async def map_description(gh_description: str | None, bt_description: str | None) -> dict[str, str] | None:
    """
    Propose a GitHub issue to add a description based on bio.tools metadata,
    using the generic bio.tools-over-GitHub issue policy.

    Both the GitHub and bio.tools descriptions are normalized (HTML/whitespace
    cleanup) before comparison. A suggestion is only made when bio.tools
    provides a description and the GitHub repository has no description set;
    existing, differing GitHub descriptions are treated as authoritative and
    result in a logged conflict but no proposed issue.

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
        or ``None`` if no issue is to be created under the policy.
    """
    gh_norm = normalize_text(gh_description)
    bt_norm = normalize_text(bt_description)

    def make_issue(desc: str) -> dict[str, str]:
        return {
            "Add description from bio.tools metadata": (
                f"The bio.tools description is:\n\n{desc}\n\n"
                "Please consider adding this description to the GitHub repository."
            )
        }

    return await reconcile_bt_over_gh(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        make_output=make_issue,
        log_label="description",
    )
