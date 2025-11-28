"""
Utility functions for converting object types and preparing them for serialization.

This module provides small, focused helpers that are useful when generating
artifacts such as YAML, JSON, or Markdown documents from richer Python objects.
"""

import base64
import re
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

E = TypeVar("E", bound=Enum)


def find_matching_enum_member[E: Enum](
    value: str,
    enum_cls: type[E],
) -> E | None:
    """
    Resolve a free-text string to a member of a given Enum via
    case-insensitive matching on both member `.value` and `.name`.

    The input is matched against:
      1. `str(member.value)` (primary match target)
      2. `member.name` (fallback match target)

    Matching is performed in a case-insensitive manner. No fuzzy matching,
    partial matching, or alias expansion is applied.

    Parameters
    ----------
    value : str
        Free-text input to be normalized.
    enum_cls : type[E]
        The Enum class to match against.

    Returns
    -------
    E | None
        The matching Enum member if an exact case-insensitive match is found
        against either `.value` or `.name`; otherwise ``None``.

    Notes
    -----
    - This function assumes Enum values are string-like or safely castable
      to `str`.
    - If multiple Enum members share the same normalized value, the first
      match in definition order is returned.
    """
    value_lower = value.lower()

    for member in enum_cls:
        if str(member.value).lower() == value_lower or member.name.lower() == value_lower:
            return member

    return None


def svg_to_base64(svg_path: str) -> str:
    """
    Convert an SVG file into a cleaned, base64-encoded string.

    This helper is intended for scenarios where an SVG needs to be embedded
    directly into another format (e.g. HTML `img` tags with data URIs,
    Markdown, or JSON/YAML configuration files) rather than referenced by
    filesystem path.

    Parameters
    ----------
    svg_path : str
        Path to the SVG file on disk.

    Returns
    -------
    str
        A base64-encoded string representing the cleaned SVG content. The
        resulting string contains only ASCII characters and no newlines, and
        can be safely used in data URIs such as::

            f"data:image/svg+xml;base64,{svg_to_base64('icon.svg')}"

    Raises
    ------
    FileNotFoundError
        If the SVG file does not exist at the given path.
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


def object_to_primitive(obj: Any) -> Any:
    """
    Recursively convert complex objects into plain Python types.

    This function walks an arbitrary Python object and produces a structure
    composed only of "primitive" container-friendly types:

    - ``dict`` with primitive values
    - ``list`` of primitive values
    - ``str``, ``int``, ``float``, ``bool``, or ``None``

    It is useful before serializing data to JSON, YAML, or other
    text-based formats where custom classes (e.g. Pydantic models, enums)
    would otherwise introduce unwanted artifacts or non-serializable types.

    Conversion rules
    ----------------
    - **Pydantic models**:
      - For v2 models, ``model_dump(mode="python", exclude_none=True)`` is used.
      - For v1 models, ``dict(exclude_none=True)`` is used.
      - The resulting dict is then processed recursively.

    - **Enum instances**:
      - Replaced with their ``.value``.

    - **Mappings / dicts**:
      - Keys are left as-is, values are passed through ``object_to_primitive``
        recursively.

    - **Iterables (list, tuple, set)**:
      - Converted to a ``list`` with each element converted recursively.

    - **Anything else**:
      - Returned unchanged, under the assumption that it is already a primitive
        type or is otherwise safely serializable.

    Parameters
    ----------
    obj : Any
        The object (or nested structure of objects) to convert.

    Returns
    -------
    Any
        A recursively converted object that only contains primitive types and
        containers thereof.
    """
    # Pydantic models
    if isinstance(obj, BaseModel):
        if hasattr(obj, "model_dump"):
            data = obj.model_dump(mode="python", exclude_none=True)
        else:
            data = obj.dict(exclude_none=True)
        return object_to_primitive(data)

    # enums
    if isinstance(obj, Enum):
        return obj.value

    # dicts
    if isinstance(obj, dict):
        return {k: object_to_primitive(v) for k, v in obj.items()}

    # lists / tuples / sets
    if isinstance(obj, (list, tuple, set)):
        return [object_to_primitive(v) for v in obj]

    # everything else is assumed to already be primitive or stringify-able
    return obj
