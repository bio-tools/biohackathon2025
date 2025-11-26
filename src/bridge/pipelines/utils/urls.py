"""
Utility functions for URL manipulation.
"""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


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
