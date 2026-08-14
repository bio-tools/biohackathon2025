"""
Unit tests for string templating utilities.
"""

import pytest

from bridge.pipelines.utils.templating import (
    fill_template,
    remove_first_snippet_from_text,
)


# ------------------------------------------------------------------
# remove_first_snippet_from_text
# ------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, snippet, expected",
    [
        # ---- None / empty handling ----
        (None, "x", ""),
        ("", "x", ""),
        ("text", None, "text"),
        ("text", "", "text"),
        # ---- Snippet not found / whole-string removal ----
        ("hello world", "missing", "hello world"),
        ("exact", "exact", ""),
        # ---- Basic removals ----
        ("hello world", "world", "hello "),
        ("hello world", "hello", " world"),
        ("hello world", "lo wo", "helrld"),
        # ---- Only first occurrence removed (no whitespace cleanup) ----
        ("abc abc abc", "abc", " abc abc"),
        # ---- Special characters (no regex semantics) ----
        ("a[b]c a[b]c", "a[b]c", " a[b]c"),
        # ---- Newlines / multiline snippets (no whitespace cleanup) ----
        ("A\nB\nC", "B\n", "A\nC"),
        ("start\nMID\nend", "start\nMID\n", "end"),
        # removal may concatenate characters; function does not insert spaces
        ("A \n  B \n C", " \n  B \n ", "AC"),
        ("line1\nline2\nline3", "line2\n", "line1\nline3"),
    ],
)
def test_remove_first_snippet_from_text(text, snippet, expected):
    assert remove_first_snippet_from_text(text, snippet) == expected


# ------------------------------------------------------------------
# fill_template
# ------------------------------------------------------------------


@pytest.mark.parametrize(
    "template, placeholders, expected",
    [
        # ---- No placeholders ----
        ("plain text", {}, "plain text"),
        # ---- Basic replacement ----
        ("Hello, {{name}}!", {"name": "Ada"}, "Hello, Ada!"),
        # ---- Whitespace inside braces is ignored ----
        ("{{ name }} {{    name   }}", {"name": "X"}, "X X"),
        # ---- Multiple placeholders ----
        ("{{a}}+{{b}}={{c}}", {"a": "1", "b": "2", "c": "3"}, "1+2=3"),
        # ---- Missing placeholder left untouched ----
        ("Hello {{name}} {{missing}}", {"name": "Ada"}, "Hello Ada {{missing}}"),
        # ---- Repeated placeholder ----
        ("{{x}}/{{x}}/{{x}}", {"x": "y"}, "y/y/y"),
        # ---- Keys treated literally (regex escaped) ----
        ("{{a.b}} {{a+b}}", {"a.b": "DOT", "a+b": "PLUS"}, "DOT PLUS"),
        # ---- Replacement value may itself look like a placeholder (not re-expanded) ----
        ("{{x}}", {"x": "{{y}}"}, "{{y}}"),
        # ---- Newlines / multiline templates ----
        (
            "Hello {{name}},\nWelcome to {{place}}.\n",
            {"name": "Ada", "place": "BioHackathon"},
            "Hello Ada,\nWelcome to BioHackathon.\n",
        ),
        (
            "BEGIN\n{{value}}\nEND",
            {"value": "MIDDLE"},
            "BEGIN\nMIDDLE\nEND",
        ),
        (
            "{{a}}\n{{b}}\n{{c}}",
            {"a": "1", "b": "2", "c": "3"},
            "1\n2\n3",
        ),
        (
            "Value:\n{{   key   }}\nDone",
            {"key": "X"},
            "Value:\nX\nDone",
        ),
        (
            "Line1\n{{missing}}\nLine3",
            {"other": "X"},
            "Line1\n{{missing}}\nLine3",
        ),
        # ---- Triple braces: inner {{name}} still matches and gets replaced ----
        ("{{{name}}}", {"name": "Ada"}, "{Ada}"),
        # ---- Backslashes in values are literal, not regex replacement escapes ----
        ("{{x}}", {"x": r'-F=".\masses.txt"'}, r'-F=".\masses.txt"'),
        ("{{x}}", {"x": r"\1"}, r"\1"),
        ("{{x}}", {"x": r"C:\new\test"}, r"C:\new\test"),
        ("{{x}}", {"x": r"\g<0>"}, r"\g<0>"),
    ],
)
def test_fill_template(template, placeholders, expected):
    assert fill_template(template, placeholders) == expected


def test_fill_template_does_not_touch_single_braces():
    template = "{name}\n{{name}}\n{{{name}}}"
    out = fill_template(template, {"name": "Ada"})
    # {name} untouched, {{name}} replaced, and triple-brace form becomes "{Ada}"
    assert out == "{name}\nAda\n{Ada}"
