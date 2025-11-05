"""
Abstract class for mapping between repository and metadata models.
"""

import functools
import importlib
from abc import ABC, abstractmethod
from enum import Enum
from functools import partial
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator


def prepare_match_items(func: callable):
    """
    Check and normalize inputs for match methods.

    Validation rule:
    - None: returns 0 without further matching

    Normalization rules:
    - list/set/tuple: converted to set
    # TODO: handle dicts?
    """

    @functools.wraps(func)
    def wrapper(self, item1: Any, item2: Any) -> float:
        # Missing inout value
        if item1 is None or item2 is None:
            return 0.0

        def normalize(item):
            if isinstance(item, (list, set, tuple)):
                return set(item)
            else:
                return item

        item1_norm, item2_norm = normalize(item1), normalize(item2)
        return func(self, item1_norm, item2_norm)

    return wrapper


class Method(Enum):
    """
    Matching method for mapping metadata record from one platform to another (GitHub, bio.tools).
    """

    EXACT = "exact"
    SUBSET = "subset"


class ModelsMap(ABC):
    """
    Abstract class for mapping between repository and metadata models.

    Parameters
    ----------
    repo: Any
        A repository model instance.
    metadata: Any
        A metadata model instance.
    """

    def __init__(self, repo: Any, metadata: Any):
        super().__init__()
        self.repo = repo
        self.metadata = metadata

    @property
    @abstractmethod
    def map(self) -> dict[str, Any]:
        """
        Perform the mapping between repository and metadata models.

        Return
        -------
        Any
            The map representation of the models.
        """
        return


def _to_path(fn):
    if isinstance(fn, partial):
        raise TypeError("partials aren’t serializable by simple dotted path")

    mod = getattr(fn, "__module__", "")
    qn = getattr(fn, "__qualname__", "")
    if not (mod and qn):
        raise TypeError("callable lacks module/qualname")

    if mod == "__main__" or "<locals>" in qn:
        raise TypeError("callable must be a top-level, importable symbol")

    return f"{mod}:{qn}"


def _import_from_path(path: str):
    # Supports "pkg.mod:attr.nested" or "pkg.mod.attr.nested"
    sep = ":" if ":" in path else "."
    mod_path, attr = path.rsplit(sep, 1)
    mod = importlib.import_module(mod_path)
    obj = mod
    for part in attr.split("."):
        obj = getattr(obj, part)
    if not callable(obj):
        raise TypeError(f"{path!r} is not callable")
    return obj


class MapItem(BaseModel):
    """
    Map metadata property to corresponding repository metadata property and match method.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    schema_entry: Any
    repo_entry: Any
    method: Method | None
    fn: callable | None = None

    @field_validator("fn", mode="before")
    @classmethod
    def ensure_callable_or_none(cls, v):
        """
        Validate that fn is either None, a callable, or a dotted path to a callable.
        """
        if v is None:
            return None
        if isinstance(v, str):
            v = _import_from_path(v)
        if not callable(v):
            raise TypeError("fn must be None, a callable, or a dotted path to one")
        return v

    @field_serializer("fn")
    def serialize_fn(self, fn):
        """
        Serialize fn to a dotted path.
        """
        if fn is None:
            return None
        return _to_path(fn)
