"""
Utility functions for URL manipulation.
"""

from urllib.parse import parse_qsl, urlencode, urlparse, urlsplit, urlunparse, urlunsplit


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
