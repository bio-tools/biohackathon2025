"""
Core domain models shared across the bridge.
Re-exports validated Pydantic models for repositories and metadata.
"""

from .biotools import ToolModel as BiotoolsToolModel
from .github import GitHubRepoModel

__all__ = [
    "BiotoolsToolModel",
    "GitHubRepoModel",
]
