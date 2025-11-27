"""
Utility functions for converting object types.
"""

import base64
import re
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def svg_to_base64(svg_path: str) -> str:
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


def object_to_primitive(obj: Any) -> Any:
    """
    Recursively convert Pydantic models and other custom types to plain Python types.

    Parameters
    ----------
    obj : Any
        The object to convert.

    Returns
    -------
    Any
        The converted object with only primitive types (dicts, lists, strings, numbers, booleans, None).
    """
    # Pydantic models
    if isinstance(obj, BaseModel):
        # v2
        if hasattr(obj, "model_dump"):
            data = obj.model_dump(mode="python", exclude_none=True)
        else:  # v1 fallback
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
