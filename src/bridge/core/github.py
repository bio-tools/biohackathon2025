"""
GitHub repository Pydantic models.
"""

from pydantic import BaseModel

from .github_latest_release import Release
from .github_repo import FullRepository


class GitHubRepoModel(BaseModel):
    """
    Represent a GitHub repository with its latest release.

    Parameters
    ----------
    repo : FullRepository
        The full repository data.
    latest_release : GitHubLatestReleaseModel | None
        The latest release data, or None if no releases exist.
    readme : str | None
        The README content of the repository, or None if not available.
    """

    repo: FullRepository
    latest_release: Release | None
    readme: str | None
