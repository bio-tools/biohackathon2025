"""
Pydantic models representing GitHub repository state for the bridge.
"""

from pydantic import BaseModel


class GitHubCommit(BaseModel):
    """
    Represent a GitHub commit metadata.

    Parameters
    ----------
    sha : str
        Commit SHA hash.
    message : str
        Commit message.
    author_name : str | None
        Name of the commit author.
    author_email : str | None
        Email of the commit author.
    date : str | None
        ISO 8601 timestamp of the commit.
    url : str | None
        URL to the commit on GitHub.
    """

    sha: str
    message: str
    author_name: str | None
    author_email: str | None
    date: str | None  # ISO 8601 timestamp
    url: str | None


class GitHubPullRequest(BaseModel):
    """
    Represent a GitHub pull request metadata.

    Parameters
    ----------
    number : int
        Pull request number.
    title : str
        Pull request title.
    state : str
        Pull request state ("open", "closed", etc.).
    created_at : str | None
        ISO 8601 timestamp of pull request creation.
    updated_at : str | None
        ISO 8601 timestamp of last pull request update.
    merged_at : str | None
        ISO 8601 timestamp of pull request merge.
    user_login : str | None
        GitHub username of the pull request creator.
    url : str
        URL to the pull request on GitHub.
    """

    number: int
    title: str
    state: str  # "open", "closed", etc.
    created_at: str | None
    updated_at: str | None
    merged_at: str | None
    user_login: str | None
    url: str


class GitHubIssue(BaseModel):
    """
    Represent a GitHub issue metadata.

    Parameters
    ----------
    number : int
        Issue number.
    title : str
        Issue title.
    state : str
        Issue state ("open", "closed", etc.).
    created_at : str | None
        ISO 8601 timestamp of issue creation.
    updated_at : str | None
        ISO 8601 timestamp of last issue update.
    closed_at : str | None
        ISO 8601 timestamp of issue closure.
    user_login : str | None
        GitHub username of the issue creator.
    url : str
        URL to the issue on GitHub.
    """

    number: int
    title: str
    state: str
    created_at: str | None
    updated_at: str | None
    closed_at: str | None
    user_login: str | None
    url: str


class GitHubFileTreeEntry(BaseModel):
    """
    Represent a file or directory in the GitHub repository file tree.

    Parameters
    ----------
    path : str
        File or directory path.
    type : str
        Type of the entry ('blob' for file, 'tree' for directory).
    sha : str
        SHA hash of the file or directory.
    size : int | None
        Size of the file in bytes (None for directories).
    url : str | None
        URL to access the file or directory via GitHub API.
    """

    path: str
    type: str  # 'blob' or 'tree'
    sha: str
    size: int | None
    url: str | None


class GitHubUser(BaseModel):
    """
    Represent a GitHub user metadata.

    Parameters
    ----------
    login : str
        GitHub username.
    id : int | None
        GitHub user ID.
    html_url : str | None
        URL to the user's GitHub profile.
    type : str | None
        Type of user (e.g., "User", "Organization").
    name : str | None
        Full name of the user.
    email : str | None
        Email address of the user.
    company : str | None
        Company affiliation of the user.
    location : str | None
        Location of the user.
    contributions : int | None
        Number of contributions made by the user to the repository.
    """

    login: str
    id: int | None
    html_url: str | None
    type: str | None
    name: str | None
    email: str | None
    company: str | None
    location: str | None
    # orcid: Optional[str]  # TODO: not in GitHub API directly; can be scraped or cross-referenced
    contributions: int | None


class GitHubRepoModel(BaseModel):
    """
    Represent the GitHub repository state relevant for metadata extraction.

    Parameters
    ----------
    name : str
        Repository name.
    full_name : str
        Full repository name including owner (e.g., "owner/repo").
    html_url : str
        URL to the repository on GitHub.
    default_branch : str
        Default branch name (e.g., "main" or "master").
    description : str | None
        Repository description.
    homepage : str | None
        Repository homepage URL.
    topics : list[str] | None
        List of topics/tags associated with the repository.
    license_name : str | None
        Name of the repository license.
    readme_content : str | None
        Content of the README file.
    license_content : str | None
        Content of the LICENSE file.
    languages : list[str] | None
        List of programming languages used in the repository.
    num_contributors : int | None
        Number of contributors to the repository.
    contributors : list[GitHubUser] | None
        List of contributors to the repository.
    commits : list[GitHubCommit] | None
        List of recent commits in the repository.
    pull_requests : list[GitHubPullRequest] | None
        List of pull requests in the repository.
    issues : list[GitHubIssue] | None
        List of issues in the repository.
    file_tree : list[GitHubFileTreeEntry] | None
        File tree structure of the repository.
    """

    name: str
    full_name: str
    html_url: str
    default_branch: str
    description: str | None
    homepage: str | None
    topics: list[str] | None
    license_name: str | None
    readme_content: str | None
    license_content: str | None
    languages: list[str] | None
    num_contributors: int | None

    contributors: list[GitHubUser] | None
    commits: list[GitHubCommit] | None
    pull_requests: list[GitHubPullRequest] | None
    issues: list[GitHubIssue] | None
    file_tree: list[GitHubFileTreeEntry] | None

    def __str__(self):
        return "\n\n".join(f"{k}={str(v)!r}" for k, v in self.model_dump().items())
