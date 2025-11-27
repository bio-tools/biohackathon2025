"""
Utilities for cleaning and canonicalizing objects.
"""

from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlsplit, urlunparse, urlunsplit


def canonicalize_shields_url(url: str) -> str:
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


def canonicalize_url(url: str) -> str:
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


def escape_shields_part(value: str) -> str:
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


def normalize_color(value: str) -> str:
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
