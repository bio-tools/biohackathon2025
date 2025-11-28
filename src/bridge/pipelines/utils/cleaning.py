"""
Utilities for cleaning and canonicalizing objects.

The functions are intentionally conservative: they avoid guessing semantics
and focus only on reversible, mechanical clean-ups and canonical forms that
improve comparison and stability.
"""

import html
import re
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlsplit, urlunparse, urlunsplit


def canonicalize_shields_url(url: str) -> str:
    """
    Canonicalize a shields.io image URL for stable comparison.

    This helper focuses on shields.io badge URLs served from `img.shields.io`.
    The main goal is to strip out purely cosmetic parameters that shouldn't
    affect logical equality (e.g. user-chosen logos) and to provide a stable
    query parameter ordering.

    Behaviour:
    - If the URL does *not* contain `img.shields.io`, it is returned unchanged.
    - If it does, the query string is parsed, the `logo` parameter is removed
      (case-insensitive), and the remaining parameters are sorted
      lexicographically and re-encoded.

    Parameters
    ----------
    url : str
        The shields.io URL to canonicalize.

    Returns
    -------
    str
        The canonicalized URL, suitable for equality checks or deduplication.
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
    Canonicalize a generic URL for stable comparison.

    This performs a minimal, well-defined normalization intended to make
    string-based URL comparisons less fragile without changing semantics
    for typical HTTP(S) URLs.

    Normalizations applied:
    - Lowercase the scheme and netloc (host + port).
    - Strip trailing slashes from the path, but ensure the path is at least "/".
    - Parse the query string into key/value pairs, sort them, and re-encode
      (preserving multiplicity via `doseq=True`).
    - Drop the fragment entirely (anything after '#').

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
    Prepare a label or message for use in a Shields.io badge path segment.

    Shields.io encodes meaning into certain characters in the path portion
    of the URL. This function escapes a free-form string so that it can be
    safely embedded in that position without accidentally triggering
    Shields' special syntax.

    Shields path semantics:
    - `-`  = segment separator
    - `--` = literal `-`
    - `_`  = space
    - `__` = literal `_`

    This function:
    - Converts `-` to `--`.
    - Converts `_` to `__`.
    - Percent-encodes anything else that needs escaping, but leaves `_`
      unchanged so that Shields can interpret it as a space.

    Parameters
    ----------
    value : str
        The label or message to escape.

    Returns
    -------
    str
        The escaped value, suitable for direct inclusion in a Shields.io URL
        path segment.
    """
    value = str(value)
    value = value.replace("-", "--")
    value = value.replace("_", "__")
    return quote(value, safe="_")


def normalize_color(value: str) -> str:
    """
    Normalize a color value by stripping a leading '#' and percent-encoding.

    Behaviour:
    - Coerces the value to a string and strips surrounding whitespace.
    - Removes a leading `#` if present.
    - Percent-encodes the remaining value with no safe characters.

    Parameters
    ----------
    value : str
        The color value to normalize (e.g. "#4c1", "brightgreen").

    Returns
    -------
    str
        The normalized color string, without a leading '#', and
        percent-encoded for safe use in URLs.
    """
    value = str(value).strip()
    if value.startswith("#"):
        value = value[1:]
    return quote(value, safe="")


def normalize_text(value: str | None, normalize_multiline: bool = True) -> str | None:
    """
    Clean and normalize free-text values.

    This is a general-purpose text scrubber intended to remove presentation
    artefacts (HTML entities/tags, box-drawing characters) and normalize
    whitespace so that strings are more suitable for storage, comparison,
    or inclusion in metadata formats.

    Steps performed:
    1. Decode HTML entities (e.g. ``&lt;i&gt;`` → ``<i>``, ``&amp;`` → ``&``).
    2. Strip all remaining HTML tags (e.g. ``<i>name</i>`` → ``name``).
    3. Replace the box-drawing dash ``\u2500`` with a plain ASCII ``-``.
    4. Remove non-printable characters.
    5. Optionally collapse all whitespace, including newlines, into single
       spaces (`normalize_multiline=True`).
    6. Strip leading and trailing whitespace.

    Parameters
    ----------
    value : str | None
        The text to normalize. If ``None``, the function returns ``None``.
    normalize_multiline : bool, optional
        If True (default), newlines and runs of whitespace are collapsed into
        single spaces. If False, existing line breaks are preserved and only
        non-printable characters and HTML artefacts are removed.

    Returns
    -------
    str | None
        The normalized text, or ``None`` if the input was ``None``.
    """
    if value is None:
        return None

    # decode HTML entities: &lt;i&gt; → <i>, &amp; → &, etc.
    text = html.unescape(value)

    # strip any remaining HTML tags: <i>name</i> -> name
    tag_re = re.compile(r"<[^>]+>")
    text = tag_re.sub("", text)

    # replace box-drawing dash with a normal ASCII dash
    text = text.replace("\u2500", "-")

    # drop non-printable characters
    text = "".join(c for c in text if c.isprintable())

    if normalize_multiline:
        # replace newlines and multiple spaces with a single space
        text = re.sub(r"\s+", " ", text)

    # strip outer whitespace
    return text.strip()


def _normalize_structure(obj: Any) -> Any:
    """
    Recursively normalize strings inside common container types.

    This helper is used by higher-level normalization functions to apply
    :func:`normalize_text` to all string-like values in nested structures.

    Supported types:
    - str / None: passed through `normalize_text`.
    - dict: keys left as-is, values normalized recursively.
    - list, tuple, set: elements normalized recursively, container type preserved.
    - Pydantic models: delegated to `normalize_pydantic_model_strings`.
    - Anything else: returned unchanged.

    Parameters
    ----------
    obj : Any
        Arbitrary Python object to normalize.

    Returns
    -------
    Any
        A normalized version of `obj`, with the same overall structure.
    """
    # scalar text
    if isinstance(obj, str) or obj is None:
        return normalize_text(obj)

    # dict: normalize values recursively, keep keys untouched
    if isinstance(obj, dict):
        return {k: _normalize_structure(v) for k, v in obj.items()}

    # lists: normalize each element, keep as list
    if isinstance(obj, list):
        return [_normalize_structure(v) for v in obj]

    # tuples: normalize each element, keep as tuple
    if isinstance(obj, tuple):
        return tuple(_normalize_structure(v) for v in obj)

    # sets: normalize each element, keep as set
    if isinstance(obj, set):
        return {_normalize_structure(v) for v in obj}

    # Pydantic model: normalize fields in-place, return the same object
    if hasattr(obj, "model_fields") or hasattr(obj, "__fields__"):
        return normalize_pydantic_model_strings(obj)

    return obj


def normalize_dict_strings(d: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively normalize all string-like values in a dictionary.

    This function walks the entire structure of the given dict and applies
    :func:`normalize_text` to any string or ``None`` value it encounters.

    Keys are left unchanged. Non-string scalar values (numbers, booleans, etc.)
    are preserved as-is.

    Parameters
    ----------
    d : dict[str, Any]
        The dictionary whose string values (and nested structures) should be
        normalized.

    Returns
    -------
    dict[str, Any]
        A new dictionary with the same structure as `d`, where all nested
        string/None values have been normalized.
    """
    return _normalize_structure(d)


def normalize_pydantic_model_strings(model: Any) -> Any:
    """
    Recursively normalize all string fields in a Pydantic model in-place.

    For each declared field on the model:

    - If the current value is a string or ``None``, it is passed through
      :func:`normalize_text`.
    - If the current value is a container (dict, list, tuple, set), its
      contents are normalized recursively via :func:`_normalize_structure`.
    - If the current value is another Pydantic model, it is normalized
      recursively by calling `normalize_pydantic_model_strings` on it.

    If the object does not look like a Pydantic model (i.e. has neither
    ``model_fields`` nor ``__fields__``), it is returned unchanged.

    Parameters
    ----------
    model : Any
        The Pydantic model instance to normalize, or any other object.

    Returns
    -------
    Any
        The same ``model`` object, potentially modified in-place if it is a
        Pydantic model with string fields or nested containers.
    """
    if hasattr(model, "model_fields"):
        fields = model.model_fields
    elif hasattr(model, "__fields__"):
        fields = model.__fields__
    else:
        return model

    for field_name in fields.keys():
        value = getattr(model, field_name, None)
        normalized_value = _normalize_structure(value)
        setattr(model, field_name, normalized_value)

    return model
