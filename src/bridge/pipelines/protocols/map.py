"""
Abstract class for mapping between repository and metadata models.
"""

from abc import ABC, abstractmethod
from typing import Any


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
    def map(self) -> Any:
        """
        Perform the mapping between repository and metadata models.

        Return
        -------
        Any
            The map representation of the models.
        """
        return
