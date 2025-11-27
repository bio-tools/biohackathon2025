"""
Utilities for handling asset files in pipelines.
"""

import base64
import re
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlsplit, urlunparse, urlunsplit

from pydantic import BaseModel


def _canonicalize_shields_url(url: str) -> str:
    """
    Canonicalize a shields.io URL by removing the "logo" query parameter.

    Parameters
    ----------
    url : str
        The shields.io URL to canonicalize.

    Returns
    -------
    str
        The canonicalized URL.
    """
    if "img.shields.io" not in url:
        return url

    parts = urlsplit(url)
    # parse query params, drop any "logo" parameter, sort rest for stability
    q_pairs = parse_qsl(parts.query, keep_blank_values=True)
    q_pairs = [(k, v) for (k, v) in q_pairs if k.lower() != "logo"]
    q_pairs.sort()
    new_query = urlencode(q_pairs)

    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def _canonicalize_url(url: str) -> str:
    """
    Canonicalize a URL by normalizing its components.

    Parameters
    ----------
    url : str
        The URL to canonicalize.

    Returns
    -------
    str
        The canonicalized URL.
    """
    parsed = urlparse(url)

    query = urlencode(sorted(parse_qsl(parsed.query)), doseq=True)
    path = parsed.path.rstrip("/") or "/"

    return urlunparse(
        parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
            path=path,
            query=query,
            fragment="",
        )
    )


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
        img = _canonicalize_shields_url(str(self.image_url))
        link = _canonicalize_url(self.link_url) if self.link_url is not None else None
        return img, link

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Badge):
            return NotImplemented
        return self._signature() == other._signature()

    def __hash__(self) -> int:
        return hash(self._signature())


def _escape_shields_part(value: str) -> str:
    """
    Prepare label/message for the Shields path segment.

    Shields semantics:
    - `-`  = separator
    - `--` = literal `-`
    - `_`  = space
    - `__` = literal `_`
    """
    value = str(value)
    value = value.replace("-", "--")
    value = value.replace("_", "__")
    return quote(value, safe="_")


def _normalize_color(value: str) -> str:
    """
    Normalize a color for Shields:
    - Strip leading '#' if present.
    - Percent-encode anything weird.

    Parameters
    ----------
    value : str
        The color value to normalize.

    Returns
    -------
    str
        The normalized color string.
    """
    value = str(value).strip()
    if value.startswith("#"):
        value = value[1:]
    return quote(value, safe="")


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

    label_enc = _escape_shields_part(label)
    message_enc = _escape_shields_part(message)
    color_enc = _normalize_color(color)

    label_color_enc = _normalize_color(label_color)
    url = f"{base}/{label_enc}-{message_enc}-{color_enc}.svg?labelColor={label_color_enc}"

    if logo_b64 is not None:
        # Shields docs: data:image/svg%2bxml;base64,<BASE64>
        mime_enc = "image/svg%2bxml"
        logo_param = f"data:{mime_enc};base64,{logo_b64}"
        url += f"&logo={logo_param}"

    return url


def _svg_to_base64(svg_path: str) -> str:
    """
    Convert an SVG file to a base64-encoded string.

    Parameters
    ----------
    svg_path : str
        Path to the SVG file.

    Returns
    -------
    str
        Base64-encoded string of the SVG content.

    Raises
    ------
    FileNotFoundError
        If the SVG file does not exist.
    """
    svg_path = Path(svg_path)
    if not svg_path.exists():
        raise FileNotFoundError(f"SVG file not found: {svg_path}")

    text = svg_path.read_text(encoding="utf-8")

    # remove XML declaration if present
    text = re.sub(r"^<\?xml[^>]*\?>\s*", "", text, flags=re.IGNORECASE)

    # strip comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # collapse trivial whitespace between tags
    text = re.sub(r">\s+<", "><", text).strip()

    encoded_svg = base64.b64encode(text.encode("utf-8")).decode("ascii").replace("\n", "")
    return encoded_svg


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
    logo_b64 = _svg_to_base64(svg_path) if svg_path is not None else None
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
