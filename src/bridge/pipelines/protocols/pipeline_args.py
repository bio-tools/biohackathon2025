"""
Base Pydantic class for pipeline arguments to keep inputs predictable.
"""

from pydantic import BaseModel, ConfigDict


class PipelineArgs(BaseModel):
    """Base class for pipeline argument models."""

    model_config = ConfigDict(extra="ignore")
