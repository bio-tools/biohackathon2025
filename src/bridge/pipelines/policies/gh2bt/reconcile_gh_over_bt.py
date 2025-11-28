"""
Generic reconciliation policy for GitHub-over-bio.tools mapping.

This module provides a generic function to reconcile metadata between
GitHub and bio.tools according to a defined policy that prioritizes GitHub
values while preserving bio.tools values when GitHub is silent.
"""

from collections.abc import Callable
from typing import TypeVar

from bridge.logging import get_user_logger

logger = get_user_logger()

BT = TypeVar("BT")  # bio.tools type
GHN = TypeVar("GHN")  # normalized GitHub representation
BTN = TypeVar("BTN")  # normalized bio.tools representation


def reconcile_gh_over_bt(
    *,
    gh_norm: GHN | None,
    bt_norm: BTN | None,
    bt_value: BT | None,
    build_bt_from_gh: Callable[[GHN], BT],
    log_label: str,
) -> BT | None:
    """
    Implement generic reconciliation policy function for GitHub-over-bio.tools mapping.

    - If gh_norm is None: keep bt_value.
    - If bt_norm is None: take GitHub (build_bt_from_gh).
    - If gh_norm == bt_norm: log exact, keep bt_value.
    - Else: log conflict, take GitHub.
    """
    if gh_norm is None:
        logger.unchanged(f"No GitHub {log_label} found, nothing to map.")
        return bt_value

    if bt_norm is None:
        logger.added(f"{log_label} from GitHub: {gh_norm!r}")
        return build_bt_from_gh(gh_norm)

    if gh_norm == bt_norm:
        logger.exact(f"GitHub {log_label} matches bio.tools {log_label}.")
        return bt_value

    logger.conflict(f"Existing GitHub {log_label} {gh_norm!r} differs from bio.tools {log_label} {bt_norm!r}")
    return build_bt_from_gh(gh_norm)
