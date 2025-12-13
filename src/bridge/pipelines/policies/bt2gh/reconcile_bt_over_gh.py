"""
Generic reconciliation policies for bio.tools to GitHub mapping.

This module provides a generic function to determine whether a GitHub issue
or pull request should be proposed based on bio.tools metadata, according to
a policy that treats bio.tools as authoritative while preserving existing GitHub
values when bio.tools is silent.
"""

from collections.abc import Awaitable, Callable
from typing import TypeVar

from bridge.logging import get_user_logger
from bridge.utils import maybe_await

logger = get_user_logger()

BTN = TypeVar("BTN")  # normalized bio.tools representation
GHN = TypeVar("GHN")  # normalized GitHub representation
OUTPUT = TypeVar("OUTPUT")  # issue payload type, e.g. dict[str, str]


async def reconcile_bt_over_gh(
    *,
    gh_norm: GHN | None,
    bt_norm: BTN | None,
    make_output: Callable[[BTN], Awaitable[OUTPUT] | OUTPUT],
    log_label: str,
    equality_fn: Callable[[GHN, BTN], bool] | None = None,
) -> OUTPUT | None:
    """
    Apply a generic bio.tools-over-GitHub policy to decide whether to
    propose a GitHub issue or pull request based on bio.tools metadata.

    This function operates on *normalized* representations of GitHub and
    bio.tools values (``gh_norm`` and ``bt_norm``) and returns an issue/pr
    payload constructed from the bio.tools value when applicable.

    Policy:
    1. If ``bt_norm`` is ``None``, bio.tools is treated as silent and no
       issue/pr is proposed. An "unchanged" log entry is emitted.
    2. If ``gh_norm`` is not ``None`` and equals ``bt_norm``, the values
       are considered aligned and no issue/pr is proposed.
       An "exact" log entry is emitted.
    3. If ``gh_norm`` is not ``None`` and differs from ``bt_norm``, GitHub
       is treated as conflicting with bio.tools. A conflict log entry is
       emitted and an issue/pr proposing the bio.tools value is constructed
       via ``make_output(bt_norm)``.
    4. If ``gh_norm`` is ``None`` and ``bt_norm`` is not ``None``, GitHub
       is missing the value and an issue/pr proposing the bio.tools value is
       constructed via ``make_output(bt_norm)`` with an added log entry.

    Parameters
    ----------
    gh_norm : GHN | None
        Normalized representation of the GitHub value, or ``None`` if no
        usable value is available from GitHub.
    bt_norm : BTN | None
        Normalized representation of the bio.tools value, or ``None`` if
        no value is recorded in bio.tools.
    make_output : Callable[[BTN], Awaitable[OUTPUT] | OUTPUT]
        Callable that constructs an issue/pr payload from the normalized
        bio.tools value. The callable may be asynchronous.
    log_label : str
        Short label used in log messages to identify the metadata field
        (e.g., ``"description"``, ``"homepage"``, ``"license"``).
    equality_fn : Callable[[GHN, BTN], bool] | None, optional
        Optional equality function to compare normalized GitHub and
        bio.tools values. If ``None``, the default equality operator
        (``==``) is used.

    Returns
    -------
    OUTPUT | None
        Issue/pr payload to propose according to the policy, or ``None`` if
        no issue should be created.
    """
    if bt_norm is None:
        logger.unchanged(f"No bio.tools {log_label} found, nothing to map.")
        return None

    if gh_norm is not None:
        if equality_fn is not None:
            equal = equality_fn(gh_norm, bt_norm)
        else:
            equal = gh_norm == bt_norm

        if equal:
            logger.exact(f"bio.tools {log_label} matches GitHub {log_label}, no need to map.")
            return None

        logger.conflict(f"existing GitHub {log_label} {gh_norm!r} differs from bio.tools {log_label} {bt_norm!r}")
        return await maybe_await(make_output, bt_norm)

    logger.added(f"{log_label}: {bt_norm!r}")
    return await maybe_await(make_output, bt_norm)
