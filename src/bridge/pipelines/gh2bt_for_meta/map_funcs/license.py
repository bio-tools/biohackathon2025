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
from bridge.pipelines.policies.gh2bt import reconcile_gh_over_bt
from bridge.pipelines.utils import find_matching_enum_member

logger = get_user_logger()


def map_license(gh_license: str | None, bt_license: License | None) -> License | None:
    """
    Map and reconcile GitHub and bio.tools license annotations using the generic
    GitHub-over-bio.tools policy.

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
    if gh_license is None:
        # if no GitHub license, return bio.tools license, which may be None
        logger.note("GitHub has no license SPDX ID, nothing to map")
        return bt_license

    return reconcile_gh_over_bt(
        gh_norm=gh_license,
        bt_norm=bt_license,
        bt_value=bt_license,
        build_bt_from_gh=lambda gh: find_matching_enum_member(gh, License),
        log_label="license",
    )
