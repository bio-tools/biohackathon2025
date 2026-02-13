"""
Generic reconciliation policy for GitHub-to-bio.tools *additive* mappings.

This module provides a generic function to reconcile metadata between
GitHub and bio.tools according to a defined policy that adds GitHub values
on top of existing bio.tools values without removing any.
"""

from collections.abc import Callable
from typing import TypeVar

from bridge.logging import get_user_logger

logger = get_user_logger()


BT = TypeVar("BT")  # bio.tools type
GHN = TypeVar("GHN")  # element type for GitHub set (usually same as BTN)
BTN = TypeVar("BTN")  # element type for bio.tools set


def reconcile_gh_ontop_bt(
    *,
    gh_norm: GHN | None,
    bt_norm: set[BTN] | None,
    bt_value: BT | None,
    build_bt_from_gh: Callable[[GHN], set[BTN] | None] | None,
    build_bt_from_norm: Callable[[set[BTN]], BT],
    log_label: str,
) -> BT | None:
    """
    Apply a generic GitHub-on-top-of-bio.tools policy for additive metadata.

    This function is intended for *multi-valued* fields where GitHub can
    contribute additional values on top of existing bio.tools ones (e.g. functions).
    Both GitHub and bio.tools values are provided as sets and the function computes
    the subset of GitHub values that are missing from bio.tools.

    Policy:
    1. If ``gh_norm`` is ``None`` or empty,
        GitHub is treated as silent and no change is made to bio.tools.
        An "unchanged" log entry is emitted.
    2. If ``gh_norm`` contains values, each value is mapped to zero or more
        bio.tools values via ``build_bt_from_gh``.
    3. If ``bt_norm`` is ``None`` or empty, all bio.tools values derived from GitHub are added to bio.tools.
        An "added" log entry is emitted.
    4. If both ``gh_norm`` and ``bt_norm`` contain values,
        the union of the existing bio.tools values and the new values derived from GitHub is computed.
    5. If the union is the same as the existing bio.tools values, no change is made.
        An "exact" log entry is emitted.
    6. If the union contains additional values compared to the existing bio.tools values,
        the new values are added to bio.tools and an "added" log entry is emitted indicating the number of new values.

    Parameters
    ----------
    gh_norm : set[GHN] | None
        A set of normalized values derived from GitHub, or ``None`` if GitHub provides no usable value.
    bt_norm : set[BTN] | None
        A set of normalized values derived from the existing bio.tools metadata, or ``None`` if no value is recorded.
    bt_value : BT | None
        The existing bio.tools value corresponding to the field being reconciled, or ``None`` if no value is recorded.
        This is preserved when GitHub is silent or when the normalized sets are equal.
    build_bt_from_gh : Callable[[GHN], set[BTN] | None]
        A callable that takes a normalized GitHub value and returns
        a set of normalized bio.tools values derived from it,
        or ``None`` if the GitHub value cannot be mapped to bio.tools.
    build_bt_from_norm : Callable[[set[BTN]], BT]
        A callable that takes a set of normalized bio.tools values and constructs
        the corresponding concrete bio.tools value.
    log_label : str
        A short label used in log messages to identify the reconciled field (e.g., "function", "topic", etc.).

    Returns
    -------
    BT | None
        The reconciled bio.tools value, which may be the same as the existing value
        if GitHub is silent or if the normalized sets are equal, or a new value with GitHub-derived additions.
    """
    if not gh_norm:
        logger.unchanged(f"No GitHub {log_label} found, nothing to map.")
        return bt_value

    if build_bt_from_gh is None:
        gh_norm_from_bt = gh_norm
    else:
        gh_norm_from_bt = build_bt_from_gh(gh_norm)

    if not gh_norm_from_bt:
        logger.unchanged(f"GitHub {log_label} could not be cast as bio.tools, nothing to map.")
        return bt_value

    if not bt_norm:
        logger.added(f"{log_label} from GitHub: {gh_norm!r}")
        return build_bt_from_norm(gh_norm_from_bt)

    updated_bt_norm = bt_norm.union(gh_norm_from_bt)
    nr_added = len(updated_bt_norm) - len(bt_norm)
    if nr_added == 0:
        logger.exact(f"GitHub {log_label} already present in bio.tools, nothing to add.")
        return bt_value

    logger.added(f"Added {nr_added} missing {log_label} from GitHub to bio.tools.")
    return build_bt_from_norm(updated_bt_norm)
