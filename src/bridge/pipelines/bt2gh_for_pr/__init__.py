"""
Pipeline package for generating repository changes (PR-ready for GitHub) from bio.tools metadata.
"""

from .main import BiotoolsToGitHubForPRPipelineArgs, run

__all__ = [
    "run",
    "BiotoolsToGitHubForPRPipelineArgs",
]
