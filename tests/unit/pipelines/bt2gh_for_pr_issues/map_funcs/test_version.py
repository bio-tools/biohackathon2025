"""
Unit tests for mapping bio.tools versions to GitHub issues (map_version).

These tests focus on the public function `map_version`. Version parsing and
comparison logic is tested separately in tests for bridge.pipelines.shared.version.
Here we validate integration-level branching:
- no bio.tools versions => no issue
- no comparable bio.tools version => no issue
- GitHub has no latest tag while bio.tools has versions => issue
- bio.tools newer than GitHub => issue
- GitHub up-to-date => no issue
"""

from __future__ import annotations

import pytest

from bridge.core.biotools import VersionType
from bridge.pipelines.bt2gh_for_pr_issues.map_funcs.version import map_version

TITLE = "Create GitHub release"


def VT(s: str) -> VersionType:
    return VersionType(root=s)


def _body(out: dict[str, str] | None) -> str:
    assert out is not None
    assert list(out.keys()) == [TITLE]
    return out[TITLE]


@pytest.mark.parametrize(
    "gh_latest_version_tag, bt_versions, expect_issue, expected_snippets",
    [
        # -----------------------------
        # bio.tools silent => no issue
        # -----------------------------
        (None, None, False, []),
        ("v1.0.0", None, False, []),
        (None, [], False, []),
        ("v1.0.0", [], False, []),
        # -----------------------------
        # no comparable bio.tools version => no issue
        # (see shared version tests for parsing rules; here we just assert behavior)
        # NOTE: find_latest_bt_version returns None only when list is non-empty but
        # *every* entry is effectively non-comparable under its rules.
        # With current implementation, RAW entries are still "baseline" and returned,
        # so this branch is hard to hit. We keep a case anyway in case the parser changes.
        # -----------------------------
        ("1.0.0", [VT("release-x")], False, []),  # probably NOT None today; kept as doc only
        # -----------------------------
        # GitHub has no latest tag => issue when bt has versions
        # -----------------------------
        (
            None,
            [VT("1.2.3")],
            True,
            ["The latest bio.tools version is '1.2.3'.", "No GitHub release is found."],
        ),
        (
            "",
            [VT("1.2.3")],
            True,
            ["The latest bio.tools version is '1.2.3'.", "No GitHub release is found."],
        ),
        # -----------------------------
        # bio.tools newer than GitHub => issue
        # -----------------------------
        (
            "1.2.3",
            [VT("1.2.4"), VT("1.0.0")],
            True,
            ["The latest bio.tools version '1.2.4' is newer than the latest GitHub release '1.2.3'."],
        ),
        # prefix 'v' should still compare under shared version rules
        (
            "v1.2.3",
            [VT("1.2.4")],
            True,
            ["'1.2.4' is newer than", "'v1.2.3'"],
        ),
        # date versions compare as dates
        (
            "2025-01-01",
            [VT("2025-12-13")],
            True,
            ["'2025-12-13' is newer than", "'2025-01-01'"],
        ),
        # -----------------------------
        # GitHub up-to-date => no issue
        # -----------------------------
        ("1.2.3", [VT("1.2.3"), VT("1.0.0")], False, []),
        ("1.2.3", [VT("1.2.2")], False, []),
        ("2025-12-13", [VT("2025-12-13"), VT("2025-01-01")], False, []),
        # If incomparable versions exist but none is newer => no issue
        ("1.2.3", [VT("release-candidate"), VT("2025-12-13")], False, []),
    ],
)
def test_map_version(gh_latest_version_tag, bt_versions, expect_issue, expected_snippets):
    out = map_version(gh_latest_version_tag=gh_latest_version_tag, bt_versions=bt_versions)

    if not expect_issue:
        assert out is None
        return

    body = _body(out)
    assert "Please consider creating a corresponding GitHub release." in body

    for snippet in expected_snippets:
        assert snippet in body


def test_map_version_issue_body_structure_mentions_latest_bt_and_gh_tag():
    out = map_version(gh_latest_version_tag="1.0.0", bt_versions=[VT("1.1.0")])
    body = _body(out)

    # light structure checks (don’t over-couple to exact phrasing)
    assert "latest bio.tools version" in body
    assert "latest GitHub release" in body
