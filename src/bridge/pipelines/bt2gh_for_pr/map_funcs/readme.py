"""
Map bio.tools metadata to GitHub README, add badges.
"""

import re
from typing import Any

from pydantic import BaseModel, HttpUrl

from bridge.pipelines.utils import fill_template, svg_to_base64

BRIDGE_BADGE_LOGO_PATH = "assets/logos/bridge.svg"
BADGE_PATTERN = re.compile(
    r"""
    \[
        !\[(?P<alt1>[^\]]*)\]
        \((?P<img1>[^)]+)\)
    \]
    \((?P<link1>[^)]+)\)
    |
    !\[(?P<alt2>[^\]]*)\]
    \((?P<img2>[^)]+)\)
    """,
    re.VERBOSE,
)
README_TOP_TEMPLATE = """\
{{ TITLE }}

{{ BADGES }}
"""


class Badge(BaseModel):
    """
    Representation of a badge in the README.

    Parameters
    ----------
    alt_text : str
        The alternative text for the badge image.
    image_url : HttpUrl
        The URL of the badge image.
    link_url : str | None
        The URL to link to when the badge is clicked.
    full_match : str
        The full Markdown string representing the badge.
    """

    alt_text: str
    image_url: HttpUrl
    link_url: str | None = None
    full_match: str | None = None

    def as_markdown(self) -> str:
        """
        Return the badge as a Markdown-formatted string.

        Returns
        -------
        str
            The Markdown representation of the badge.
        """
        if self.full_match is not None:
            return self.full_match
        if self.link_url is not None:
            return f"[![{self.alt_text}]({self.image_url})]({self.link_url})"
        else:
            return f"![{self.alt_text}]({self.image_url})"


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


def _compose_badge_with_svg(
    label: str,
    message: str,
    color: str,
    svg_path: str,
    alt_text: str,
    url: str,
) -> Badge:
    """
    Create a badge with an embedded SVG logo.

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
    Badge
        The constructed Badge object.
    """
    logo_b64 = svg_to_base64(svg_path)
    badge_url = _make_shields_badge_url(
        label=label,
        message=message,
        color=color,
        logo_b64=logo_b64,
    )
    badge = Badge(
        alt_text=alt_text,
        image_url=badge_url,
        link_url=url,
    )
    badge.full_match = badge.as_markdown()
    return badge


def _extract_existing_badges(gh_readme: str | None) -> list[Badge]:
    badges: list[Badge] = []

    for match in BADGE_PATTERN.finditer(gh_readme or ""):
        if match.group("alt1") is not None:
            alt = match.group("alt1").strip()
            img = match.group("img1").strip()
            link = match.group("link1").strip()
        else:
            alt = match.group("alt2").strip()
            img = match.group("img2").strip()
            link = None

        try:
            badge = Badge(
                alt_text=alt,
                image_url=img,
                link_url=link,
                full_match=match.group(0),
            )
        except Exception:
            # invalid URL or malformed badge, skip
            continue

        badges.append(badge)

    return badges


def _build_top_content(gh_readme: str | None) -> str:
    bridge_badge = _compose_badge_with_svg(
        label="bridge",
        message="bio.tools → github",
        color="orange",
        svg_path=BRIDGE_BADGE_LOGO_PATH,
        alt_text="Bridge",
        url="https://bio-tools.github.io/biohackathon2025/",
    )

    _extract_existing_badges(gh_readme)

    placeholders = {
        "TITLE": gh_readme if gh_readme is not None else "# Project Title",
        "BADGES": bridge_badge,
    }

    return fill_template(README_TOP_TEMPLATE, placeholders)


def map_readme(gh_readme: str | None, bt_params: dict[str, Any]) -> dict[str, str]:
    """
    Docstring for map_readme
    """
    if gh_readme is None:
        pass  # TODO: generate a default README
    return {"readme": gh_readme}
