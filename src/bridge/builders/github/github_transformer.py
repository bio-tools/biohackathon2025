"""
Transformer converting raw GitHub repo JSON into the generated FullRepository model.
"""

import logging

from bridge.builders.protocols import Transformer
from bridge.core import GitHubRepoModel
from bridge.core.github_languages import Language
from bridge.core.github_latest_release import Release
from bridge.core.github_pages import GitHubPages
from bridge.core.github_repo import FullRepository
from bridge.services.github import GitHubIngestor

logger = logging.getLogger(__name__)


class GitHubRepoTransformer(Transformer):
    """
    Transform raw data from GitHubIngestor into a FullRepository.
    """

    def __init__(self, ingestor: GitHubIngestor):
        self.ingestor = ingestor

    async def transform(self) -> GitHubRepoModel:
        """
        Transform raw data into a GitHubRepoModel model.

        Returns
        -------
        GitHubRepoModel
            The transformed GitHub repository model.
        """
        logger.info(f"Transforming data for repository {self.ingestor.owner}/{self.ingestor.repo}")
        raw_data = await self.ingestor.fetch()

        repo_raw_data = raw_data.get("repo", {})
        latest_release_raw_data = raw_data.get("latest_release")
        github_pages_raw_data = raw_data.get("github_pages")
        languages_raw_data = raw_data.get("languages")

        if not repo_raw_data["homepage"]:
            repo_raw_data["homepage"] = None

        latest_release_raw_data = raw_data.get("latest_release")
        result = GitHubRepoModel(
            repo=FullRepository(**repo_raw_data),
            latest_release=Release(**latest_release_raw_data) if latest_release_raw_data else None,
            github_pages=GitHubPages(**github_pages_raw_data) if github_pages_raw_data else None,
            readme=raw_data.get("readme"),
            languages=Language(**languages_raw_data) if languages_raw_data else None,
        )
        return result
