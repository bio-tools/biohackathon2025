"""
Generic reconciliation policies for bio.tools-to-GitHub *additive* mappings.

This module provides a generic function to determine whether a GitHub issue
or pull request should be proposed based on bio.tools metadata, according to a
policy that treats bio.tools values as additions on top of existing GitHub values.
"""

from collections.abc import Callable
from typing import TypeVar

from bridge.logging import get_user_logger

logger = get_user_logger()

BTN = TypeVar("BTN")  # element type for bio.tools set
GHN = TypeVar("GHN")  # element type for GitHub set (usually same as BTN)
OUTPUT = TypeVar("OUTPUT")  # issue/pr payload type, e.g. dict[str, str]


def reconcile_bt_ontop_gh(
    *,
    gh_norm: set[GHN] | None,
    bt_norm: set[BTN] | None,
    make_output: Callable[[set[BTN]], OUTPUT],
    log_label: str,
) -> OUTPUT | None:
    """
    Apply a generic bio.tools-on-top-of-GitHub policy for additive metadata.

    This function is intended for *multi-valued* fields where bio.tools can
    contribute additional values without replacing existing GitHub ones
    (e.g. topics, labels, EDAM terms). Both GitHub and bio.tools values are
    provided as sets and the function computes the subset of bio.tools values
    that are missing from GitHub.

    Policy:
    1. If ``bt_norm`` is ``None`` or empty, bio.tools is treated as silent and
       no issue/pr is proposed. An "unchanged" log entry is emitted.
    2. If ``gh_norm`` is ``None`` or empty, all values from ``bt_norm`` are
       considered missing and an issue/pr is proposed with an "added" log entry.
    3. If both ``gh_norm`` and ``bt_norm`` are non-empty:
       - If all values in ``bt_norm`` are already present in ``gh_norm``,
         no issue/pr is proposed and an "exact" log entry is emitted.
       - Otherwise, the set difference ``missing = bt_norm - gh_norm`` is
         passed to ``make_output`` and an "added" log entry is emitted.

    Parameters
    ----------
    gh_norm : set[GHN] | None
        Normalized set of values currently present on GitHub, or ``None``
        if no values are recorded.
    bt_norm : set[BTN] | None
        Normalized set of values from bio.tools, or ``None`` if bio.tools
        does not provide values for this field.
    make_output : Callable[[set[BTN]], OUTPUT]
        Callable that constructs an issue/pr payload from the set of missing
        bio.tools values.
    log_label : str
        Short label used in log messages to identify the metadata field
        (e.g., ``"topics"``, ``"edam terms"``).

    Returns
    -------
    ISSUE | None
        Issue payload to propose according to the policy, or ``None`` if
        no issue should be created.
    """
    if not bt_norm:
        logger.unchanged(f"No bio.tools {log_label} found, nothing to map.")
        return None

    if not gh_norm:
        logger.added(f"bio.tools {log_label} additions: {bt_norm!r}")
        return make_output(bt_norm)

    missing = bt_norm - gh_norm  # set difference

    if not missing:
        logger.exact(f"All bio.tools {log_label} are already present on GitHub.")
        return None

    logger.added(f"bio.tools {log_label} additions missing on GitHub: {missing!r}")
    return make_output(missing)
