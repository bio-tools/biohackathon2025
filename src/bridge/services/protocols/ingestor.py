"""
Service protocol for fetching raw external data.
"""

from typing import Any, Protocol


class Ingestor(Protocol):
    """Protocol for classes that fetch raw metadata from an external source."""

    async def fetch(self) -> dict[str, Any]:
        """Fetch raw metadata from an external source."""
        ...
