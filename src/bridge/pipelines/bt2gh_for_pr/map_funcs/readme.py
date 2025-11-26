"""
Map bio.tools metadata to GitHub README, add badges.
"""

from typing import Any

from bridge.pipelines.utils import fill_template, svg_to_base64

BRIDGE_BADGE_LOGO_PATH = "assets/logos/bridge.svg"


def _readme_top_template() -> str:
    """
    Template for the top section of the README.

    Returns
    -------
    str
        The README top section template.
    """
    return """\
{{ TITLE }}

{{ BADGES }}
"""


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


def _make_markdown_badge(alt_text: str, badge_url: str, url: str) -> str:
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
    return f"[![{alt_text}]({badge_url})]({url})"


def _compore_markdown_badge(
    label: str,
    message: str,
    color: str,
    svg_path: str,
    alt_text: str,
    url: str,
):
    """
    Create a Markdown badge with an embedded SVG logo.

    Parameters
    ----------
    label : str
        The label text on the badge.
    message : str
        The message text on the badge.
    color : str
        The color of the badge.
    svg_path : str
        The file path to the SVG logo.
    alt_text : str
        The alternative text for the badge image.
    url : str
        The URL to link to when the badge is clicked.

    Returns
    -------
    str
        The Markdown-formatted badge string.
    """
    logo_b64 = svg_to_base64(svg_path)
    badge_url = _make_shields_badge_url(
        label=label,
        message=message,
        color=color,
        logo_b64=logo_b64,
    )
    return _make_markdown_badge(
        alt_text=alt_text,
        badge_url=badge_url,
        url=url,
    )


def _build_top_content(gh_readme: str | None) -> str:
    bridge_badge = _compore_markdown_badge(
        label="bridge",
        message="bio.tools → github",
        color="orange",
        svg_path=BRIDGE_BADGE_LOGO_PATH,
        alt_text="Bridge",
        url="https://bio-tools.github.io/biohackathon2025/",
    )

    placeholders = {
        "TITLE": gh_readme if gh_readme is not None else "# Project Title",
        "BADGES": bridge_badge,
    }

    return fill_template(_readme_top_template(), placeholders)


def map_readme(gh_readme: str | None, bt_params: dict[str, Any]) -> dict[str, str]:
    """
    Docstring for map_readme
    """
    if gh_readme is None:
        pass  # TODO: generate a default README
    return {"readme": gh_readme}
