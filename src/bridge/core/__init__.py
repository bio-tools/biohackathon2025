"""
Core domain models shared across the bridge.
Re-exports validated Pydantic models for repositories and metadata.
"""

from .biotools import ToolModel as BiotoolsToolModel
from .github import GitHubRepoModel
from .license import SPDXLicense
from .publication import Publication

__all__ = [
    "BiotoolsToolModel",
    "GitHubRepoModel",
    "Publication",
    "SPDXLicense",
]
