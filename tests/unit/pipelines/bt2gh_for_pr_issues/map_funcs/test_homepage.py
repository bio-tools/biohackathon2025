"""
Unit tests for mapping bio.tools homepage to GitHub issues (map_homepage).
"""

from __future__ import annotations

import pytest

from bridge.core.biotools import UrlftpType
from bridge.pipelines.bt2gh_for_pr_issues.map_funcs.homepage import map_homepage

pytestmark = pytest.mark.asyncio

TITLE = "Add homepage from bio.tools metadata"


def _bt(url: str | None) -> UrlftpType | None:
    return None if url is None else UrlftpType(root=url)


def _body(out: dict[str, str] | None) -> str:
    assert out is not None
    assert list(out.keys()) == [TITLE]
    return out[TITLE]


@pytest.mark.parametrize(
    "gh_schema, bt_homepage, expect_issue, expected_snippet",
    [
        # -----------------------------
        # bio.tools silent => no issue
        # -----------------------------
        ({"homepage": None, "html_url": "https://github.com/o/r"}, None, False, None),
        ({"homepage": "", "html_url": "https://github.com/o/r"}, None, False, None),
        # -----------------------------
        # bt homepage equals repo URL => no issue (canonicalized)
        # -----------------------------
        (
            {"homepage": None, "html_url": "https://github.com/o/r"},
            _bt("https://github.com/o/r/"),  # trailing slash should be ignored
            False,
            None,
        ),
        (
            {"homepage": None, "html_url": "https://GITHUB.COM/o/r/"},
            _bt("https://github.com/o/r"),
            False,
            None,
        ),
        # -----------------------------
        # both present and equal => no issue (canonicalized)
        # -----------------------------
        (
            {"homepage": "https://example.org/docs", "html_url": "https://github.com/o/r"},
            _bt("https://example.org/docs/"),
            False,
            None,
        ),
        (
            {"homepage": "https://ex.org/path?a=1&b=2", "html_url": "https://github.com/o/r"},
            _bt("https://ex.org/path?b=2&a=1"),
            False,
            None,
        ),
        # -----------------------------
        # GitHub present but different => code proposes anyway (policy via reconcile_bt_over_gh)
        # -----------------------------
        (
            {"homepage": "https://gh.example.org", "html_url": "https://github.com/o/r"},
            _bt("https://bt.example.org"),
            True,
            "https://bt.example.org",
        ),
        # -----------------------------
        # GitHub missing/empty but bt present => propose bt
        # -----------------------------
        (
            {"homepage": None, "html_url": "https://github.com/o/r"},
            _bt("https://example.org/docs"),
            True,
            "https://example.org/docs",
        ),
        (
            {"homepage": "", "html_url": "https://github.com/o/r"},
            _bt("https://example.org/docs"),
            True,
            "https://example.org/docs",
        ),
        # note: map_homepage treats "   " as truthy -> canonicalize_url("   ") => "///" (implementation detail),
        # so use empty string/None for "unset" in tests.
        # -----------------------------
        # bt present but gh_schema missing html_url still can propose (unless bt==repo-url check triggers)
        # -----------------------------
        (
            {"homepage": None, "html_url": None},
            _bt("https://example.org"),
            True,
            "https://example.org",
        ),
        # -----------------------------
        # bt homepage has fragment; canonicalize_url drops fragment, so equality works
        # -----------------------------
        (
            {"homepage": "https://ex.org/page", "html_url": "https://github.com/o/r"},
            _bt("https://ex.org/page#section"),
            False,
            None,
        ),
    ],
)
async def test_map_homepage(gh_schema, bt_homepage, expect_issue, expected_snippet):
    out = await map_homepage(gh_schema=gh_schema, bt_homepage=bt_homepage)

    if not expect_issue:
        assert out is None
        return

    body = _body(out)
    assert "The bio.tools homepage is:" in body
    assert "Please consider adding this homepage to the GitHub repository." in body

    if expected_snippet is not None:
        assert expected_snippet in body


async def test_map_homepage_issue_body_wraps_homepage_block():
    out = await map_homepage(
        gh_schema={"homepage": None, "html_url": "https://github.com/o/r"},
        bt_homepage=_bt("https://example.org"),
    )
    body = _body(out)

    assert body.startswith("The bio.tools homepage is:\n\n")
    assert "\n\nPlease consider adding this homepage" in body
