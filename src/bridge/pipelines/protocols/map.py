"""
Abstract class for mapping between repository and metadata models.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class Method(Enum):
    """
    Matching method for mapping metadata record from one platform to another (GitHub, bio.tools).
    """

    EXACT = "exact"
    SUBSET = "subset"

    def match_exact(self, item1: Any, item2: Any):
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
        match_level = 0
        if item1 == item2:
            match_level = 1
        # TODO: else - partial matches
        return match_level

    def match_subset(self, item1, item2):
        """
        Evaluate whether one set of values is equal to the intersection of the set of values and another set of values.
        """
        # TODO: create decorator for mach methods
        match_level = 0
        if set(item1) == set(item1).intersection(set(item2)):
            match_level = 1
        return match_level


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
