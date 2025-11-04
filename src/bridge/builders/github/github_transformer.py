"""
Transformer converting raw GitHub repo JSON into the generated FullRepository model.
"""

import logging

from bridge.builders.protocols import Transformer

# Adjust path to your generated models module:
from bridge.core import GitHubRepoModel
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
        logger.debug(f"Raw data keys: {list(raw_data.keys())}")
        result = GitHubRepoModel(**raw_data)
        return result
