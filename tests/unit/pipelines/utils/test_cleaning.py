"""
Unit tests for cleaning and canonicalization utilities.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

# Adjust import to your real module path
from bridge.pipelines.utils.cleaning import (
    canonicalize_shields_url,
    canonicalize_url,
    escape_shields_part,
    normalize_color,
    normalize_dict_strings,
    normalize_pydantic_model_strings,
    normalize_text,
)


# ----------------------------
# canonicalize_shields_url
# ----------------------------


@pytest.mark.parametrize(
    "url, expected",
    [
        # Case 1: Non-shields URL is unchanged
        ("https://example.org/a?b=1&logo=x#frag", "https://example.org/a?b=1&logo=x#frag"),
        # Case 2: Shields URL removes logo (any casing) and sorts remaining params
        (
            "https://img.shields.io/badge/a-b-c.svg?b=2&logo=data:xxx&a=1",
            "https://img.shields.io/badge/a-b-c.svg?a=1&b=2",
        ),
        # Case 3: Keeps blank values, removes logo, sorts
        (
            "https://img.shields.io/badge/a-b-c.svg?x=&logo=zzz&y=1",
            "https://img.shields.io/badge/a-b-c.svg?x=&y=1",
        ),
        # Case 4: Keeps fragment
        (
            "https://img.shields.io/badge/a-b-c.svg?b=2&logo=zzz#a",
            "https://img.shields.io/badge/a-b-c.svg?b=2#a",
        ),
        # Case 5: No query params
        (
            "https://img.shields.io/badge/a-b-c.svg",
            "https://img.shields.io/badge/a-b-c.svg",
        ),
    ],
)
def test_canonicalize_shields_url(url, expected):
    assert canonicalize_shields_url(url) == expected


# ----------------------------
# canonicalize_url
# ----------------------------


@pytest.mark.parametrize(
    "url, expected",
    [
        # Case 1: Lowercase scheme+netloc, strip fragment
        (
            "HTTPS://EXAMPLE.ORG/Path#Section",
            "https://example.org/Path",
        ),
        # Case 2: Strip trailing slashes; ensure at least "/"
        (
            "https://example.org////",
            "https://example.org/",
        ),
        (
            "https://example.org/a/b///",
            "https://example.org/a/b",
        ),
        # Case 3: Sort query params
        (
            "https://example.org/a?b=2&a=1",
            "https://example.org/a?a=1&b=2",
        ),
        # Case 4: Preserve multiplicity (doseq=True) and sort pairs
        (
            "https://example.org/a?b=2&b=1&a=9",
            "https://example.org/a?a=9&b=1&b=2",
        ),
    ],
)
def test_canonicalize_url(url, expected):
    assert canonicalize_url(url) == expected


# ----------------------------
# escape_shields_part
# ----------------------------


@pytest.mark.parametrize(
    "value, expected",
    [
        # Case 1: "-" becomes "--"
        ("a-b", "a--b"),
        # Case 2: "_" becomes "__" (and remains safe, not % encoded)
        ("a_b", "a__b"),
        # Case 3: space gets percent-encoded (underscore is the “space” convention, but we do not auto-convert)
        ("a b", "a%20b"),
        # Case 4: mix of -, _, and special chars
        ("a-b_c+d", "a--b__c%2Bd"),
    ],
)
def test_escape_shields_part(value, expected):
    assert escape_shields_part(value) == expected


# ----------------------------
# normalize_color
# ----------------------------


@pytest.mark.parametrize(
    "value, expected",
    [
        # Case 1: strip leading "#"
        ("#4c1", "4c1"),
        # Case 2: strip whitespace
        ("  #00FF00  ", "00FF00"),
        # Case 3: percent-encode unsafe chars (space, etc.)
        ("bright green", "bright%20green"),
        # Case 4: already safe-ish stays as-is (no safe chars allowed, but alnum passes unchanged)
        ("blue", "blue"),
    ],
)
def test_normalize_color(value, expected):
    assert normalize_color(value) == expected


# ----------------------------
# normalize_text
# ----------------------------


@pytest.mark.parametrize(
    "value, normalize_multiline, expected",
    [
        # Case 1: None stays None
        (None, True, None),
        # Case 2: HTML entity decoding + tag stripping
        ("Hello &lt;i&gt;world&lt;/i&gt; &amp; friends", True, "Hello world & friends"),
        # Case 3: Box drawing dash -> "-"
        ("A\u2500B", True, "A-B"),
        # Case 4: drop non-printable characters
        ("A\x00B\x07C", True, "ABC"),
        # Case 5: whitespace collapsing (note: tabs/newlines are removed as non-printable before collapsing)
        (" A \n  B\t\tC ", True, "A BC"),
        # Case 6: normalize_multiline=False still removes newlines/tabs (non-printable), so line breaks are NOT preserved
        ("A\n\nB\tC", False, "ABC"),
        # Case 7: tag stripping without entity stage needed
        ("<b>Bold</b>  text", True, "Bold text"),
    ],
)
def test_normalize_text(value, normalize_multiline, expected):
    assert normalize_text(value, normalize_multiline=normalize_multiline) == expected


# ----------------------------
# normalize_dict_strings (recursive)
# ----------------------------


def test_normalize_dict_strings_recurses_through_common_containers():
    payload = {
        "a": "  Hi &amp; <i>there</i> \n",
        "b": ["A\u2500B", None, {"c": " X\tY "}],
        "c": ("<b>Z</b>",),
        "d": {"nested": {"set": {" A ", "B "}}},
        "e": 123,  # non-string untouched
        "f": True,
    }

    out = normalize_dict_strings(payload)

    assert out["a"] == "Hi & there"
    assert out["b"][0] == "A-B"
    assert out["b"][1] is None
    # tabs are removed (non-printable) before whitespace normalization
    assert out["b"][2]["c"] == "XY"
    assert out["c"][0] == "Z"
    assert out["d"]["nested"]["set"] == {"A", "B"}
    assert out["e"] == 123
    assert out["f"] is True


# ----------------------------
# normalize_pydantic_model_strings (in-place)
# ----------------------------


class _Inner(BaseModel):
    text: str | None = None


class _Outer(BaseModel):
    title: str
    inner: _Inner | None = None
    items: list[str | None] = []
    meta: dict[str, object] = {}


def test_normalize_pydantic_model_strings_normalizes_in_place():
    m = _Outer(
        title="  Hello &amp; <i>world</i> ",
        inner=_Inner(text="A\u2500B"),
        items=[" X\tY ", None],
        meta={"desc": "<b>Bold</b>\ntext", "n": 7, "inner2": _Inner(text="  Z ")},
    )

    out = normalize_pydantic_model_strings(m)

    assert out is m
    assert m.title == "Hello & world"
    assert m.inner is not None
    assert m.inner.text == "A-B"
    # tab removed -> "XY"
    assert m.items == ["XY", None]
    assert m.meta["desc"] == "Boldtext"  # newline removed as non-printable, no whitespace collapse needed
    assert m.meta["n"] == 7
    assert isinstance(m.meta["inner2"], _Inner)
    assert m.meta["inner2"].text == "Z"


def test_normalize_pydantic_model_strings_non_model_is_noop():
    obj = {"a": " <b>X</b> "}
    out = normalize_pydantic_model_strings(obj)
    assert out is obj  # unchanged object
    assert out["a"] == " <b>X</b> "  # function is not supposed to normalize non-models
