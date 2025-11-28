"""
Utilities for handling asset files in pipelines.
"""

from pydantic import BaseModel

from .cleaning import canonicalize_shields_url, canonicalize_url, escape_shields_part, normalize_color
from .conversions import svg_to_base64


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
    image_url: str
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

    def _signature(self) -> tuple[str, str | None]:
        """
        Canonical semantic identity of the badge.
        """
        img = canonicalize_shields_url(str(self.image_url))
        link = canonicalize_url(self.link_url) if self.link_url is not None else None
        return img, link

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Badge):
            return NotImplemented
        return self._signature() == other._signature()

    def __hash__(self) -> int:
        return hash(self._signature())


def _make_shields_badge_url(
    label: str,
    message: str,
    color: str,  # right side
    label_color: str,  # left side
    logo_b64: str | None = None,
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
    label_color : str
        The color of the label side of the badge.
    logo_b64 : str
        The base64-encoded SVG logo to embed in the badge.

    Returns
    -------
    str
        The complete Shields.io badge URL.
    """
    base = "https://img.shields.io/badge"

    label_enc = escape_shields_part(label)
    message_enc = escape_shields_part(message)
    color_enc = normalize_color(color)

    label_color_enc = normalize_color(label_color)
    url = f"{base}/{label_enc}-{message_enc}-{color_enc}.svg?labelColor={label_color_enc}"

    if logo_b64 is not None:
        # Shields docs: data:image/svg%2bxml;base64,<BASE64>
        mime_enc = "image/svg%2bxml"
        logo_param = f"data:{mime_enc};base64,{logo_b64}"
        url += f"&logo={logo_param}"

    return url


def compose_badge(
    label: str,
    message: str,
    color: str,
    label_color: str,
    alt_text: str,
    url: str | None = None,
    svg_path: str | None = None,
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
    label_color : str
        The color of the label side of the badge.
    alt_text : str
        The alternative text for the badge image.
    url : str | None
        The URL to link to when the badge is clicked.
        If None, the badge will link to the image itself.
    svg_path : str | None
        Path to the SVG file to embed as the logo.

    Returns
    -------
    Badge
        The constructed Badge object.
    """
    logo_b64 = svg_to_base64(svg_path) if svg_path is not None else None
    badge_url = _make_shields_badge_url(
        label=label,
        message=message,
        color=color,
        label_color=label_color,
        logo_b64=logo_b64,
    )
    badge = Badge(
        alt_text=alt_text,
        image_url=badge_url,
        link_url=url,
    )
    badge.full_match = badge.as_markdown()
    return badge
