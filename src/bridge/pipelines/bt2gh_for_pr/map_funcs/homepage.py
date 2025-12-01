"""
Map homepage URL from bio.tools to a GitHub.

This module compares the homepage URL recorded in bio.tools with the
homepage (and HTML URL) of a GitHub repository and, when appropriate,
proposes a GitHub issue suggesting that the bio.tools homepage be added
to the repository settings. It applies a bio.tools-over-GitHub policy.
"""

from pydantic import AnyUrl

from bridge.core.biotools import UrlftpType
from bridge.logging import get_user_logger
from bridge.pipelines.policies.bt2gh import reconcile_bt_over_gh
from bridge.pipelines.utils import canonicalize_url

logger = get_user_logger()


async def map_homepage(gh_schema: dict[AnyUrl | str | None], bt_homepage: UrlftpType | None) -> dict[str, str] | None:
    """
    Propose a GitHub issue to add a homepage based on bio.tools metadata,
    using the generic bio.tools-over-GitHub issue policy.

    All URLs (GitHub homepage, GitHub HTML URL, and bio.tools homepage)
    are compared in canonicalized form to avoid spurious differences due
    to trailing slashes, case, or query parameter ordering.
    If the bio.tools homepage is equal to the repository HTML URL,
    no suggestion is made. If GitHub already has a different homepage configured,
    that value is treated as authoritative and a conflict is logged while still proposing an issue.
    When the bio.tools homepage is present, differs from the HTML URL,
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
    gh_homepage_raw = gh_schema.get("homepage")
    gh_url_raw = gh_schema.get("html_url")
    bt_homepage_raw = str(bt_homepage.root) if bt_homepage is not None else None

    gh_hp_norm = canonicalize_url(str(gh_homepage_raw)) if gh_homepage_raw else None
    gh_url_norm = canonicalize_url(str(gh_url_raw)) if gh_url_raw else None
    bt_hp_norm = canonicalize_url(bt_homepage_raw) if bt_homepage_raw else None

    if bt_hp_norm is not None and gh_url_norm is not None and bt_hp_norm == gh_url_norm:
        logger.exact("bio.tools homepage is the same as GitHub repository URL, no need to map.")
        return None

    def make_issue(homepage_norm: str) -> dict[str, str]:
        # Use the normalized value for the suggestion; if you prefer the raw value,
        # you can pass `bt_homepage_raw` instead.
        return {
            "Add homepage from bio.tools metadata": (
                f"The bio.tools homepage is:\n\n{homepage_norm}\n\n"
                "Please consider adding this homepage to the GitHub repository."
            )
        }

    return await reconcile_bt_over_gh(
        gh_norm=gh_hp_norm,
        bt_norm=bt_hp_norm,
        make_output=make_issue,
        log_label="homepage",
    )
