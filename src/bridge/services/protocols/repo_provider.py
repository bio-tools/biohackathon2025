"""
Protocol for repository operations and a minimal ForkInfo dataclass.
"""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol


@dataclass
class ForkInfo:
    """Generic metadata for a forked repository."""

    full_name: str  # e.g. "owner/repo"
    owner: str  # e.g. "owner" or namespace
    repo: str  # repository name


class RepoProvider(Protocol):
    """Protocol for repository operations."""

    async def fork(self, owner: str, repo: str) -> ForkInfo:
        """Fork a repository."""
        ...

    def clone_context(self, repo_full_name: str) -> AbstractContextManager[str]:
        """Use context manager to clone a repository."""
        ...

    def apply_changes_and_push(self, repo_path: str, branch_name: str, file_changes: dict):
        """Apply file changes and push to a branch."""
        ...

    async def create_pull_request(
        self, owner: str, repo: str, title: str, body: str, head_branch: str, base_branch: str
    ) -> dict:
        """Create a pull request."""
        ...

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> dict:
        """Create a new issue on a repository."""
        ...
