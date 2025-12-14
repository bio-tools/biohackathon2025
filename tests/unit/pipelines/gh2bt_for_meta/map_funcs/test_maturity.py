"""
Unit tests for mapping GitHub maturity signals to bio.tools maturity (map_maturity).
"""

from __future__ import annotations

import pytest

from bridge.core.biotools import Maturity
from bridge.pipelines.gh2bt_for_meta.map_funcs.maturity import map_maturity


@pytest.mark.parametrize(
    "gh_schema, bt_maturity, expected",
    [
        # -----------------------
        # GitHub schema missing
        # -----------------------
        (None, None, None),
        (None, Maturity.Mature, Maturity.Mature),
        # -----------------------
        # Archived repo is always Legacy
        # -----------------------
        ({"archived": True}, None, Maturity.Legacy),
        ({"archived": True}, Maturity.Legacy, Maturity.Legacy),  # already matches
        ({"archived": True}, Maturity.Mature, Maturity.Legacy),  # overwrite
        ({"archived": True}, Maturity.Emerging, Maturity.Legacy),  # overwrite
        # -----------------------
        # Active repo -> score-based classification
        # Threshold: score > 3 => Mature, else Emerging
        # -----------------------
        (
            # all zeros => score=0 => Emerging
            {"archived": False, "stargazers_count": 0, "forks_count": 0, "watchers_count": 0, "subscribers_count": 0},
            None,
            Maturity.Emerging,
        ),
        (
            # values chosen so log1p sum exceeds 3 -> Mature
            # log1p(10)=~2.398, others 0 => ~2.398 (not enough)
            # log1p(10)+log1p(10)=~4.796 => Mature
            {"archived": False, "stargazers_count": 10, "forks_count": 10, "watchers_count": 0, "subscribers_count": 0},
            None,
            Maturity.Mature,
        ),
        (
            # if bt already matches computed, preserve bt value
            {"archived": False, "stargazers_count": 10, "forks_count": 10, "watchers_count": 0, "subscribers_count": 0},
            Maturity.Mature,
            Maturity.Mature,
        ),
        (
            # conflict -> overwrite with GitHub-derived value
            {"archived": False, "stargazers_count": 10, "forks_count": 10, "watchers_count": 0, "subscribers_count": 0},
            Maturity.Emerging,
            Maturity.Mature,
        ),
        (
            # computed Emerging, bt Mature => overwrite
            {"archived": False, "stargazers_count": 0, "forks_count": 0, "watchers_count": 0, "subscribers_count": 0},
            Maturity.Mature,
            Maturity.Emerging,
        ),
    ],
)
def test_map_maturity(gh_schema, bt_maturity, expected):
    assert map_maturity(gh_schema=gh_schema, bt_maturity=bt_maturity) == expected


@pytest.mark.parametrize(
    "bad_value",
    [
        None,
        "not-a-number",
        {"oops": 1},
        object(),
    ],
)
def test_map_maturity_treats_non_numeric_metrics_as_zero(bad_value):
    """
    Non-numeric metrics should be treated as 0.0 (via _safe_metric),
    which means with all metrics invalid => score=0 => Emerging.
    """
    gh_schema = {
        "archived": False,
        "stargazers_count": bad_value,
        "forks_count": bad_value,
        "watchers_count": bad_value,
        "subscribers_count": bad_value,
    }
    assert map_maturity(gh_schema=gh_schema, bt_maturity=None) == Maturity.Emerging
