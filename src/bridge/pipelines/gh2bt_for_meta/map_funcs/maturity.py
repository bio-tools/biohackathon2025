"""
Mapping functions for maturity metrics.
"""

import numpy as np

from bridge.core.biotools import Maturity
from bridge.logging import get_user_logger

logger = get_user_logger()


def _safe_metric(gh_schema: dict, key: str) -> float:
    value = gh_schema.get(key, 0)
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.note(f"Non-numeric GitHub metric {key}={value!r}, treating as 0.")
        return 0.0


def map_maturity(gh_schema: dict | None, bt_maturity: Maturity | None) -> Maturity | None:
    """
    Map GitHub maturity metrics to bio.tools maturity metadata.
    """
    gh_archived = gh_schema.get("archived")
    if gh_archived is None:
        logger.unchanged("No GitHub archived status found, nothing to map.")
        return bt_maturity

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
