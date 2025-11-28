"""
Utilities for constructing and handling badge assets (e.g. Shields.io badges).
"""

from pydantic import BaseModel

from .cleaning import canonicalize_shields_url, canonicalize_url, escape_shields_part, normalize_color
from .conversions import svg_to_base64


class Badge(BaseModel):
    """
    Representation of a README badge and its Markdown rendering.

    Two `Badge` instances are considered equal if their *canonical* image URL
    and link URL match, irrespective of superficial formatting differences in
    the original Markdown.

    Parameters
    ----------
    alt_text : str
        The alternative text for the badge image (used in the Markdown `alt`
        field and as a textual fallback).
    image_url : str
        The URL of the badge image (e.g. a Shields.io badge endpoint).
    link_url : str | None
        The URL to link to when the badge is clicked. If ``None``, the badge
        will be rendered as an image without a surrounding link.
    full_match : str | None
        The original Markdown string representing the badge, if this `Badge`
        was created from a parsed README. When set, `as_markdown()` will return
        this exact string, preserving original formatting.
    """

    alt_text: str
    image_url: str
    link_url: str | None = None
    full_match: str | None = None

    def as_markdown(self) -> str:
        """
        Render the badge as a Markdown-formatted string.

        If `full_match` is set (e.g. when this badge came from a parsed
        README), that original Markdown string is returned verbatim. This
        preserves existing formatting and parameter ordering, even if internal
        fields were canonicalized.

        Otherwise, a canonical Markdown representation is generated:

        - If `link_url` is not ``None``:

          ``[![alt_text](image_url)](link_url)``

        - If `link_url` is ``None``:

          ``![alt_text](image_url)``

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
        Compute a canonical identity for the badge.

        The signature is a tuple of:

        - a canonicalized Shields.io image URL, and
        - a canonicalized link URL (or ``None``).

        Returns
        -------
        tuple[str, str | None]
            The canonical `(image_url, link_url)` pair used for equality and
            hashing.
        """
        img = canonicalize_shields_url(str(self.image_url))
        link = canonicalize_url(self.link_url) if self.link_url is not None else None
        return img, link

    def __eq__(self, other: object) -> bool:
        """
        Compare two badges for semantic equality.

        Badges are considered equal if their canonical image and link URLs
        match, regardless of how they were originally written in Markdown.

        Parameters
        ----------
        other : object
            The object to compare with.

        Returns
        -------
        bool
            ``True`` if the badges are semantically equivalent, otherwise
            ``False``.
        """
        if not isinstance(other, Badge):
            return NotImplemented
        return self._signature() == other._signature()

    def __hash__(self) -> int:
        """
        Compute a hash based on the badge's canonical identity.

        Returns
        -------
        int
            The hash value for the badge.
        """
        return hash(self._signature())


def _make_shields_badge_url(
    label: str,
    message: str,
    color: str,  # right side
    label_color: str,  # left side
    logo_b64: str | None = None,
) -> str:
    """
    Construct a Shields.io badge URL, optionally embedding a base64 SVG logo.

    This helper builds a URL for the static Shields.io endpoint:

        ``https://img.shields.io/badge/<label>-<message>-<color>.svg``

    and attaches additional query parameters:

    - ``labelColor`` to control the left-side (label) background.
    - ``logo=<data URI>`` to embed a base64-encoded SVG logo, if provided.

    The `label` and `message` are escaped to be safe in Shields.io URLs (e.g.
    spaces, dashes, and special characters). Colors are normalized to a form
    accepted by Shields (hex colors or named colors).

    Parameters
    ----------
    label : str
        The text shown on the left-hand side of the badge.
    message : str
        The text shown on the right-hand side of the badge.
    color : str
        The color for the right-hand side of the badge (e.g. hex or named
        color).
    label_color : str
        The color for the label side of the badge (left-hand side).
    logo_b64 : str | None, optional
        Base64-encoded SVG content to embed as the Shields.io logo. If
        ``None``, no logo parameter is added.

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
    Construct a `Badge` with a Shields.io URL and optional embedded SVG logo.

    This high-level helper:

    1. Optionally reads an SVG file from `svg_path` and encodes it as base64.
    2. Builds a Shields.io badge URL with `label`, `message`, `color`,
       `label_color`, and the embedded logo (if any).
    3. Instantiates a `Badge` with `alt_text`, the generated `image_url`,
       and an optional `link_url`.
    4. Pre-populates the `full_match` field with the Markdown representation
       of the badge, so that `as_markdown()` returns a ready-to-use snippet.

    Parameters
    ----------
    label : str
        The text shown on the left-hand side of the badge.
    message : str
        The text shown on the right-hand side of the badge.
    color : str
        The color for the right-hand side of the badge (e.g. hex or named).
    label_color : str
        The color for the label side (left-hand side) of the badge.
    alt_text : str
        The alternative text for the badge image (used as the `alt` attribute
        in Markdown).
    url : str | None, optional
        The URL to link to when the badge is clicked. If ``None``, the badge
        is rendered as a plain image without a link.
    svg_path : str | None, optional
        Filesystem path to an SVG file to embed as a logo in the badge. If
        ``None``, no logo is embedded.

    Returns
    -------
    Badge
        A fully constructed `Badge` instance with `image_url` pointing to a
        Shields.io badge URL and `full_match` containing the Markdown snippet.
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
