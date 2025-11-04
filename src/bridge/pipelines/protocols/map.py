"""Abstract class for mapping."""

from abc import ABC, abstractmethod
from typing import Any


class ModelsMap(ABC):
    """
    Abstract class for mapping.

    Parameters
    ----------
    repo: Any
        TODO
    metadata: Any
        TODO
    """

    def __init__(self, repo: Any, metadata: Any):
        super().__init__()
        self.repo = repo
        self.metadata = metadata

    @property
    @abstractmethod
    def map(self) -> Any:
        """
        Blah

        Return
        -------
        Any
            Blah.
        """
        return
