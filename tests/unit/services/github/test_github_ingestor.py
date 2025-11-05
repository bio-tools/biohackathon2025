"""
Unit tests for bridge.services.github.GitHubIngestor.
"""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from bridge.config import settings
from bridge.services.github import GitHubIngestor


@pytest.mark.asyncio
async def test_github_ingestor_fetch_repo_and_latest_release(httpx_mock: HTTPXMock):
    """
    GitHubIngestor.fetch returns repo JSON + latest release JSON on success.
    """
    owner, repo = "org", "repo"
    base = settings.github_api_base

    # Repo data
    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}",
        json={
            "full_name": f"{owner}/{repo}",
            "default_branch": "main",
        },
    )

    # Latest release data
    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/releases/latest",
        json={
            "tag_name": "v1.2.3",
            "name": "First proper release",
        },
    )

    ing = GitHubIngestor(owner, repo)
    result = await ing.fetch()

    assert result["repo"]["full_name"] == f"{owner}/{repo}"
    assert result["repo"]["default_branch"] == "main"
    assert result["latest_release"]["tag_name"] == "v1.2.3"


@pytest.mark.asyncio
async def test_github_ingestor_fetch_handles_no_releases(httpx_mock: HTTPXMock):
    """
    GitHubIngestor.fetch sets latest_release to None when there are no releases (404).
    """
    owner, repo = "org", "repo"
    base = settings.github_api_base

    # Repo exists
    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}",
        json={"full_name": f"{owner}/{repo}", "default_branch": "main"},
    )

    # GitHub returns 404 for /releases/latest when there are no releases
    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/releases/latest",
        status_code=404,
        json={"message": "Not Found"},
    )

    ing = GitHubIngestor(owner, repo)
    result = await ing.fetch()

    assert result["repo"]["full_name"] == f"{owner}/{repo}"
    assert result["latest_release"] is None


@pytest.mark.asyncio
async def test_github_ingestor_raises_on_repo_error(httpx_mock: HTTPXMock):
    """
    GitHubIngestor.fetch propagates HTTPStatusError when the repo itself fails.
    """
    owner, repo = "org", "repo"
    base = settings.github_api_base

    # Repo fetch fails; fetch_latest_release is never called
    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}",
        status_code=404,
        json={"message": "Not Found"},
    )

    ing = GitHubIngestor(owner, repo)

    with pytest.raises(httpx.HTTPStatusError):
        await ing.fetch()


@pytest.mark.asyncio
async def test_github_ingestor_get_user(httpx_mock: HTTPXMock):
    """
    GitHubIngestor.get_user returns raw user JSON.
    """
    username = "alice"
    base = settings.github_api_base

    httpx_mock.add_response(
        url=f"{base}/users/{username}",
        json={"login": username, "id": 123},
    )

    # owner/repo are irrelevant for get_user; just pass something.
    ing = GitHubIngestor(owner="org", repo="repo")
    user = await ing.get_user(username)

    assert user["login"] == username
    assert user["id"] == 123
