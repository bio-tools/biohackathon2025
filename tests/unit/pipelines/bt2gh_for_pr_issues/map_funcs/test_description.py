"""
Unit tests for mapping bio.tools description to GitHub issues (map_description).

These tests validate behavior of map_description as implemented:
- bio.tools silent => no issue
- GitHub present and equal => no issue
- GitHub present and different => conflict but STILL proposes bio.tools value
- GitHub missing and bio.tools present => proposes bio.tools value
"""

from __future__ import annotations

import pytest

from bridge.pipelines.bt2gh_for_pr_issues.map_funcs.description import map_description

pytestmark = pytest.mark.asyncio

TITLE = "Add description from bio.tools metadata"


def _body(out: dict[str, str] | None) -> str:
    assert out is not None
    assert list(out.keys()) == [TITLE]
    return out[TITLE]


@pytest.mark.parametrize(
    "gh_description, bt_description, expect_issue, expected_snippet",
    [
        # -----------------------------
        # bio.tools silent => no issue
        # -----------------------------
        (None, None, False, None),
        ("Already set", None, False, None),
        # empty string is NOT None -> code treats it as present and proposes
        (None, "   ", True, "\n\n\n\n"),
        # -----------------------------
        # both present and equal (after normalize_text) => no issue
        # -----------------------------
        ("Hello world", "Hello world", False, None),
        ("Hello world", "  Hello   world  ", False, None),
        # -----------------------------
        # GitHub present but different => code proposes anyway
        # -----------------------------
        ("Existing GH desc", "Different BT desc", True, "Different BT desc"),
        ("Existing GH desc", "Hello &lt;b&gt;world&lt;/b&gt;", True, "Hello world"),
        # -----------------------------
        # GitHub missing => propose bt
        # -----------------------------
        (None, "A bio.tools description.", True, "A bio.tools description."),
        ("   ", "A bio.tools description.", True, "A bio.tools description."),
        (None, "Hello &lt;i&gt;world&lt;/i&gt;\n\nand friends", True, "Hello worldand friends"),
    ],
)
async def test_map_description(gh_description, bt_description, expect_issue, expected_snippet):
    out = await map_description(gh_description=gh_description, bt_description=bt_description)

    if not expect_issue:
        assert out is None
        return

    body = _body(out)
    assert "The bio.tools description is:" in body
    assert "Please consider adding this description to the GitHub repository." in body

    if expected_snippet is not None:
        assert expected_snippet in body


async def test_map_description_issue_body_wraps_description_block():
    out = await map_description(gh_description=None, bt_description="X")
    body = _body(out)

    # very light structure checks
    assert body.startswith("The bio.tools description is:\n\n")
    assert "\n\nPlease consider adding this description" in body
