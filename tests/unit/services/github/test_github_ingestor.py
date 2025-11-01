"""
Unit tests for bridge.services.github.GitHubIngestor.
"""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from bridge.config import settings
from bridge.services.github import GitHubIngestor


@pytest.mark.asyncio
async def test_github_ingestor_fetch(httpx_mock: HTTPXMock):
    """
    Test that GitHubIngestor can fetch data from the GitHub API.

    Raises
    ------
    AssertionError
        If the fetched data does not match the expected values.
    """
    owner, repo = "org", "repo"
    base = settings.github_api_base

    httpx_mock.add_response(url=f"{base}/repos/{owner}/{repo}", json={"default_branch": "main"})
    httpx_mock.add_response(url=f"{base}/repos/{owner}/{repo}/readme", json={"content": "..."})
    httpx_mock.add_response(url=f"{base}/repos/{owner}/{repo}/license", json={"spdx_id": "Apache-2.0"})
    httpx_mock.add_response(url=f"{base}/repos/{owner}/{repo}/languages", json={"Python": 1000})
    httpx_mock.add_response(url=f"{base}/repos/{owner}/{repo}/contributors", json=[])
    httpx_mock.add_response(url=f"{base}/repos/{owner}/{repo}/commits?per_page=30", json=[])
    httpx_mock.add_response(url=f"{base}/repos/{owner}/{repo}/pulls?state=all&per_page=30", json=[])
    httpx_mock.add_response(url=f"{base}/repos/{owner}/{repo}/issues?state=all&per_page=30", json=[])
    httpx_mock.add_response(url=f"{base}/repos/{owner}/{repo}/topics", json={"names": ["bioinformatics"]})

    # branch -> tree
    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/branches/main",
        json={"commit": {"commit": {"tree": {"sha": "abc"}}}},
    )
    # IMPORTANT: match query params
    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/git/trees/abc?recursive=1",
        json={"tree": []},
    )

    ing = GitHubIngestor(owner, repo)
    data = await ing.fetch()

    assert data["repo_data"]["default_branch"] == "main"
    assert data["languages_dict"]["Python"] == 1000


@pytest.mark.asyncio
async def test_github_ingestor_raises_on_repo_error(httpx_mock: HTTPXMock):
    """
    Test that GitHubIngestor.fetch raises an exception on repo fetch error.

    Raises
    ------
    Exception
        If the repository fetch does not raise an exception on error.
    """
    owner, repo = "org", "repo"
    base = settings.github_api_base

    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}",
        status_code=404,
        json={"message": "Not Found"},
    )

    ing = GitHubIngestor(owner, repo)

    with pytest.raises(httpx.HTTPStatusError):
        await ing.fetch()
