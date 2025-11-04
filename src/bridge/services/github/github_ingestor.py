"""
Async client for the GitHub API.
Fetches a repository and returns the raw JSON (single call).
"""

import logging
from typing import Any

import httpx

from bridge.config import settings
from bridge.services.protocols import Ingestor

from .github_auth import get_github_headers

logger = logging.getLogger(__name__)


class GitHubIngestor(Ingestor):
    """
    Ingest GitHub repository metadata via the GitHub REST API (raw JSON).
    """

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def _get(self, url: str, *, params: dict | None = None, headers: dict | None = None) -> dict[str, Any]:
        # Ask for topics in the repo payload as well (mercy preview still matters in practice).
        base_headers = get_github_headers()
        want_topics = "application/vnd.github.mercy-preview+json"
        accept = base_headers.get("Accept", "application/vnd.github+json")
        merged = {**base_headers, **(headers or {}), "Accept": f"{accept}; {want_topics}"}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers=merged, params=params)
                resp.raise_for_status()
                return resp.json()
        except httpx.RequestError as e:
            logger.error(f"Network error while fetching {url}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} from {url}")
            raise

    async def fetch(self) -> dict[str, Any]:
        """
        Fetch the full repository object (single endpoint).

        Returns
        -------
        dict
            Raw JSON for the repository from GET /repos/{owner}/{repo}.
        """
        base = settings.github_api_base
        url = f"{base}/repos/{self.owner}/{self.repo}"
        logger.debug(f"Fetching repository: {url}")
        data = await self._get(url)
        logger.info(f"Ingested data for {self.owner}/{self.repo} successfully")
        return data

    async def get_user(self, username: str) -> dict[str, Any]:
        """
        Fetch a GitHub user by username.

        Parameters
        ----------
        username : str
            GitHub username.

        Returns
        -------
        dict
            Raw JSON for the user from GET /users/{username}.
        """
        base = settings.github_api_base
        url = f"{base}/users/{username}"
        return await self._get(url)
