"""
Abstract class for mapping between repository and metadata models.
"""

import functools
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel


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

    @prepare_match_items
    def match_exact(self, item1: Any, item2: Any) -> float:
        """
        Evaluate whether or not match is exact.

        Parameters
        ----------
        item1 : Any
            Value of a metadata record property from either bio.tools or GitHub.
        item1 : Any
            Value of corresponding property in metadata record form other platform.

        Returns
        -------
        float
            0 means no match, 1 means perfect match
        """
        return 1.0 if item1 == item2 else 0.0

    @prepare_match_items
    def match_subset(self, item1: Any, item2: Any) -> float:
        """
        Evaluate whether one set of values is equal to the intersection of the set of values and another set of values.
        """
        return 1.0 if item1 == item1.intersection(item2) else 0.0


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


class MapItem(BaseModel):
    """
    Map metadata property to corresponding repository metadata property and match method.
    """

    schema_entry: Any
    repo_entry: Any
    method: Method | None
