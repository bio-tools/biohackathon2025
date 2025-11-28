"""
Map license metadata from GitHub to bio.tools.

This module reconciles license information between GitHub repository metadata
and existing bio.tools metadata. It compares the license reported by GitHub
with the license recorded in bio.tools, and
applies a policy that prefers recognized GitHub licenses while preserving
bio.tools values when GitHub is silent or ambiguous.
"""

from bridge.core.biotools import License
from bridge.logging import get_user_logger
from bridge.pipelines.utils import find_matching_enum_member

logger = get_user_logger()


def map_license(gh_license: str | None, bt_license: License | None) -> License | None:
    """
    Map and reconcile license metadata from GitHub and bio.tools.

    This function aligns the GitHub license (SPDX ID) for a repository with
    the license annotation in bio.tools, using the `License` enum as the
    canonical representation.

    Policy:
    1. GitHub is considered authoritative when it exposes a recognized license.
       If `gh_license` is provided and can be resolved to a `License` enum
       member, that value is used as the canonical license.
    2. bio.tools is preserved when GitHub is silent or unrecognized.
       If GitHub provides no license (`gh_license is None`) or the value cannot
       be matched to the `License` enum, the existing bio.tools license
       (`bt_license`) is returned unchanged.
    3. Exact matches are treated as no-ops.
       If both GitHub and bio.tools provide a license and they resolve to the
       same `License` enum member, the existing bio.tools value is returned
       unchanged and an exact-match log message is emitted.
    4. Conflicts are logged and resolved in favor of GitHub.
       If both GitHub and bio.tools provide licenses but they resolve to
       different `License` enum members, a conflict is logged and the
       GitHub-derived license replaces the bio.tools value.

    Parameters
    ----------
    gh_license : str | None
        Github repository license (SPDX ID), or ``None`` if no license is configured.
    bt_license : License | None
        Existing bio.tools license annotation, or ``None`` if no license
        is currently recorded.

    Returns
    -------
    License | None
        The reconciled license as a `License` enum member, or ``None`` if
        neither GitHub nor bio.tools provides a usable license.
    """
    gh_matched_license = find_matching_enum_member(gh_license, License) if gh_license else None

    if gh_license is None:
        # if no GitHub license, return bio.tools license, which may be None
        logger.note("GitHub has no license SPDX ID, nothing to map")
        return bt_license

    if gh_matched_license is None:
        # if GitHub license is not recognized, return bio.tools license, which may be None
        logger.note(f"GitHub license '{gh_license}' not recognized in bio.tools License enum, nothing to map")
        return bt_license

    if bt_license is None:
        # if no bio.tools license, return GitHub license
        logger.added(f"license '{gh_license}'")
        return gh_matched_license

    if bt_license != gh_matched_license:
        # if both licenses exist, but they are not the same, return GitHub License
        logger.conflict(f"Overwrite existing bio.tools license '{bt_license}' with GitHub license '{gh_license}'")
        return gh_matched_license

    # both licenses exist and are the same
    logger.exact(f"license '{bt_license}'")
    return bt_license
