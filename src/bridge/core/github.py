"""
GitHub repository Pydantic models.
"""

from pydantic import BaseModel

from .github_latest_release import GitHubLatestReleaseModel
from .github_repo import FullRepository


class GitHubRepoModel(BaseModel):
    """
    FullRepository model generated from GitHub repository schema.

    Parameters
    ----------
    repo : FullRepository
        The full repository data.
    latest_release : GitHubLatestReleaseModel | None
        The latest release data, or None if no releases exist.
    """

    repo: FullRepository
    latest_release: GitHubLatestReleaseModel | None
