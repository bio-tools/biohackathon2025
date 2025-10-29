"""
Pipeline package for extracting (or updating) bio.tools metadata from a GitHub repository.
"""

from .main import GitHubToBiotoolsForMetaPipelineArgs, run

__all__ = [
    "run",
    "GitHubToBiotoolsForMetaPipelineArgs",
]
