"""
Abstract class for mapping between repository and metadata models.
"""

import importlib
from abc import ABC, abstractmethod
from enum import Enum
from functools import partial
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator


class Method(Enum):
    """
    Matching method for mapping metadata record from one platform to another (GitHub, bio.tools).
    """

    EXACT = "exact"
    SUBSET = "subset"
    FUZZY = "fuzzy"


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

    def run(self) -> Any:
        """
        Run the mapping function if provided, otherwise return None.

        Return
        -------
        Any
            The result of the mapping function or None.
        """
        if self.fn is not None:
            return self.fn(self.repo_entry, self.schema_entry)
        return None
