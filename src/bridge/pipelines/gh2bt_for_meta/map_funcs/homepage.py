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
    gh_homepage = gh_schema.get("homepage", None)
    gh_url = gh_schema.get("html_url", None)

    if gh_homepage is not None:
        if bt_homepage is not None:
            gh_norm = canonicalize_url(str(gh_homepage))
            bt_norm = canonicalize_url(str(bt_homepage.root))

            if gh_norm == bt_norm:
                logger.exact(f"GitHub homepage '{gh_norm}' matches bio.tools homepage.")
                return bt_homepage

            logger.conflict(f"existing GitHub homepage '{gh_norm}'" f" differs from bio.tools homepage '{bt_norm}'")

        logger.added(f"homepage '{gh_homepage}' from GitHub")
        return UrlftpType(root=str(gh_homepage))

    if gh_homepage is None and bt_homepage is None:
        logger.added(f"homepage as GitHub repo url '{gh_url}'")
        return UrlftpType(root=str(gh_url))

    logger.unchanged("No GitHub homepage found, nothing to map.")
    return bt_homepage
