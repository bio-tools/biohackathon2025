"""
Repository provider for GitHub.
Forks repos, clones to a temp directory, applies file changes,
pushes branches, and creates pull requests via the GitHub API.
"""

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager

import httpx

from bridge.config import settings
from bridge.services.protocols import ForkInfo, RepoProvider

from .github_auth import get_github_headers

logger = logging.getLogger(__name__)


class GitHubRepoProvider(RepoProvider):
    """
    Provide GitHub repository operations.
    """

    def __init__(self):
        settings.require_github_token()
        self._login: str | None = None
        logger.debug("GitHubRepoProvider initialized (token verified).")

    async def _get_authenticated_login(self) -> str:
        """
        Return the login of the authenticated GitHub user (cached).

        Returns
        -------
        str
            GitHub username of the authenticated user.
        """
        if self._login is not None:
            return self._login

        base = settings.github_api_base
        url = f"{base}/user"
        headers = get_github_headers()

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            self._login = data["login"]
            logger.debug(f"Authenticated as GitHub user '{self._login}'")
            return self._login

    async def _get_existing_fork(self, source_owner: str, source_repo: str) -> ForkInfo | None:
        """
        Return ForkInfo for an existing fork of `source_owner/source_repo` owned by
        the authenticated user, or None if it does not exist.

        Parameters
        ----------
        source_owner : str
            Owner of the source repository.
        source_repo : str
            Name of the source repository.

        Returns
        -------
        ForkInfo | None
            ForkInfo of the existing fork, or None if not found.
        """
        login = await self._get_authenticated_login()
        base = settings.github_api_base
        url = f"{base}/repos/{login}/{source_repo}"
        headers = get_github_headers()

        logger.debug(f"Checking for existing fork {login}/{source_repo} of {source_owner}/{source_repo}")

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 404:
                logger.debug("No existing fork found.")
                return None

            response.raise_for_status()
            data = response.json()

        if not data.get("fork"):
            logger.debug(f"Repo {login}/{source_repo} exists but is not a fork.")
            return None

        parent_full_name = data.get("parent", {}).get("full_name")
        if parent_full_name != f"{source_owner}/{source_repo}":
            logger.debug(
                f"Repo {login}/{source_repo} is a fork, but parent is {parent_full_name}, "
                f"not {source_owner}/{source_repo}."
            )
            return None

        fork_info = ForkInfo(
            full_name=data["full_name"],
            owner=data["owner"]["login"],
            repo=data["name"],
        )
        logger.info(f"Reusing existing fork: {fork_info.full_name}")
        return fork_info

    async def _delete_repo(self, owner: str, repo: str) -> None:
        """
        Delete a GitHub repository.
        NOTE: This is destructive.

        Parameters
        ----------
        owner : str
            Owner of the repository.
        repo : str
            Name of the repository.
        """
        base = settings.github_api_base
        url = f"{base}/repos/{owner}/{repo}"
        headers = get_github_headers()

        logger.warning(f"Deleting repo {owner}/{repo}")

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.delete(url, headers=headers)

        # 204: deleted; 404: already gone -> both OK
        if response.status_code not in (204, 404):
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to delete repo {owner}/{repo}: {e}")
                raise

        logger.info(f"Repo {owner}/{repo} deleted or did not exist.")

    async def fork(
        self, owner: str, repo: str, replace_existing: bool = True, wait_ready: bool = True, max_wait: int = 20
    ) -> ForkInfo:
        """
        Fork a GitHub repository (or return an existing fork).

        Parameters
        ----------
        owner : str
            The owner of the repository to fork.
        repo : str
            The name of the repository to fork.
        replace_existing : bool
            Whether to delete an existing fork (if present) before creating a new one. Default is True.
        wait_ready : bool
            Whether to wait until the fork is fully ready. Default is True.
        max_wait : int
            Maximum number of seconds to wait for the fork to become ready. Default is 20.

        Returns
        -------
        dict
            JSON metadata for the forked repository.

        Raises
        ------
        HTTPError
            If the fork operation fails.
        """
        existing_fork = await self._get_existing_fork(owner, repo)

        if not replace_existing and existing_fork is not None:
            return existing_fork

        if replace_existing and existing_fork is not None:
            await self._delete_repo(existing_fork.owner, existing_fork.repo)

        base = settings.github_api_base
        url = f"{base}/repos/{owner}/{repo}/forks"
        headers = get_github_headers()

        logger.info(f"Forking repo {owner}/{repo} (wait_ready={wait_ready}, max_wait={max_wait}s)")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, headers=headers)
                response.raise_for_status()
                fork_data = response.json()
                fork_full_name = fork_data["full_name"]
                fork_owner = fork_data["owner"]["login"]
                fork_repo = fork_data["name"]
                fork_info = ForkInfo(full_name=fork_full_name, owner=fork_owner, repo=fork_repo)
                logger.info(f"Fork created: {fork_full_name}")

                if not wait_ready:
                    return fork_info

                # poll until fork is available (but don't fail hard if slow)
                for i in range(max_wait):
                    check = await client.get(f"{settings.github_api_url}repos/{fork_full_name}", headers=headers)
                    if check.status_code == 200:
                        logger.debug(f"Fork {fork_full_name} became ready after {i + 1}s.")
                        return fork_info
                    await asyncio.sleep(1)

                # if still not ready, just warn and continue with the initial response
                logger.warning(f"Fork {fork_full_name} not fully ready after {max_wait}s, returning initial data.")
                return fork_info
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error while forking {owner}/{repo}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while forking {owner}/{repo}: {e}")
            raise

    @contextmanager
    def clone_context(self, repo_full_name: str):
        """
        Use context manager to clone a GitHub repo into a temp dir and delete it afterward.

        Parameters
        ----------
        repo_full_name : str
            Full name of the repository (e.g., "owner/repo").
        """
        tmp_dir = tempfile.mkdtemp()
        repo_url = f"https://{settings.github_token}:x-oauth-basic@github.com/{repo_full_name}.git"

        logger.info(f"Cloning repo {repo_full_name} into temp dir {tmp_dir}")

        try:
            subprocess.run(["git", "clone", repo_url, tmp_dir], check=True)
            logger.debug(f"Repo {repo_full_name} cloned successfully.")
            yield tmp_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed for {repo_full_name}: {e}")
            raise
        finally:
            logger.debug(f"Cleaning up temp dir {tmp_dir}")
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def apply_changes_and_push(self, repo_path: str, branch_name: str, file_changes: dict):
        """
        Create a new branch from a local cloned repo, apply changes, and push.

        Parameters
        ----------
        repo_path : str
            Path to the local cloned GitHub repository.
        branch_name : str
            Name of the new branch to create.
        file_changes : dict
            Dictionary mapping file paths to their new content.
        """
        logger.info(f"Applying changes to {repo_path} on new branch {branch_name}")

        try:
            os.chdir(repo_path)
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)

            for path, content in file_changes.items():
                full_path = os.path.join(repo_path, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(content)
                subprocess.run(["git", "add", path], check=True)
                logger.debug(f"Added file: {path}")

            subprocess.run(["git", "commit", "-m", "Automated update via script"], check=True)
            subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)

            logger.info(f"Branch {branch_name} pushed successfully for repo at {repo_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.cmd}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while applying changes to {repo_path}: {e}")
            raise

    async def create_pull_request(
        self, owner: str, repo: str, title: str, body: str, head_branch: str, base_branch: str
    ) -> dict:
        """
        Create a pull request via GitHub REST API.

        Parameters
        ----------
        owner : str
            GitHub user or organization that owns the repository.
        repo : str
            Repository name.
        title : str
            Title of the pull request.
        body : str
            Description of the pull request.
        head_branch : str
            Name of the branch with the proposed changes.
        base_branch : str, optional
            Target branch to merge into (default is 'main').

        Returns
        -------
        dict
            JSON response from the GitHub API representing the created pull request.

        Raises
        ------
        HTTPError
            If the API request fails.
        """
        base = settings.github_api_base
        url = f"{base}/repos/{owner}/{repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
        }
        headers = get_github_headers()

        logger.info(f"Creating PR on {owner}/{repo}: '{title}' (head={head_branch}, base={base_branch})")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=data, headers=headers)

                if response.status_code == 422:
                    logger.warning(f"PR creation returned 422 for {owner}/{repo}: {response.text}")

                response.raise_for_status()
                pr_data = response.json()
                logger.info(f"Pull request created successfully: {pr_data.get('html_url', 'unknown URL')}")
                return pr_data
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API PR creation failed: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error creating PR for {owner}/{repo}: {e}")
            raise

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> dict:
        """
        Create a new issue on a GitHub repository.

        Parameters
        ----------
        owner : str
            GitHub user or organization that owns the repository.
        repo : str
            Repository name.
        title : str
            Title of the issue.
        body : str, optional
            Description of the issue.
        labels : list of str, optional
            List of label names to assign to the issue.
        assignees : list of str, optional
            List of GitHub usernames to assign to the issue.

        Returns
        -------
        dict
            JSON response from the GitHub API representing the created issue.

        Raises
        ------
        HTTPError
            If the API request fails.
        """
        base = settings.github_api_base
        url = f"{base}/repos/{owner}/{repo}/issues"
        headers = get_github_headers()

        data = {"title": title}
        if body:
            data["body"] = body
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees

        logger.info(f"Creating issue on {owner}/{repo}: '{title}'")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=data, headers=headers)

                if response.status_code == 422:
                    logger.warning(f"Issue creation returned 422 for {owner}/{repo}: {response.text}")

                response.raise_for_status()
                issue_data = response.json()
                logger.info(f"Issue created successfully: {issue_data.get('html_url', 'unknown URL')}")
                return issue_data
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API issue creation failed for {owner}/{repo}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while creating issue on {owner}/{repo}: {e}")
            raise
