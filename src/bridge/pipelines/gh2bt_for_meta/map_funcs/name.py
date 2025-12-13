"""
Mapping name from GitHub to bio.tools.

This module reconciles the GitHub repository name with the bio.tools name.
It compares the two names and applies a policy that prefers the GitHub name
while preserving the bio.tools name when GitHub is silent or ambiguous.
"""

from bridge.logging import get_user_logger
from bridge.pipelines.policies.gh2bt import reconcile_gh_over_bt
from bridge.pipelines.utils import normalize_text

logger = get_user_logger()


def map_name(gh_name: str | None, bt_name: str | None) -> str | None:
    """
    Map and reconcile GitHub and bio.tools names using the generic
    GitHub-over-bio.tools policy.

    Parameters
    ----------
    gh_name : str | None
        GitHub repository name.
    bt_name : str | None
        Existing bio.tools name.

    Returns
    -------
    str | None
        Mapped bio.tools name.
    """
    if gh_name is None:
        logger.unchanged("No GitHub name found, nothing to map.")
        return bt_name

    gh_norm = normalize_text(gh_name)
    bt_norm = normalize_text(bt_name)

    return reconcile_gh_over_bt(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        bt_value=bt_name,
        build_bt_from_gh=lambda name: name,
        log_label="name",
    )
