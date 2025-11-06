"""
Mapping functions for maturity metrics.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def map_maturity(gh_schema: dict | None, bt_maturity: str | None) -> str | None:
    """
    Map GitHub maturity metrics to bio.tools maturity metadata.
    """
    gh_archived = gh_schema["archived"]

    has_bt_maturity = False
    if bt_maturity is not None:
        has_bt_maturity = True

    if gh_archived:
        if has_bt_maturity and bt_maturity == "Legacy":
            logging.info("EXACT MATCH: GitHub archived status matches existing bio.tools maturity 'legacy'.")
            return bt_maturity
        elif has_bt_maturity:
            logging.info("CONFLICT: GitHub archived status conflicts with existing bio.tools maturity.")
        else:
            logging.info("ADDED: Using GitHub archived status to set bio.tools maturity to 'legacy'.")
        return "Legacy"

    gh_stargazers = gh_schema["stargazers_count"]
    gh_forks = gh_schema["forks_count"]
    gh_watchers = gh_schema["watchers_count"]
    gh_subscribers = gh_schema["subscribers_count"]

    # Crude differentiation scheme based on PCA analysis
    score = np.log1p(gh_stargazers) + np.log1p(gh_forks) + np.log1p(gh_watchers) + np.log1p(gh_subscribers)

    # Separate tools into two maturity levels based on score threshold
    if score > 3:
        if has_bt_maturity and bt_maturity == "Mature":
            logging.info("EXACT MATCH: GitHub maturity score matches existing bio.tools maturity 'Mature'.")
            return bt_maturity
        elif has_bt_maturity:
            logging.info("CONFLICT: GitHub maturity score conflicts with existing bio.tools maturity. Will overwrite.")
        else:
            logging.info("ADDED: Using GitHub maturity score to set bio.tools maturity to 'Mature'.")
        return "Mature"
    else:
        if has_bt_maturity and bt_maturity == "Emerging":
            logging.info("EXACT MATCH: GitHub maturity score matches existing bio.tools maturity 'Emerging'.")
            return bt_maturity
        elif has_bt_maturity:
            logging.info("CONFLICT: GitHub maturity score conflicts with existing bio.tools maturity. Will overwrite.")
        else:
            logging.info("ADDED: Using GitHub maturity score to set bio.tools maturity to 'Emerging'.")
        return "Emerging"
    return None
