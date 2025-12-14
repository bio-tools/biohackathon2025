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
    "gh_schema, bt_homepage, expect_issue, expected_homepage_in_body",
    [
        # -------------------------------------------------
        # bio.tools silent => no issue (bt_norm is None)
        # -------------------------------------------------
        ({"homepage": None, "html_url": "https://github.com/o/r"}, _bt(None), False, None),
        ({"homepage": "", "html_url": "https://github.com/o/r"}, _bt(None), False, None),
        ({"homepage": "https://example.org", "html_url": "https://github.com/o/r"}, _bt(None), False, None),
        # -------------------------------------------------
        # bt homepage equals repo html_url (canonicalized) => no issue
        # -------------------------------------------------
        (
            {"homepage": None, "html_url": "https://github.com/o/r"},
            _bt("https://github.com/o/r/"),
            False,
            None,
        ),
        (
            {"homepage": None, "html_url": "HTTPS://GITHUB.COM/o/r/"},
            _bt("https://github.com/o/r"),
            False,
            None,
        ),
        # -------------------------------------------------
        # GitHub homepage missing => propose bt homepage
        # (note: canonicalize_url strips trailing slash)
        # -------------------------------------------------
        (
            {"homepage": None, "html_url": "https://github.com/o/r"},
            _bt("https://example.org/docs"),
            True,
            "https://example.org/docs",
        ),
        (
            {"homepage": "", "html_url": "https://github.com/o/r"},
            _bt("https://example.org/docs/"),
            True,
            "https://example.org/docs",
        ),
        # query ordering canonicalization in the suggested value
        (
            {"homepage": None, "html_url": "https://github.com/o/r"},
            _bt("https://ex.org/path?b=2&a=1"),
            True,
            "https://ex.org/path?a=1&b=2",
        ),
        # fragment is dropped by canonicalize_url
        (
            {"homepage": None, "html_url": "https://github.com/o/r"},
            _bt("https://ex.org/page#section"),
            True,
            "https://ex.org/page",
        ),
        # -------------------------------------------------
        # GitHub homepage present and equal (canonicalized) => no issue
        # -------------------------------------------------
        (
            {"homepage": "HTTPS://EXAMPLE.ORG/docs/", "html_url": "https://github.com/o/r"},
            _bt("https://example.org/docs"),
            False,
            None,
        ),
        (
            {"homepage": "https://ex.org/path?b=2&a=1", "html_url": "https://github.com/o/r"},
            _bt("https://ex.org/path?a=1&b=2"),
            False,
            None,
        ),
        # -------------------------------------------------
        # GitHub homepage present but different => conflict, but STILL proposes
        # (because reconcile_bt_over_gh proposes on conflict)
        # -------------------------------------------------
        (
            {"homepage": "https://gh.example.org", "html_url": "https://github.com/o/r"},
            _bt("https://bt.example.org"),
            True,
            "https://bt.example.org",
        ),
    ],
)
async def test_map_homepage(gh_schema, bt_homepage, expect_issue, expected_homepage_in_body):
    out = await map_homepage(gh_schema=gh_schema, bt_homepage=bt_homepage)

    if not expect_issue:
        assert out is None
        return

    body = _body(out)
    assert "The bio.tools homepage is:" in body
    assert "Please consider adding this homepage to the GitHub repository." in body

    assert expected_homepage_in_body is not None
    assert expected_homepage_in_body in body


async def test_map_homepage_issue_payload_shape_and_title():
    out = await map_homepage(
        gh_schema={"homepage": None, "html_url": "https://github.com/o/r"},
        bt_homepage=_bt("https://example.org"),
    )
    assert out is not None
    assert list(out.keys()) == [TITLE]
    assert isinstance(out[TITLE], str)
