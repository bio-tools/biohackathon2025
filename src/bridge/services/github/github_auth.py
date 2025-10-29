"""
Helper for constructing GitHub API request headers using configured credentials.
"""

from bridge.config import settings


def get_github_headers() -> dict:
    """
    Construct headers for GitHub API requests.

    Returns
    -------
    dict
        A dictionary containing the authorization and accept headers.
    """
    return {"Authorization": f"Bearer {settings.github_token}", "Accept": "application/vnd.github+json"}
