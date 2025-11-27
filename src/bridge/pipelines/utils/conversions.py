"""
Utility functions for converting object types.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel


def to_primitive(obj: Any) -> Any:
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
        return to_primitive(data)

    # enums
    if isinstance(obj, Enum):
        return obj.value

    # dicts
    if isinstance(obj, dict):
        return {k: to_primitive(v) for k, v in obj.items()}

    # lists / tuples / sets
    if isinstance(obj, (list, tuple, set)):
        return [to_primitive(v) for v in obj]

    # everything else is assumed to already be primitive or stringify-able
    return obj
