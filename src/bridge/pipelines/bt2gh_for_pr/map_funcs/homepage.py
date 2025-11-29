"""
Map homepage URL from bio.tools to a GitHub.

This module compares the homepage URL recorded in bio.tools with the
homepage (and HTML URL) of a GitHub repository and, when appropriate,
proposes a GitHub issue suggesting that the bio.tools homepage be added
to the repository settings. It applies a bio.tools-over-GitHub policy:
bio.tools is only used to suggest a homepage when GitHub has no
conflicting homepage configured.
"""

from pydantic import AnyUrl

from bridge.core.biotools import UrlftpType
from bridge.logging import get_user_logger
from bridge.pipelines.policies import reconcile_bt_over_gh_issue

logger = get_user_logger()


def map_homepage(gh_schema: dict[AnyUrl | str | None], bt_homepage: UrlftpType | None) -> dict[str, str] | None:
    """
    Propose a GitHub issue to add a homepage based on bio.tools metadata,
    using the generic bio.tools-over-GitHub issue policy.

    The GitHub homepage and bio.tools homepage are normalized by stripping
    trailing slashes before comparison. If the bio.tools homepage is equal
    to the repository HTML URL, no suggestion is made. If GitHub already
    has a different homepage configured, that value is treated as
    authoritative and a conflict is logged without proposing an issue.
    Only when the bio.tools homepage is present, differs from the HTML URL,
    and the GitHub homepage is unset does this function propose an issue.

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
    gh_url = str(gh_schema["html_url"]).rstrip("/")
    bt_hp = str(bt_homepage).rstrip("/") if bt_homepage else None

    if bt_hp is not None and bt_hp == gh_url:
        logger.exact("bio.tools homepage is the same as GitHub URL, no need to map.")
        return None

    def make_issue(homepage: str) -> dict[str, str]:
        return {
            "Add homepage from bio.tools metadata": (
                f"The bio.tools homepage is:\n\n{homepage}\n\n"
                "Please consider adding this homepage to the GitHub repository."
            )
        }

    return reconcile_bt_over_gh_issue(
        gh_norm=gh_hp,
        bt_norm=bt_hp,
        make_issue=make_issue,
        log_label="homepage",
    )
