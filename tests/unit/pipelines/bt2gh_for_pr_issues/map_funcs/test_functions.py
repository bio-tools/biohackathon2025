"""
Unit tests for mapping bio.tools functions to GitHub (map_functions + map_functions_to_readme).

These tests focus strictly on behavior, not logging. We patch:
- fill_template: deterministic placeholder substitution
- find_matches: deterministic "README contains functions?" signals + match blocks
- separate_snippets_from_text: deterministic splitting so we can assert exact output
- yaml.safe_dump: deterministic YAML rendering so _build_function output is stable

We avoid depending on Pydantic FunctionItem by using minimal stubs that provide:
- .operation (list of op objects with .term/.uri)
- .model_dump(exclude_none=True)
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

import bridge.pipelines.bt2gh_for_pr_issues.map_funcs.functions as mod


# -----------------------------
# Minimal stubs
# -----------------------------


@dataclass
class _Op:
    term: str | None = None
    uri: str | None = None


class _Func:
    def __init__(self, ops: list[_Op], dumped: dict):
        self.operation = ops
        self._dumped = dumped

    def model_dump(self, exclude_none: bool = True):
        return self._dumped


class _Match:
    def __init__(self, block: str):
        self._block = block

    def group(self, idx_or_name=0):
        # module uses m.group(0) only here
        assert idx_or_name == 0
        return self._block


# -----------------------------
# Fixtures: patch dependencies
# -----------------------------


@pytest.fixture(autouse=True)
def _patch_helpers(monkeypatch):
    # Deterministic template filler (handles {{K}}, {{ K}}, {{K }}, {{ K }})
    def fake_fill_template(template: str, filling: dict[str, str]) -> str:
        s = template
        for k, v in filling.items():
            for pattern in (f"{{{{ {k} }}}}", f"{{{{{k}}}}}", f"{{{{ {k}}}}}", f"{{{{{k} }}}}"):
                s = s.replace(pattern, v)
        return s

    # Deterministic YAML dump
    def fake_safe_dump(data, **_kwargs):
        lines = []
        for k, v in data.items():
            lines.append(f"{k}: {v}")
        return "\n".join(lines) + "\n"

    monkeypatch.setattr(mod, "fill_template", fake_fill_template)
    monkeypatch.setattr(mod.yaml, "safe_dump", fake_safe_dump)


@pytest.fixture
def _patch_find_matches(monkeypatch):
    """
    Patch find_matches; tests can replace by monkeypatching again if needed.
    Default: no functions in README.
    """
    monkeypatch.setattr(mod, "find_matches", lambda _txt: [])


@pytest.fixture
def _patch_separate_snippets(monkeypatch):
    """
    Patch separate_snippets_from_text; default is a naive split:
    remove all snippets and return (before, after) as (prefix, suffix)
    around the first occurrence of the first snippet.

    Tests that care will provide explicit behavior via monkeypatch.
    """

    def fake_sep(text: str, snippets: list[str]):
        # simple, deterministic behavior:
        # remove each snippet once (first occurrence), and return remaining as (before, after="")
        out = text
        for snip in snippets:
            idx = out.find(snip)
            if idx >= 0:
                out = out[:idx] + out[idx + len(snip) :]
        return out, ""

    monkeypatch.setattr(mod, "separate_snippets_from_text", fake_sep)


# -----------------------------
# Helpers to build functions
# -----------------------------


def F(name_term: str | None, name_uri: str | None, dumped: dict) -> _Func:
    return _Func(ops=[_Op(term=name_term, uri=name_uri)], dumped=dumped)


# =========================================================
# map_functions (issue creation)
# =========================================================

TITLE = "Add function annotations from bio.tools metadata"


def _body(out: dict[str, str] | None) -> str:
    assert out is not None
    assert list(out.keys()) == [TITLE]
    return out[TITLE]


@pytest.mark.parametrize(
    "case, matches, bt_functions, expect_issue",
    [
        (
            "functions already in readme => no issue",
            [_Match("<details>...</details>")],
            [F("X", None, {"x": 1})],
            False,
        ),
        ("bt_functions None => no issue", [], None, False),
        ("bt_functions empty => no issue", [], [], False),
        ("bt_functions present and no matches => issue", [], [F("X", None, {"x": 1})], True),
    ],
)
def test_map_functions_issue_policy(case, matches, bt_functions, expect_issue, monkeypatch, _patch_helpers):
    monkeypatch.setattr(mod, "find_matches", lambda _txt: matches)

    out = mod.map_functions(gh_readme="README", bt_functions=bt_functions)

    if not expect_issue:
        assert out is None, case
        return

    body = _body(out)
    assert "The bio.tools metadata contains the following function annotations" in body
    assert "~~~markdown" in body
    assert "# Functions" in body  # section header
    # function block structure should be present
    assert "<details>" in body
    assert "```yaml" in body
    assert "# biotools-function" in body
    assert "</details>" in body


def test_map_functions_builds_function_name_from_term_then_uri_then_fallback(
    monkeypatch, _patch_helpers, _patch_find_matches
):
    # No matches => issue created
    funcs = [
        F("OpTerm", None, {"k": "v"}),
        F(None, "http://edamontology.org/operation_0001", {"k2": "v2"}),
        _Func(ops=[_Op(term=None, uri=None)], dumped={"k3": "v3"}),  # fallback name
    ]

    out = mod.map_functions(gh_readme="README", bt_functions=funcs)
    body = _body(out)

    assert "<summary>OpTerm</summary>" in body
    assert "<summary>http://edamontology.org/operation_0001</summary>" in body
    assert "<summary>Unnamed operation</summary>" in body


def test_map_functions_uses_all_operations_in_name(monkeypatch, _patch_helpers, _patch_find_matches):
    func = _Func(
        ops=[_Op(term="A", uri=None), _Op(term=None, uri="U"), _Op(term=None, uri=None)],
        dumped={"x": 1},
    )

    out = mod.map_functions(gh_readme="README", bt_functions=[func])
    body = _body(out)

    # joined by ", "
    assert "<summary>A, U, Unnamed operation</summary>" in body


# =========================================================
# map_functions_to_readme (PR content update)
# =========================================================


@pytest.mark.parametrize(
    "case, gh_readme, matches, bt_functions, expected",
    [
        ("readme None => unchanged", None, [], [F("X", None, {"x": 1})], None),
        ("no matches => unchanged", "Intro\nBody\n", [], [F("X", None, {"x": 1})], "Intro\nBody\n"),
        ("matches but bt_functions None => unchanged", "X", [_Match("OLD")], None, "X"),
        ("matches but bt_functions empty => unchanged", "X", [_Match("OLD")], [], "X"),
    ],
)
def test_map_functions_to_readme_no_update_cases(
    case, gh_readme, matches, bt_functions, expected, monkeypatch, _patch_helpers
):
    monkeypatch.setattr(mod, "find_matches", lambda _txt: matches)

    out = mod.map_functions_to_readme(gh_readme=gh_readme, bt_functions=bt_functions)
    assert out == expected, case


def test_map_functions_to_readme_replaces_all_existing_blocks(monkeypatch, _patch_helpers, _patch_separate_snippets):
    gh_readme = "BEFORE\nOLD1\nMIDDLE\nOLD2\nAFTER\n"
    blocks = ["OLD1", "OLD2"]
    monkeypatch.setattr(mod, "find_matches", lambda _txt: [_Match(b) for b in blocks])

    # Force a split that proves we removed both blocks and inserted new ones between before/after
    def fake_sep(text: str, snippets: list[str]):
        assert snippets == blocks
        return ("BEFORE\n", "\nAFTER\n")

    monkeypatch.setattr(mod, "separate_snippets_from_text", fake_sep)

    new_funcs = [
        F("NewOp", None, {"a": 1}),
        F("Another", None, {"b": 2}),
    ]

    out = mod.map_functions_to_readme(gh_readme=gh_readme, bt_functions=new_funcs)

    assert out is not None
    assert out.startswith("BEFORE\n")
    assert out.endswith("\nAFTER\n")

    # Old blocks gone
    assert "OLD1" not in out
    assert "OLD2" not in out

    # New blocks inserted
    assert "<summary>NewOp</summary>" in out
    assert "<summary>Another</summary>" in out
    assert "# biotools-function" in out
    assert "a: 1" in out  # from fake_safe_dump
    assert "b: 2" in out


def test_map_functions_to_readme_calls_separate_snippets_with_exact_match_blocks(monkeypatch, _patch_helpers):
    gh_readme = "X\nOLD\nY\n"
    m1 = _Match("OLD")
    monkeypatch.setattr(mod, "find_matches", lambda _txt: [m1])

    captured: dict[str, object] = {}

    def fake_sep(text: str, snippets: list[str]):
        captured["text"] = text
        captured["snippets"] = list(snippets)
        return ("X\n", "\nY\n")

    monkeypatch.setattr(mod, "separate_snippets_from_text", fake_sep)

    out = mod.map_functions_to_readme(gh_readme=gh_readme, bt_functions=[F("New", None, {"k": "v"})])

    assert captured["text"] == gh_readme
    assert captured["snippets"] == ["OLD"]
    assert out is not None
    assert "<summary>New</summary>" in out


def test_build_function_template_replaces_yaml_placeholder_even_without_space(monkeypatch, _patch_helpers):
    func = F("X", None, {"a": 1})
    txt = mod._build_function(func)
    assert "{{ FUNCTION_YAML" not in txt  # placeholder must be gone
    assert "a: 1" in txt
