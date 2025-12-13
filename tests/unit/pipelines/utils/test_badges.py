"""
Unit tests for badge utilities (Shields.io badge URL construction and Badge model).
"""

import pytest

# Adjust this import path to where your module actually lives.
# Example assumes: bridge/pipelines/utils/badges.py
import bridge.pipelines.utils.badges as badges_mod


# ----------------------------
# Badge.as_markdown tests
# ----------------------------


@pytest.mark.parametrize(
    "alt_text, image_url, link_url, full_match, expected",
    [
        # Case 1: full_match overrides everything
        ("Alt", "https://img", "https://link", "[![X](Y)](Z)", "[![X](Y)](Z)"),
        # Case 2: linked badge (canonical render)
        ("Alt", "https://img", "https://link", None, "[![Alt](https://img)](https://link)"),
        # Case 3: image-only badge
        ("Alt", "https://img", None, None, "![Alt](https://img)"),
    ],
)
def test_badge_as_markdown(alt_text, image_url, link_url, full_match, expected):
    b = badges_mod.Badge(alt_text=alt_text, image_url=image_url, link_url=link_url, full_match=full_match)
    assert b.as_markdown() == expected


# ----------------------------
# Badge equality / hashing tests
# ----------------------------


def test_badge_equality_uses_canonical_signatures(monkeypatch):
    """
    Badges should be equal if canonicalized image_url and link_url match.
    We monkeypatch canonicalizers so the test is stable and doesn't depend
    on URL normalization details.
    """

    def fake_canon_shields(url: str) -> str:
        # pretend shields URL canonicalization only lowercases
        return url.lower()

    def fake_canon_url(url: str | None) -> str | None:
        return url.lower() if url is not None else None

    monkeypatch.setattr(badges_mod, "canonicalize_shields_url", fake_canon_shields)
    monkeypatch.setattr(badges_mod, "canonicalize_url", fake_canon_url)

    a = badges_mod.Badge(
        alt_text="A",
        image_url="HTTPS://IMG.SHIELDS.IO/badge/X-Y-Z.svg?labelColor=ABC",
        link_url="HTTPS://EXAMPLE.ORG/Docs/",
    )
    b = badges_mod.Badge(
        alt_text="B",
        image_url="https://img.shields.io/badge/x-y-z.svg?labelColor=abc",
        link_url="https://example.org/docs/",
    )

    assert a == b
    assert hash(a) == hash(b)

    s = {a}
    assert b in s  # hashing consistent with equality


def test_badge_not_equal_when_link_differs(monkeypatch):
    monkeypatch.setattr(badges_mod, "canonicalize_shields_url", lambda u: u.lower())
    monkeypatch.setattr(badges_mod, "canonicalize_url", lambda u: u.lower() if u else None)

    a = badges_mod.Badge(alt_text="A", image_url="https://img", link_url="https://a")
    b = badges_mod.Badge(alt_text="B", image_url="https://img", link_url="https://b")
    assert a != b


def test_badge_eq_with_non_badge_returns_notimplemented():
    b = badges_mod.Badge(alt_text="A", image_url="https://img")
    assert b.__eq__("not-a-badge") is NotImplemented


# ----------------------------
# _make_shields_badge_url tests
# ----------------------------


@pytest.mark.parametrize(
    "label, message, color, label_color, logo_b64, expected_contains, expected_not_contains",
    [
        # Case 1: no logo -> has labelColor, no logo param
        (
            "My Tool",
            "v1.2.3",
            "blue",
            "gray",
            None,
            [
                "https://img.shields.io/badge/",
                ".svg?labelColor=",
            ],
            ["&logo=data:"],
        ),
        # Case 2: logo -> contains properly formatted data URI param
        (
            "My Tool",
            "v1.2.3",
            "#00FF00",
            "#111111",
            "BASE64SVG==",
            [
                "https://img.shields.io/badge/",
                ".svg?labelColor=",
                "&logo=data:image/svg%2bxml;base64,BASE64SVG==",
            ],
            [],
        ),
    ],
)
def test_make_shields_badge_url(
    monkeypatch, label, message, color, label_color, logo_b64, expected_contains, expected_not_contains
):
    """
    We monkeypatch the escaping/normalization helpers to make the output deterministic.
    """
    monkeypatch.setattr(badges_mod, "escape_shields_part", lambda s: s.replace(" ", "_"))
    monkeypatch.setattr(badges_mod, "normalize_color", lambda c: c.lstrip("#").lower())

    url = badges_mod._make_shields_badge_url(
        label=label,
        message=message,
        color=color,
        label_color=label_color,
        logo_b64=logo_b64,
    )

    # Basic structure checks
    for needle in expected_contains:
        assert needle in url
    for needle in expected_not_contains:
        assert needle not in url

    # Ensure label/message escaping and color normalization are used
    assert "My_Tool" in url
    assert "v1.2.3" in url
    assert "00ff00" in url or "blue" in url  # depends on case
    assert "labelColor=" in url


# ----------------------------
# compose_badge tests
# ----------------------------


def test_compose_badge_without_svg_sets_full_match_and_returns_badge(monkeypatch):
    """
    compose_badge should:
      - build shields URL via _make_shields_badge_url
      - construct Badge(alt_text, image_url, link_url)
      - set full_match to the markdown representation
    """
    monkeypatch.setattr(
        badges_mod, "_make_shields_badge_url", lambda **kwargs: "https://img.shields.io/badge/X-Y-Z.svg"
    )
    # If svg_path is None, svg_to_base64 shouldn't be called; but we patch anyway to be safe.
    monkeypatch.setattr(badges_mod, "svg_to_base64", lambda _p: "SHOULD_NOT_BE_USED")

    badge = badges_mod.compose_badge(
        label="X",
        message="Y",
        color="Z",
        label_color="W",
        alt_text="ALT",
        url="https://example.org",
        svg_path=None,
    )

    assert isinstance(badge, badges_mod.Badge)
    assert badge.alt_text == "ALT"
    assert badge.image_url == "https://img.shields.io/badge/X-Y-Z.svg"
    assert badge.link_url == "https://example.org"

    # full_match should be precomputed markdown
    assert badge.full_match == "[![ALT](https://img.shields.io/badge/X-Y-Z.svg)](https://example.org)"
    assert badge.as_markdown() == badge.full_match  # returns verbatim when full_match is set


def test_compose_badge_with_svg_embeds_logo(monkeypatch):
    """
    compose_badge should call svg_to_base64 when svg_path is provided and pass
    the resulting base64 into _make_shields_badge_url.
    """
    captured = {}

    def fake_svg_to_base64(path: str) -> str:
        assert path == "logo.svg"
        return "B64=="

    def fake_make_url(**kwargs):
        captured.update(kwargs)
        return "https://img.shields.io/badge/with-logo.svg?labelColor=fff&logo=data:image/svg%2bxml;base64,B64=="

    monkeypatch.setattr(badges_mod, "svg_to_base64", fake_svg_to_base64)
    monkeypatch.setattr(badges_mod, "_make_shields_badge_url", fake_make_url)

    badge = badges_mod.compose_badge(
        label="Tool",
        message="ok",
        color="green",
        label_color="fff",
        alt_text="Alt",
        url=None,
        svg_path="logo.svg",
    )

    assert captured["logo_b64"] == "B64=="
    assert badge.link_url is None
    assert badge.image_url.startswith("https://img.shields.io/badge/with-logo.svg")

    # full_match should be image-only markdown if no link_url
    assert badge.full_match == "![Alt](" + badge.image_url + ")"
    assert badge.as_markdown() == badge.full_match
