"""
High-level coroutine that chains GitHubIngestor and GitHubRepoTransformer
to produce a GitHubRepoModel from owner/repo coordinates.
"""

import logging

from bridge.core import GitHubRepoModel
from bridge.services import GitHubIngestor
from bridge.utils import require_args

from .github_transformer import GitHubRepoTransformer

logger = logging.getLogger(__name__)


@require_args("owner", "repo")
async def compose_github_repo(**kwargs) -> GitHubRepoModel:
    """
    Fetch and transform GitHub repository data into a GitHubRepoModel model.

    Parameters
    ----------
    **kwargs
        Expected to contain:
        - owner : str - GitHub user or organization that owns the repository.
        - repo : str - Repository name.

    Returns
    -------
    GitHubRepoModel
        A GitHubRepoModel model representing the repository.

    Raises
    ------
    Exception
        If there is an error during ingestion or transformation.
    """
    owner = kwargs.get("owner")
    repo = kwargs.get("repo")
    logger.info(f"Composing GitHub repository model for {owner}/{repo}")
    try:
        github_ingestor = GitHubIngestor(owner, repo)
        github_transformer = GitHubRepoTransformer(github_ingestor)
        github_repo = await github_transformer.transform()
        logger.info(f"Composed GitHub repository model for {owner}/{repo} successfully")
        return github_repo
    except Exception as e:
        logger.exception(f"Error composing GitHub repository model for {owner}/{repo}: {e}")
        raise
