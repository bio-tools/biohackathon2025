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
        repo_data = await self.fetch_repo()
        latest_release_data = await self.fetch_latest_release()
        github_pages = await self.fetch_github_pages()
        readme = await self.fetch_readme()

        result: dict[str, Any] = {
            "repo": repo_data,
            "latest_release": latest_release_data,
            "github_pages": github_pages,
            "readme": readme,
        }
        return result

    async def fetch_repo(self) -> dict[str, Any]:
        """
        Fetch the full repository object (raw JSON).

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

    async def fetch_latest_release(self) -> dict[str, Any] | None:
        """
        Fetch the latest release (raw JSON) or return None if the repo has no releases.

        Returns
        -------
        dict | None
            Latest release JSON, or None when GitHub returns 404 (no releases).
        """
        base = settings.github_api_base
        url = f"{base}/repos/{self.owner}/{self.repo}/releases/latest"
        # Include the version header GitHub recommends; Accept is already set in get_github_headers().
        headers = {"X-GitHub-Api-Version": "2022-11-28"}
        try:
            logger.debug(f"Fetching latest release: {url}")
            return await self._get(url, headers=headers)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"No releases for {self.owner}/{self.repo}")
                return None
            raise

    async def fetch_github_pages(self) -> dict[str, Any]:
        """
        Fetch the GitHub Pages information for the repository.

        Returns
        -------
        dict
            Raw JSON for the GitHub Pages from GET /repos/{owner}/{repo}/pages.
        """
        base = settings.github_api_base
        url = f"{base}/repos/{self.owner}/{self.repo}/pages"
        headers = {"X-GitHub-Api-Version": "2022-11-28"}
        try:
            logger.debug(f"Fetching GitHub pages: {url}")
            return await self._get(url, headers=headers)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"No GitHub pages found for {self.owner}/{self.repo}")
                return None
            raise

    async def fetch_readme(self) -> str | None:
        """
        Fetch the README content (decoded) or return None if not found.

        Returns
        -------
        str | None
            Decoded README content, or None if not found.
        """
        base = settings.github_api_base
        url = f"{base}/repos/{self.owner}/{self.repo}/readme"
        headers = {"X-GitHub-Api-Version": "2022-11-28"}
        try:
            logger.debug(f"Fetching README: {url}")
            data = await self._get(url, headers=headers)
            import base64

            content_encoded = data.get("content", "")
            content_bytes = base64.b64decode(content_encoded)
            content_str = content_bytes.decode("utf-8", errors="replace")
            logger.info(f"Ingested README for {self.owner}/{self.repo} successfully")
            return content_str
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"No README found for {self.owner}/{self.repo}")
                return None
            raise

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
