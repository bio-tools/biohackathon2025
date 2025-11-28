"""
Map homepage metadata from GitHub to bio.tools.

This module reconciles homepage URLs between GitHub repository metadata and
existing bio.tools metadata. It applies a merge policy that prefers explicit
GitHub homepage configuration when available, preserves existing bio.tools
values when GitHub is silent, and falls back to the repository URL when no
homepage is defined anywhere.
"""

from pydantic import AnyUrl

from bridge.core.biotools import UrlftpType
from bridge.logging import get_user_logger
from bridge.pipelines.policies.gh2bt import reconcile_gh_over_bt
from bridge.pipelines.utils import canonicalize_url

logger = get_user_logger()


def map_homepage(gh_schema: dict[str, AnyUrl | str | None], bt_homepage: UrlftpType | None) -> UrlftpType | None:
    """
    Map and reconcile homepage metadata from GitHub and bio.tools.

    Policy:
    1. GitHub is considered the authoritative source when a homepage is present.
       If GitHub provides a homepage (`gh_schema["homepage"]`), that value is used
       as the canonical homepage.
    2. bio.tools is preserved only when GitHub provides no homepage.
       If GitHub reports no homepage (missing or ``None``), the existing bio.tools
       homepage is returned unchanged.
    3. Exact matches are treated as no-ops.
       If both GitHub and bio.tools provide a homepage and their canonicalized
       URLs are identical, the existing bio.tools value
       is returned unchanged and an exact-match log message is emitted.
    4. Conflicts are logged and resolved in favor of GitHub.
       If both GitHub and bio.tools provide a homepage but the canonicalized URLs
       differ, a conflict is logged and the GitHub homepage replaces the bio.tools
       value.
    5. The GitHub repository URL is used as a fallback.
       If neither GitHub nor bio.tools provides a homepage, the GitHub repository
       URL (`gh_schema["html_url"]`) is used as the homepage and logged as added.

    Parameters
    ----------
    gh_schema : dict[str, AnyUrl | str | None]
        GitHub repository metadata dictionary.
        Expected keys include:
        - 'homepage' : The homepage URL configured on GitHub (may be None).
        - 'html_url' : The GitHub repository URL (used as fallback).
    bt_homepage : UrlftpType | None
        Existing homepage value from bio.tools metadata, or ``None`` if none
        is defined.

    Returns
    -------
    UrlftpType | None
        The resolved homepage as a `UrlftpType` instance, or ``None`` if no
        homepage could be determined (only possible if `gh_schema` is malformed).
    """
    gh_homepage = gh_schema.get("homepage")
    gh_url = gh_schema.get("html_url")

    gh_norm = canonicalize_url(str(gh_homepage)) if gh_homepage is not None else None
    bt_norm = canonicalize_url(str(bt_homepage.root)) if bt_homepage is not None else None

    if gh_norm is None and bt_homepage is None:
        # special-case fallback: repo URL
        if gh_url is None:
            logger.unchanged("No GitHub homepage or repo url found, nothing to map.")
            return None
        logger.added(f"homepage as GitHub repo url '{gh_url}'")
        return UrlftpType(root=str(gh_url))

    if gh_norm is None:
        logger.unchanged("No GitHub homepage found, nothing to map.")
        return bt_homepage

    # reconciliation between GitHub homepage and bio.tools homepage
    return reconcile_gh_over_bt(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        bt_value=bt_homepage,
        build_bt_from_gh=lambda url: UrlftpType(root=url),
        log_label="homepage",
    )
