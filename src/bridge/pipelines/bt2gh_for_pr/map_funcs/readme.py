"""
Map bio.tools metadata to GitHub README, add badges.
"""

from typing import Any


def _make_shields_badge_url(
    label: str,
    message: str,
    color: str,
    logo_b64: str,
) -> str:
    """
    Construct a Shields.io badge URL with an embedded base64 SVG logo.

    Parameters
    ----------
    label : str
        The label text on the badge.
    message : str
        The message text on the badge.
    color : str
        The color of the badge.
    logo_b64 : str
        The base64-encoded SVG logo to embed in the badge.

    Returns
    -------
    str
        The complete Shields.io badge URL.
    """
    base = "https://img.shields.io/badge"
    return f"{base}/{label}-{message}-{color}?logo=data:image/svg+xml;base64,{logo_b64}"


def _make_markdown_badge(alt_text: str, badge_url: str) -> str:
    """
    Wrap a badge URL in Markdown image syntax.

    Parameters
    ----------
    alt_text : str
        The alternative text for the badge image.
    badge_url : str
        The URL of the badge image.

    Returns
    -------
    str
        The Markdown-formatted badge string.
    """
    return f"![{alt_text}]({badge_url})"


def map_readme(gh_readme: str | None, bt_params: dict[str, Any]) -> dict[str, str]:
    """
    Docstring for map_readme
    """
    if gh_readme is None:
        pass  # TODO: generate a default README
    return {"readme": gh_readme}
