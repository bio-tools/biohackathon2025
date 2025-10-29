"""
Async client for the GitHub API.
Gathers repository metadata and returns a comprehensive dictionary of information.
"""

import asyncio
import logging
from typing import Any

import httpx

from bridge.config import settings
from bridge.services.protocols import Ingestor

from .github_auth import get_github_headers

logger = logging.getLogger(__name__)


class GitHubIngestor(Ingestor):
    """
    Ingest GitHub repository metadata via the GitHub REST API.

    Parameters
    ----------
    owner : str
        GitHub user or organization that owns the repository.
    repo : str
        Repository name.
    """

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def _get(
        self,
        endpoint: str = "",
        params: dict | None = None,
        scope: str = "repo",
        username: str | None = None,
        headers: dict | None = None,
    ) -> dict[str, Any]:
        """
        Perform async GET requests to GitHub API.

        Parameters
        ----------
        endpoint : str
            Specific API endpoint to query (default is root repo endpoint).
        params : dict, optional
            Query parameters for the request. Defaults to None.
        scope : str
            Scope of the request: 'repo' for repository, 'user' for user, 'raw' for raw endpoint. Default is 'repo'.
        username : str, optional
            GitHub username for 'user' scope requests. Required if scope is 'user'.
        headers : dict, optional
            Additional headers to include in the request. Defaults to None.

        Returns
        -------
        dict
            JSON response from the GitHub API.
        """
        base = settings.github_api_base
        endpoint = endpoint.lstrip("/")

        if scope == "repo":
            url = f"{base}/repos/{self.owner}/{self.repo}/{endpoint}".rstrip("/")
        elif scope == "user":
            if not username:
                raise ValueError("username must be provided for user scope")
            url = f"{base}/users/{username}/{endpoint}".rstrip("/")
        elif scope == "raw":
            url = f"{base}/{endpoint}".rstrip("/")
        else:
            raise ValueError(f"Unknown scope: {scope}")

        all_headers = {**get_github_headers(), **(headers or {})}

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, headers=all_headers, params=params)
                response.raise_for_status()
                logger.debug(f"Fetched data from {url} successfully")
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"Network error while fetching {url}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} from {url}")
            raise

    async def fetch(self) -> dict[str, Any]:
        """
        Fetch metadata for the specified GitHub repository.

        Returns
        -------
        dict
            A dictionary containing various metadata about the repository.
        """
        logger.debug(f"Fetching metadata for {self.owner}/{self.repo}")

        # first get basic repo data to determine default branch
        repo_data = await self._get("")
        default_branch = repo_data.get("default_branch", "main")

        # launch in parallel
        results = await asyncio.gather(
            self._get("/readme"),
            self._get("/license"),
            self._get("/languages"),
            self._get("/contributors"),
            self._get("/commits", {"per_page": 30}),
            self._get("/pulls", {"state": "all", "per_page": 30}),
            self._get("/issues", {"state": "all", "per_page": 30}),
            self.get_topics(),
            self.get_file_tree(default_branch),
        )

        result = {
            "repo_data": repo_data,
            "readme_data": results[0],
            "license_data": results[1],
            "languages_dict": results[2],
            "contributors_data": results[3],
            "commits_data": results[4],
            "pull_requests_data": results[5],
            "issues_data": results[6],
            "topics": results[7],
            "file_tree_data": results[8],
        }
        logger.info(f"Ingested data for {self.owner}/{self.repo} successfully")
        return result

    async def get_topics(self) -> dict[str, Any]:
        """
        Fetch the list of topics for the repository. Requires the topics preview header.

        Returns
        -------
        dict[str, Any]
            A dictionary containing the list of topics.
        """
        preview_header = {"Accept": "application/vnd.github.mercy-preview+json"}
        result = await self._get("topics", headers=preview_header)
        return {"names": result.get("names", [])}

    async def get_file_tree(self, branch: str = "main") -> dict[str, Any] | None:
        """
        Fetch the file tree for the specified branch. Requires recursive tree retrieval.

        Parameters
        ----------
        branch : str
            Branch name to fetch the file tree from. Default is 'main'.

        Returns
        -------
        dict[str, Any] | None
            A dictionary representing the file tree, or None if not found.
        """
        branch_data = await self._get(f"/branches/{branch}")
        tree_sha = branch_data.get("commit", {}).get("commit", {}).get("tree", {}).get("sha")
        if not tree_sha:
            logger.warning(f"No tree SHA found for branch {branch} in {self.repo}")
            return None
        return await self._get(f"/git/trees/{tree_sha}", params={"recursive": 1})

    async def get_user(self, username: str) -> dict[str, Any]:
        """
        Fetch metadata for a specified GitHub user.

        Parameters
        ----------
        username : str
            GitHub username to fetch metadata for.

        Returns
        -------
        dict[str, Any]
            JSON metadata for the specified GitHub user.
        """
        return await self._get(scope="user", username=username)
