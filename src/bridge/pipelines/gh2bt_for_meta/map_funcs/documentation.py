"""
Mapping functions for documentation field.
"""

from bridge.core.biotools import DocumentationItem, TypeEnum1
from bridge.core.github_pages import GitHubPages
from bridge.logging import get_user_logger
from bridge.pipelines.utils import canonicalize_url

logger = get_user_logger()


def _add_doc_if_not_exists(
    bt_documentation: list[DocumentationItem] | None, url: str, doc_type: TypeEnum1
) -> list[DocumentationItem]:
    """
    Add documentation item if it doesn't already exist.
    """
    if not bt_documentation:
        bt_documentation = []

    # Normalize the incoming URL for comparison
    normalized_url = canonicalize_url(url)

    url_exists = any(canonicalize_url(str(doc.url.root)) == normalized_url for doc in bt_documentation)

    if not url_exists:
        doc_item = DocumentationItem(url=url, type=[doc_type])
        bt_documentation.append(doc_item)

    return bt_documentation


def map_wiki(
    gh_html_url: str | None, gh_has_wiki: bool | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map GitHub wiki presence to bio.tools documentation.
    """
    if gh_has_wiki and gh_html_url:
        repo_url = canonicalize_url(str(gh_html_url))
        wiki_url = canonicalize_url(f"{repo_url}/wiki")
        return _add_doc_if_not_exists(bt_documentation, wiki_url, TypeEnum1.General)

    return bt_documentation


def map_code_of_conduct(
    gh_code_of_conduct: dict | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map GitHub code of conduct presence to bio.tools documentation.
    """
    if gh_code_of_conduct and gh_code_of_conduct.get("html_url"):
        coc_url = gh_code_of_conduct.get("html_url")
        return _add_doc_if_not_exists(bt_documentation, coc_url, TypeEnum1.Code_of_conduct)

    return bt_documentation


def map_github_pages(
    gh_pages: GitHubPages | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map GitHub Pages to bio.tools documentation.
    """
    if gh_pages and gh_pages.html_url:
        pages_url = str(gh_pages.html_url)
        return _add_doc_if_not_exists(bt_documentation, pages_url, TypeEnum1.General)

    return bt_documentation


def map_documentation(
    gh_repo_data: dict | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map GitHub wiki presence to bio.tools documentation field.
    """
    if not gh_repo_data:
        return bt_documentation

    gh_html_url = gh_repo_data.get("html_url")
    gh_has_wiki = gh_repo_data.get("has_wiki")
    gh_code_of_conduct = gh_repo_data.get("code_of_conduct")
    gh_pages = gh_repo_data.get("github_pages")

    bt_documentation = map_wiki(gh_html_url, gh_has_wiki, bt_documentation)
    bt_documentation = map_code_of_conduct(gh_code_of_conduct, bt_documentation)
    bt_documentation = map_github_pages(gh_pages, bt_documentation)

    return bt_documentation
