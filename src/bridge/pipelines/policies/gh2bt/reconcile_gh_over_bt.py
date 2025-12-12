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
    Apply a generic GitHub-over-bio.tools reconciliation policy.

    This function operates on *normalized* representations of GitHub and
    bio.tools values (``gh_norm`` and ``bt_norm``), while returning and
    constructing concrete bio.tools values (``bt_value`` and the output).

    Policy:
    1. If ``gh_norm`` is ``None``, GitHub is treated as silent and the existing
       bio.tools value (``bt_value``) is preserved. An "unchanged" log entry is
       emitted.
    2. If ``gh_norm`` is not ``None`` and ``bt_norm`` is ``None``, GitHub is
       treated as the only source. A new bio.tools value is constructed via
       ``build_bt_from_gh(gh_norm)`` and an "added" log entry is emitted.
    3. If both ``gh_norm`` and ``bt_norm`` are not ``None`` and they compare
       equal (``gh_norm == bt_norm``), the existing bio.tools value
       (``bt_value``) is preserved and an exact-match log entry is emitted.
    4. If both ``gh_norm`` and ``bt_norm`` are not ``None`` and differ, the
       GitHub value is treated as authoritative. A new bio.tools value is
       constructed via ``build_bt_from_gh(gh_norm)`` and a conflict log entry
       is emitted.

    Parameters
    ----------
    gh_norm : GHN | None
        Normalized representation of the GitHub value (e.g., canonicalized URL,
        lowercased language set, enum, etc.), or ``None`` if GitHub provides no
        usable value.
    bt_norm : BTN | None
        Normalized representation of the existing bio.tools value, or ``None``
        if no value is recorded.
    bt_value : BT | None
        The current bio.tools value to be preserved when GitHub is silent or
        when the normalized values match.
    build_bt_from_gh : Callable[[GHN], BT]
        Callable that constructs a concrete bio.tools value from the normalized
        GitHub representation.
    log_label : str
        Short label used in log messages to identify the reconciled field
        (e.g., ``"license"``, ``"languages"``, ``"homepage"``).

    Returns
    -------
    BT | None
        The reconciled bio.tools value according to the policy, or ``None`` if
        both sources effectively provide no usable value.
    """
    if gh_norm is None:
        logger.unchanged(f"No GitHub {log_label} found, nothing to map.")
        return bt_value

    gh_from_bt = build_bt_from_gh(gh_norm)

    if gh_from_bt is None:
        logger.unchanged(f"GitHub {log_label} could not be cast as bio.tools, nothing to map.")
        return bt_value

    if bt_norm is None:
        logger.added(f"{log_label} from GitHub: {gh_norm!r}")
        return gh_from_bt

    if gh_from_bt == bt_norm:
        logger.exact(f"GitHub {log_label} matches bio.tools {log_label}.")
        return bt_value

    logger.conflict(f"Existing GitHub {log_label} {gh_norm!r} differs from bio.tools {log_label} {bt_norm!r}")
    return gh_from_bt
