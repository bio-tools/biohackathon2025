"""
Unit tests for bridge.services.github.GitHubRepoProvider.
"""

import pytest

from bridge.services.github.github_repo_provider import GitHubRepoProvider


@pytest.mark.asyncio
async def test_fork_wait_ready_false(monkeypatch):
    """
    Test forking a repo with wait_ready=False.

    Raises
    ------
    AssertionError
        If the forked repo information does not match expected values.
    """

    # fake httpx client
    class FakeResp:
        def __init__(self, json_data, status_code=202):
            self._json = json_data
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError("HTTP error")

        def json(self):
            return self._json

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self._calls = []

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
    # settings.require_github_token() is called in __init__, but we set env in conftest → OK
    provider = GitHubRepoProvider()
    fork_info = await provider.fork("upstream", "repo", wait_ready=False)
    assert fork_info.full_name == "me/repo-fork"
    assert fork_info.owner == "me"
    assert fork_info.repo == "repo-fork"


def test_clone_context(monkeypatch, tmp_path):
    """
    Test cloning a GitHub repository.

    Raises
    ------
    AssertionError
        If the cloned path does not match expected values or if the git clone command was not called.
    """
    # make mkdtemp deterministic
    monkeypatch.setattr("tempfile.mkdtemp", lambda: str(tmp_path / "cloned"))
    # don't actually clone, just assert command
    calls = []

    def fake_run(cmd, check):
        calls.append(cmd)

    monkeypatch.setattr("subprocess.run", fake_run)
    # don't actually delete
    monkeypatch.setattr("shutil.rmtree", lambda *a, **k: None)

    from bridge.services.github.github_repo_provider import GitHubRepoProvider

    provider = GitHubRepoProvider()
    with provider.clone_context("me/repo") as path:
        assert path == str(tmp_path / "cloned")
    # we should have called git clone
    assert any("clone" in c for c in (" ".join(cmd) for cmd in calls))


def test_apply_changes_and_push(monkeypatch, tmp_path):
    """
    Test applying changes to a GitHub repository and pushing them.

    Raises
    ------
    AssertionError
        If the expected git commands were not called during the process.
    """
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    # avoid chdir out of pytest runner
    cwd_holder = {"cwd": None}

    def fake_chdir(path):
        cwd_holder["cwd"] = path

    monkeypatch.setattr("os.chdir", fake_chdir)

    calls = []

    def fake_run(cmd, check):
        calls.append(cmd)

    monkeypatch.setattr("subprocess.run", fake_run)

    from bridge.services.github.github_repo_provider import GitHubRepoProvider

    provider = GitHubRepoProvider()
    provider.apply_changes_and_push(
        str(repo_dir),
        "update",
        {"README.md": "# hi"},
    )

    # chdir happened
    assert cwd_holder["cwd"] == str(repo_dir)
    # branch created
    assert ["git", "checkout", "-b", "update"] in calls
    # file was added
    assert any(cmd[:2] == ["git", "add"] for cmd in calls)
    # commit and push happened
    assert any(cmd[:2] == ["git", "commit"] for cmd in calls)
    assert any(cmd[:2] == ["git", "push"] for cmd in calls)


@pytest.mark.asyncio
async def test_create_pr_success(monkeypatch):
    """
    Test creating a pull request successfully.

    Raises
    ------
    AssertionError
        If the created pull request URL does not match expected values.
    """

    class FakeResp:
        status_code = 201

        def raise_for_status(self): ...
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
async def test_create_pr_422(monkeypatch):
    """
    Test creating a pull request that results in a 422 error.

    Raises
    ------
    RuntimeError
        If the pull request creation does not raise a RuntimeError on 422 response.
    """

    class FakeResp:
        status_code = 422
        text = "validation failed"

        def raise_for_status(self):
            raise RuntimeError("422")

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
    with pytest.raises(RuntimeError):
        await prov.create_pull_request(
            owner="o",
            repo="r",
            title="t",
            body="b",
            head_branch="me:branch",
            base_branch="main",
        )
