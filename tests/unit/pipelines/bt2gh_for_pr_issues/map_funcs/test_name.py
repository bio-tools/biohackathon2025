"""
Unit tests for mapping bio.tools name/id to GitHub issues (map_name).

These tests validate behavior of map_name as implemented:
- bt_params missing => no issue
- bio.tools silent (bt_id_norm is None) => no issue
- if GitHub name contains bt_id OR contains bt_name => no issue
- if GitHub differs => proposes an issue suggesting bt_id (even if GitHub is present)
"""

from __future__ import annotations

import pytest

from bridge.pipelines.bt2gh_for_pr_issues.map_funcs.name import map_name

pytestmark = pytest.mark.asyncio

TITLE = "Update repository name from bio.tools metadata"


def _body(out: dict[str, str] | None) -> str:
    assert out is not None
    assert list(out.keys()) == [TITLE]
    return out[TITLE]


@pytest.mark.parametrize(
    "gh_name, bt_params, expect_issue, expected_snippets",
    [
        # -----------------------------
        # bio.tools params missing => no issue
        # -----------------------------
        (None, None, False, []),
        ("repo", None, False, []),
        # -----------------------------
        # bio.tools silent for bt_id => no issue
        # (bt_norm is bt_id_norm, so if bt_id is None -> bt_norm None -> policy returns None)
        # -----------------------------
        ("repo", {"name": "Tool Name", "biotoolsID": None}, False, []),
        ("repo", {"name": None, "biotoolsID": None}, False, []),
        # -----------------------------
        # GitHub matches bt_id (containment)
        # -----------------------------
        ("cooltool", {"name": "Cool Tool", "biotoolsID": "cooltool"}, False, []),
        ("COOLTOOL", {"name": "Cool Tool", "biotoolsID": "cooltool"}, False, []),
        ("cooltool-plus", {"name": "Cool Tool", "biotoolsID": "cooltool"}, False, []),
        ("tool", {"name": "Irrelevant", "biotoolsID": "toolkit"}, False, []),  # gh in bt_id
        # -----------------------------
        # GitHub matches bt_name (containment) => no issue
        # -----------------------------
        ("awesome-tool", {"name": "Awesome", "biotoolsID": "awesomeid"}, False, []),
        ("Awesome", {"name": "awesome-tool", "biotoolsID": "awesomeid"}, False, []),
        # -----------------------------
        # Conflict => issue is proposed (even if gh_name exists)
        # -----------------------------
        (
            "repo",
            {"name": "Tool Name", "biotoolsID": "biotoolsid"},
            True,
            ["repo", "Tool Name", "biotoolsid", "Proposed new name"],
        ),
        # gh_name is None => still proposes (bt_id present)
        (
            None,
            {"name": "Tool Name", "biotoolsID": "biotoolsid"},
            True,
            ["The GitHub repository name 'None'", "Tool Name", "biotoolsid"],
        ),
        # Newlines / weird whitespace: the issue body uses raw bt fields (not normalized)
        (
            "repo",
            {"name": "Tool\tName\n", "biotoolsID": "bio\nid"},
            True,
            ["repo", "Tool\tName\n", "bio\nid"],
        ),
    ],
)
async def test_map_name(gh_name, bt_params, expect_issue, expected_snippets):
    out = await map_name(gh_name=gh_name, bt_params=bt_params)

    if not expect_issue:
        assert out is None
        return

    body = _body(out)
    assert "Please consider updating the repository name." in body

    for snippet in expected_snippets:
        assert snippet in body


async def test_map_name_issue_body_mentions_biotools_id_as_proposed_name():
    out = await map_name(
        gh_name="repo",
        bt_params={"name": "Tool Name", "biotoolsID": "mytoolid"},
    )
    body = _body(out)
    assert "Proposed new name: 'mytoolid'." in body
