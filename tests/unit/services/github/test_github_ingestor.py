"""
Unit tests for bridge.services.github.GitHubIngestor.
"""

import base64

import httpx
import pytest
from pytest_httpx import HTTPXMock

from bridge.config import settings
from bridge.services.github import GitHubIngestor


def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


@pytest.mark.asyncio
async def test_github_ingestor_fetch_happy(httpx_mock: HTTPXMock):
    """
    fetch() returns repo + latest_release + github_pages + readme + languages on success.
    """
    owner, repo = "org", "repo"
    base = settings.github_api_base

    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}",
        json={"full_name": f"{owner}/{repo}", "default_branch": "main"},
    )

    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/releases/latest",
        json={"tag_name": "v1.2.3", "name": "Release"},
    )

    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/pages",
        json={"html_url": f"https://{owner}.github.io/{repo}"},
    )

    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/readme",
        json={"content": _b64("# Hello README\n")},
    )

    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/languages",
        json={"Python": 1234, "JavaScript": 567},
    )

    ing = GitHubIngestor(owner, repo)
    result = await ing.fetch()

    assert result["repo"]["full_name"] == f"{owner}/{repo}"
    assert result["latest_release"]["tag_name"] == "v1.2.3"
    assert result["github_pages"]["html_url"].endswith(f"/{repo}")
    assert result["readme"].startswith("# Hello README")
    assert "Python" in result["languages"]


@pytest.mark.asyncio
async def test_github_ingestor_fetch_handles_no_releases(httpx_mock: HTTPXMock):
    """
    fetch() sets latest_release to None when /releases/latest returns 404.
    Other components still succeed.
    """
    owner, repo = "org", "repo"
    base = settings.github_api_base

    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}",
        json={"full_name": f"{owner}/{repo}", "default_branch": "main"},
    )

    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/releases/latest",
        status_code=404,
        json={"message": "Not Found"},
    )

    # still required because fetch() calls these
    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/pages",
        json={"html_url": f"https://{owner}.github.io/{repo}"},
    )
    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/readme",
        json={"content": _b64("readme\n")},
    )
    httpx_mock.add_response(
        url=f"{base}/repos/{owner}/{repo}/languages",
        json={"Python": 1},
    )

    ing = GitHubIngestor(owner, repo)
    result = await ing.fetch()

    assert result["repo"]["full_name"] == f"{owner}/{repo}"
    assert result["latest_release"] is None
    assert result["readme"] is not None


@pytest.mark.asyncio
async def test_github_ingestor_raises_on_repo_error(httpx_mock: HTTPXMock):
    """
    fetch() should raise HTTPStatusError if repo fetch fails.
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


@pytest.mark.asyncio
async def test_github_ingestor_get_user(httpx_mock: HTTPXMock):
    """
    get_user() returns raw user JSON.
    """
    username = "alice"
    base = settings.github_api_base

    httpx_mock.add_response(
        url=f"{base}/users/{username}",
        json={"login": username, "id": 123},
    )

    ing = GitHubIngestor(owner="org", repo="repo")
    user = await ing.get_user(username)

    assert user["login"] == username
    assert user["id"] == 123
