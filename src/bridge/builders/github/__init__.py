"""
Composition utilities for GitHub: fetch repository data and transform it into a GitHubRepoModel.
"""

from .github_composer import compose_github_repo

__all__ = [
    "compose_github_repo",
]
