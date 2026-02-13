"""
Unit tests for shared functions utilities for pipelines.

Behavior under test:
- A function block is ONLY recognized if the code fence is ```yaml and it contains
  a '# biotools-function' marker line.
- The marker line is part of the fenced YAML code, but is NOT included in the
  captured group('yaml'); group('yaml') contains only the YAML body after the marker.
"""

from __future__ import annotations

import pytest

import bridge.pipelines.shared.functions as fnmod


def _block(
    name: str,
    yaml_body: str,
    newline: str = "\n",
    include_marker: bool = True,
    fence_lang: str = "yaml",
) -> str:
    marker = f"# biotools-function{newline}" if include_marker else ""
    return (
        f"<details>{newline}"
        f"<summary>{name}</summary>{newline}"
        f"```{fence_lang}{newline}"
        f"{marker}"
        f"{yaml_body}{newline}"
        f"```{newline}"
        f"</details>"
    )


def test_find_matches_none_or_empty_returns_empty():
    assert fnmod.find_matches(None) == []
    assert fnmod.find_matches("") == []


def test_find_match_yamls_none_or_empty_returns_empty():
    assert fnmod.find_match_yamls(None) == []
    assert fnmod.find_match_yamls("") == []


def test_find_matches_single_block_captures_name_and_yaml_body_only_and_marker_is_in_code():
    body = "operation:\n  - term: Multiple sequence alignment\n"
    text = "Intro\n\n" + _block("Align sequences", body) + "\n\nOutro"

    matches = fnmod.find_matches(text)
    assert len(matches) == 1

    m = matches[0]
    assert m.group("name") == "Align sequences"

    # group('yaml') is the body ONLY (marker excluded by design)
    assert m.group("yaml") == body + "\n"

    # but the marker is inside the overall matched code block
    assert "# biotools-function" in m.group(0)


def test_find_match_yamls_single_block_returns_yaml_body_only():
    body = "output:\n  - data:\n      term: Alignment\n"
    text = _block("Something", body)

    out = fnmod.find_match_yamls(text)
    assert out == [body + "\n"]


def test_find_matches_multiple_blocks_returns_all_in_order_and_marker_present_in_each_match():
    body1 = "a: 1\n"
    body2 = "b:\n  - 2\n"
    text = "Header\n" + _block("First", body1) + "\n\nMiddle\n\n" + _block("Second", body2) + "\nFooter\n"

    matches = fnmod.find_matches(text)
    assert [m.group("name") for m in matches] == ["First", "Second"]

    # body only
    assert [m.group("yaml") for m in matches] == [body1 + "\n", body2 + "\n"]

    # marker in matched block text for each
    assert all("# biotools-function" in m.group(0) for m in matches)

    assert fnmod.find_match_yamls(text) == [body1 + "\n", body2 + "\n"]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_find_matches_supports_windows_newlines(newline: str):
    # Body uses \n; outer newlines vary. This should still match.
    body = "x: 1\ny: 2\n"
    text = _block("WinNewlines", body.rstrip("\n"), newline=newline)

    matches = fnmod.find_matches(text)
    assert len(matches) == 1

    m = matches[0]
    assert m.group("name") == "WinNewlines"

    # body only
    assert "x: 1" in m.group("yaml")
    assert "y: 2" in m.group("yaml")

    # marker present in full match
    assert "# biotools-function" in m.group(0)


def test_find_matches_requires_marker_comment_line():
    text = _block("No marker", "operation:\n  - term: X\n", include_marker=False)
    assert fnmod.find_matches(text) == []
    assert fnmod.find_match_yamls(text) == []


def test_find_matches_does_not_match_wrong_fence_language():
    text = _block("Wrong fence", "a: 1\n", fence_lang="yml")
    assert fnmod.find_matches(text) == []
    assert fnmod.find_match_yamls(text) == []


def test_find_matches_allows_whitespace_after_yaml_fence_and_marker_indent_and_captures_body_only():
    text = (
        "<details>\n"
        "<summary>Whitespace ok</summary>\n"
        "```yaml   \n"
        "#    biotools-function   \n"
        "a: 1\n"
        "```\n"
        "</details>\n"
    )
    matches = fnmod.find_matches(text)
    assert len(matches) == 1

    m = matches[0]
    assert m.group("name") == "Whitespace ok"

    # marker not in group('yaml')
    assert m.group("yaml") == "a: 1\n"

    # but marker exists in the matched code
    assert "biotools-function" in m.group(0)


def test_find_matches_summary_with_angle_bracket_does_not_match():
    # '<' inside summary text prevents matching entirely due to [^\\r\\n<]*
    text = _block("Name with <tag>", "a: 1\n")
    assert fnmod.find_matches(text) == []
    assert fnmod.find_match_yamls(text) == []


def test_find_matches_yaml_is_non_greedy_stops_at_first_closing_fence():
    body = "a: 1\n"
    text = _block("First", body) + "\n\n" + "<details>\n<summary>Not a function</summary>\nnope\n</details>\n"

    matches = fnmod.find_matches(text)
    assert len(matches) == 1

    m = matches[0]
    assert m.group("name") == "First"
    assert m.group("yaml") == body + "\n"
    assert "# biotools-function" in m.group(0)
