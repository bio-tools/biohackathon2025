"""
Unit tests for mapping GitHub homepage to bio.tools homepage (map_homepage).
"""

from __future__ import annotations

import pytest

from bridge.core.biotools import UrlftpType
from bridge.pipelines.gh2bt_for_meta.map_funcs.homepage import map_homepage


def _bt(url: str | None) -> UrlftpType | None:
    return None if url is None else UrlftpType(root=url)


@pytest.mark.parametrize(
    "gh_schema, bt_homepage, expected_url",
    [
        # ---------------------------
        # GitHub silent: preserve bt
        # ---------------------------
        (
            {"homepage": None, "html_url": "https://github.com/o/r"},
            _bt("https://example.org/docs"),
            "https://example.org/docs",
        ),
        (
            {"homepage": None, "html_url": "https://github.com/o/r"},
            None,
            # special fallback when both missing: use repo html_url
            "https://github.com/o/r",
        ),
        (
            {"homepage": None, "html_url": None},
            None,
            # malformed schema: no homepage + no repo url => None
            None,
        ),
        # ---------------------------
        # GitHub homepage present
        # ---------------------------
        (
            {"homepage": "https://example.org/docs", "html_url": "https://github.com/o/r"},
            None,
            "https://example.org/docs",
        ),
        # canonicalization: scheme/host case + trailing slash should be treated as equal
        (
            {"homepage": "HTTPS://EXAMPLE.ORG/docs/", "html_url": "https://github.com/o/r"},
            _bt("https://example.org/docs"),
            # should preserve existing bt value because canonical URLs match
            "https://example.org/docs",
        ),
        # conflict: GitHub differs -> GitHub wins
        (
            {"homepage": "https://new.example.org", "html_url": "https://github.com/o/r"},
            _bt("https://old.example.org"),
            "https://new.example.org/",
        ),
        # query canonicalization: ordering differences should match
        (
            {"homepage": "https://ex.org/path?b=2&a=1", "html_url": "https://github.com/o/r"},
            _bt("https://ex.org/path?a=1&b=2"),
            # canonical forms match, so preserve bt_value (original formatting)
            "https://ex.org/path?a=1&b=2",
        ),
        # fragment is dropped by canonicalize_url, so these should match -> preserve bt
        (
            {"homepage": "https://ex.org/page#section", "html_url": "https://github.com/o/r"},
            _bt("https://ex.org/page"),
            "https://ex.org/page",
        ),
    ],
)
def test_map_homepage(gh_schema, bt_homepage, expected_url):
    out = map_homepage(gh_schema=gh_schema, bt_homepage=bt_homepage)

    if expected_url is None:
        assert out is None
    else:
        assert out is not None
        assert str(out.root) == expected_url


def test_map_homepage_returns_UrlftpType_when_setting_from_github():
    """
    Sanity check: when GitHub homepage is present and bt is None,
    output is a UrlftpType.
    """
    out = map_homepage(
        gh_schema={"homepage": "https://example.org", "html_url": "https://github.com/o/r"},
        bt_homepage=None,
    )
    assert isinstance(out, UrlftpType)
    assert str(out.root) == "https://example.org/"
