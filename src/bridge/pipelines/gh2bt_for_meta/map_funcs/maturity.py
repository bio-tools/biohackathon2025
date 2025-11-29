"""
Mapping functions for maturity metrics.

This module derives bio.tools maturity metadata from GitHub repository
signals. GitHub archived status is treated as authoritative, while a
simple popularity-based heuristic is used to distinguish between
emerging and mature tools when the repository is active.
"""

from typing import Any

import numpy as np

from bridge.core.biotools import Maturity
from bridge.logging import get_user_logger

logger = get_user_logger()


def _safe_metric(gh_schema: dict[str, Any], key: str) -> float:
    """
    Safely extract a numeric GitHub metric from a repository schema.

    Missing, null, or non-numeric values are converted to ``0.0`` and
    logged at note level.

    Parameters
    ----------
    gh_schema : dict[str, Any]
        GitHub repository metadata dictionary.
    key : str
        Name of the metric field to extract.

    Returns
    -------
    float
        Numeric value of the metric, or ``0.0`` if unavailable or invalid.
    """
    value = gh_schema.get(key, 0)
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.note(f"Non-numeric GitHub metric {key}={value!r}, treating as 0.")
        return 0.0


def map_maturity(gh_schema: dict | None, bt_maturity: Maturity | None) -> Maturity | None:
    """
    Map GitHub repository signals to bio.tools maturity metadata.

    Policy:
    1. If the GitHub repository is archived, maturity is always set to
       ``Maturity.Legacy``, regardless of existing bio.tools values.
    2. Otherwise, a popularity score based on stars, forks,
       watchers, and subscribers is computed.
    3. Scores above a fixed threshold are classified as
       ``Maturity.Mature``; lower scores as ``Maturity.Emerging``.
    4. Existing bio.tools maturity is preserved only when it matches the
       GitHub-derived classification.
    5. Conflicting values are overwritten in favor of GitHub-derived
       maturity and logged as conflicts.

    Parameters
    ----------
    gh_schema : dict[str, Any] | None
        GitHub repository metadata dictionary, or ``None`` if unavailable.
        Expected keys include:
        - 'archived'           : Boolean indicating if the repository is archived.
        - 'stargazers_count'   : Number of stars.
        - 'forks_count'        : Number of forks.
        - 'watchers_count'     : Number of watchers.
        - 'subscribers_count'  : Number of subscribers.
    bt_maturity : Maturity | None
        Existing bio.tools maturity annotation, or ``None`` if unset.

    Returns
    -------
    Maturity | None
        The reconciled bio.tools maturity classification, or the existing
        value if no GitHub-derived maturity could be computed.
    """
    if gh_schema is None:
        logger.unchanged("No GitHub schema provided, nothing to map.")
        return bt_maturity

    gh_archived = gh_schema.get("archived", False)

    has_bt_maturity = False
    if bt_maturity is not None:
        has_bt_maturity = True

    if gh_archived:
        if has_bt_maturity and bt_maturity == Maturity.Legacy:
            logger.exact("GitHub archived status matches existing bio.tools maturity 'Legacy'.")
            return bt_maturity
        elif has_bt_maturity:
            logger.conflict("GitHub archived status conflicts with existing bio.tools maturity.")
        else:
            logger.added("Using GitHub archived status to set bio.tools maturity to 'Legacy'.")
        return Maturity.Legacy

    gh_stargazers = _safe_metric(gh_schema, "stargazers_count")
    gh_forks = _safe_metric(gh_schema, "forks_count")
    gh_watchers = _safe_metric(gh_schema, "watchers_count")
    gh_subscribers = _safe_metric(gh_schema, "subscribers_count")

    # Crude differentiation scheme based on PCA analysis
    score = np.log1p(gh_stargazers) + np.log1p(gh_forks) + np.log1p(gh_watchers) + np.log1p(gh_subscribers)

    # Separate tools into two maturity levels based on score threshold
    if score > 3:
        if has_bt_maturity and bt_maturity == Maturity.Mature:
            logger.exact("GitHub maturity score matches existing bio.tools maturity 'Mature'.")
            return bt_maturity
        elif has_bt_maturity:
            logger.conflict("GitHub maturity score conflicts with existing bio.tools maturity. Will overwrite.")
        else:
            logger.added("Using GitHub maturity score to set bio.tools maturity to 'Mature'.")
        return Maturity.Mature
    else:
        if has_bt_maturity and bt_maturity == Maturity.Emerging:
            logger.exact("GitHub maturity score matches existing bio.tools maturity 'Emerging'.")
            return bt_maturity
        elif has_bt_maturity:
            logger.conflict("GitHub maturity score conflicts with existing bio.tools maturity. Will overwrite.")
        else:
            logger.added("Using GitHub maturity score to set bio.tools maturity to 'Emerging'.")
        return Maturity.Emerging
