"""
GitHub repository Pydantic models.
"""

from pydantic import BaseModel

from bridge.core.github_pages import GithubPages

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
    github_pages : GithubPages | None
        The GitHub Pages data, or None if not available.
    readme : str | None
        The README content of the repository, or None if not available.
    """

    repo: FullRepository
    latest_release: Release | None
    github_pages: GithubPages | None
    readme: str | None
