"""
Protocol for transformers that converts ingested raw data into a structured core model.
"""

from typing import Any, Protocol


class Transformer(Protocol):
    """Transforms raw metadata into a structured model."""

    def transform(self) -> Any:
        """Transform raw data into a structured model."""
        ...
