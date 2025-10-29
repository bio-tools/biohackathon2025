"""
Transformer normalizing GitHub REST responses into GitHubRepoModel.
"""

import base64
import logging

from bridge.builders.protocols import Transformer
from bridge.core import GitHubRepoModel
from bridge.core.github import GitHubCommit, GitHubFileTreeEntry, GitHubIssue, GitHubPullRequest, GitHubUser
from bridge.services import GitHubIngestor

logger = logging.getLogger(__name__)


class GitHubRepoTransformer(Transformer):
    """
    Transform raw data from GitHubIngestor into a GitHubRepoModel.

    Parameters
    ----------
    ingestor : GitHubIngestor
        An instance of GitHubIngestor to fetch raw repository metadata.

    Attributes
    ----------
    ingestor : GitHubIngestor
        The ingestor instance used to fetch raw repository metadata.
    """

    def __init__(self, ingestor: GitHubIngestor):
        self.ingestor = ingestor

    async def transform(self) -> GitHubRepoModel:
        """
        Transform raw data into a GitHubRepoModel.

        Returns
        -------
        GitHubRepoModel
            The transformed repository model.
        """
        logger.info(f"Transforming data for repository {self.ingestor.owner}/{self.ingestor.repo}")
        raw_data = await self.ingestor.fetch()
        logger.debug(f"Raw data keys: {list(raw_data.keys())}")

        result = GitHubRepoModel(
            name=raw_data["repo_data"]["name"],
            full_name=raw_data["repo_data"]["full_name"],
            description=raw_data["repo_data"].get("description"),
            html_url=raw_data["repo_data"]["html_url"],
            homepage=raw_data["repo_data"].get("homepage"),
            default_branch=raw_data["repo_data"]["default_branch"],
            topics=raw_data["topics"]["names"],
            license_name=raw_data["license_data"].get("license", {}).get("name") if raw_data["license_data"] else None,
            readme_content=self._decode_base64_content(raw_data["readme_data"]) if raw_data["readme_data"] else None,
            license_content=self._decode_base64_content(raw_data["license_data"]) if raw_data["license_data"] else None,
            languages=list(raw_data["languages_dict"].keys()),
            num_contributors=len(raw_data["contributors_data"]) if raw_data["contributors_data"] else 0,
            contributors=[
                GitHubUser(
                    login=user_data["login"],
                    id=user_data.get("id"),
                    html_url=user_data.get("html_url"),
                    type=user_data.get("type"),
                    name=user_data.get("name"),
                    email=user_data.get("email"),
                    company=user_data.get("company"),
                    location=user_data.get("location"),
                    contributions=c.get("contributions"),
                )
                for c in raw_data["contributors_data"]
                if (user_data := await self.ingestor.get_user(c["login"]))
            ],
            commits=[
                GitHubCommit(
                    sha=c["sha"],
                    message=c["commit"]["message"],
                    author_name=c["commit"]["author"].get("name"),
                    author_email=c["commit"]["author"].get("email"),
                    date=c["commit"]["author"].get("date"),
                    url=c["html_url"],
                )
                for c in raw_data["commits_data"]
            ],
            pull_requests=[
                GitHubPullRequest(
                    number=pr["number"],
                    title=pr["title"],
                    state=pr["state"],
                    created_at=pr.get("created_at"),
                    updated_at=pr.get("updated_at"),
                    merged_at=pr.get("merged_at"),
                    user_login=pr.get("user", {}).get("login"),
                    url=pr["html_url"],
                )
                for pr in raw_data["pull_requests_data"]
            ],
            issues=[
                GitHubIssue(
                    number=iss["number"],
                    title=iss["title"],
                    state=iss["state"],
                    created_at=iss.get("created_at"),
                    updated_at=iss.get("updated_at"),
                    closed_at=iss.get("closed_at"),
                    user_login=iss.get("user", {}).get("login"),
                    url=iss["html_url"],
                )
                for iss in raw_data["issues_data"]
                if "pull_request" not in iss  # exclude PRs
            ],
            file_tree=[
                GitHubFileTreeEntry(path=f["path"], type=f["type"], sha=f["sha"], size=f.get("size"), url=f.get("url"))
                for f in raw_data["file_tree_data"].get("tree", [])
            ],
        )

        logger.info(f"GitHub transformation completed successfully for {self.ingestor.owner}/{self.ingestor.repo}")
        return result

    @staticmethod
    def _decode_base64_content(data: dict | None) -> str | None:
        """
        Decode base64 encoded content from GitHub API response.

        Parameters
        ----------
        data : dict | None
            The data dictionary containing base64 encoded content.
        """
        if not data or "content" not in data:
            return None
        return base64.b64decode(data["content"]).decode("utf-8")
