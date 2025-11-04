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
