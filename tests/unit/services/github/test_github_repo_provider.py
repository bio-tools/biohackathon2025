"""
Minimal, high-value unit tests for bridge.services.github.GitHubRepoProvider.
"""

import httpx
import pytest

from bridge.services.github.github_repo_provider import GitHubRepoProvider


@pytest.mark.asyncio
async def test_fork_wait_ready_false(monkeypatch):
    """
    fork(wait_ready=False) returns ForkInfo from the POST /forks response
    and does not poll readiness.
    """

    # Bypass existing-fork logic (avoids extra API calls to /user and /repos/{login}/{repo})
    async def fake_get_existing_fork(self, source_owner, source_repo):
        return None

    monkeypatch.setattr(GitHubRepoProvider, "_get_existing_fork", fake_get_existing_fork)

    class FakeResp:
        def __init__(self, json_data, status_code=202):
            self._json = json_data
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError(
                    "error",
                    request=httpx.Request("POST", "https://api.github.test/forks"),
                    response=httpx.Response(self.status_code),
                )

        def json(self):
            return self._json

    class FakeClient:
        def __init__(self, *args, **kwargs): ...

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None):
            return FakeResp(
                {
                    "full_name": "me/repo-fork",
                    "owner": {"login": "me"},
                    "name": "repo-fork",
                },
                status_code=202,
            )

    monkeypatch.setattr("bridge.services.github.github_repo_provider.httpx.AsyncClient", FakeClient)

    provider = GitHubRepoProvider()
    fork_info = await provider.fork("upstream", "repo", wait_ready=False)

    assert fork_info.full_name == "me/repo-fork"
    assert fork_info.owner == "me"
    assert fork_info.repo == "repo-fork"


def test_apply_changes_and_push(monkeypatch, tmp_path):
    """
    apply_changes_and_push runs the expected git commands and writes files.
    """
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    # avoid changing the real process cwd
    chdirs = []

    def fake_chdir(path):
        chdirs.append(path)

    monkeypatch.setattr("os.chdir", fake_chdir)

    calls = []

    def fake_run(cmd, check=True):
        calls.append(cmd)

    monkeypatch.setattr("subprocess.run", fake_run)

    provider = GitHubRepoProvider()
    provider.apply_changes_and_push(
        str(repo_dir),
        "update-branch",
        {"README.md": "# hi"},
    )

    assert chdirs == [str(repo_dir)]
    assert ["git", "checkout", "-b", "update-branch"] in calls
    assert any(cmd[:2] == ["git", "add"] for cmd in calls)
    assert any(cmd[:2] == ["git", "commit"] for cmd in calls)
    assert any(cmd[:2] == ["git", "push"] for cmd in calls)


@pytest.mark.asyncio
async def test_create_pr_success(monkeypatch):
    """
    create_pull_request returns JSON on success.
    """

    class FakeResp:
        status_code = 201
        text = ""

        def raise_for_status(self):  # no error
            return None

        def json(self):
            return {"html_url": "https://github.com/x/y/pull/1"}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json, headers):
            return FakeResp()

    monkeypatch.setattr(
        "bridge.services.github.github_repo_provider.httpx.AsyncClient",
        lambda *a, **k: FakeClient(),
    )

    prov = GitHubRepoProvider()
    pr = await prov.create_pull_request(
        owner="o",
        repo="r",
        title="t",
        body="b",
        head_branch="me:branch",
        base_branch="main",
    )
    assert pr["html_url"].endswith("/pull/1")


@pytest.mark.asyncio
async def test_create_pr_422_raises_http_status_error(monkeypatch):
    """
    create_pull_request raises httpx.HTTPStatusError on 422 (validation failed).
    """

    class FakeResp:
        status_code = 422
        text = "validation failed"

        def raise_for_status(self):
            raise httpx.HTTPStatusError(
                "422 Unprocessable Entity",
                request=httpx.Request("POST", "https://api.github.test/pulls"),
                response=httpx.Response(422, request=httpx.Request("POST", "https://api.github.test/pulls")),
            )

        def json(self):
            return {}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json, headers):
            return FakeResp()

    monkeypatch.setattr(
        "bridge.services.github.github_repo_provider.httpx.AsyncClient",
        lambda *a, **k: FakeClient(),
    )

    prov = GitHubRepoProvider()
    with pytest.raises(httpx.HTTPStatusError):
        await prov.create_pull_request(
            owner="o",
            repo="r",
            title="t",
            body="b",
            head_branch="me:branch",
            base_branch="main",
        )
