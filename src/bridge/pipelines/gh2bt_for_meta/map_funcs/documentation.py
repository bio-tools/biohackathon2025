"""
Mapping functions for documentation metadata.

This module maps GitHub repository features (wiki, code of conduct, GitHub Pages)
to the bio.tools ``documentation`` field by adding appropriate
``DocumentationItem`` entries when they are not already present.
"""

from urllib.parse import urljoin

from bridge.core.biotools import DocumentationItem, TypeEnum1
from bridge.core.github_pages import GitHubPages
from bridge.logging import get_user_logger
from bridge.pipelines.utils import canonicalize_url

logger = get_user_logger()


def _add_doc_if_not_exists(
    bt_documentation: list[DocumentationItem] | None, url: str, doc_type: TypeEnum1
) -> list[DocumentationItem]:
    """
    Add a documentation item for the given URL if it does not already exist.

    Parameters
    ----------
    bt_documentation : list[DocumentationItem] | None
        Existing bio.tools documentation list, or ``None`` if unset.
    url : str
        Documentation URL to add.
    doc_type : TypeEnum1
        Documentation type to associate with this URL.

    Returns
    -------
    list[DocumentationItem]
        Updated list of documentation items.
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

    If the repository has a wiki enabled and a repository URL is available,
    a documentation entry of type ``TypeEnum1.General`` pointing to
    ``<repo_url>/wiki`` is added when not already present.

    Parameters
    ----------
    gh_html_url : str | None
        GitHub repository HTML URL (e.g. ``https://github.com/user/repo``).
    gh_has_wiki : bool | None
        Flag indicating whether the repository has wiki enabled.
    bt_documentation : list[DocumentationItem] | None
        Existing bio.tools documentation entries.

    Returns
    -------
    list[DocumentationItem] | None
        Updated documentation list, or the original list if nothing changed.
    """
    if gh_has_wiki and gh_html_url:
        repo_url = str(gh_html_url)
        wiki_raw = urljoin(repo_url.rstrip("/") + "/", "wiki")
        wiki_url = canonicalize_url(wiki_raw)
        return _add_doc_if_not_exists(bt_documentation, wiki_url, TypeEnum1.General)

    return bt_documentation


def map_code_of_conduct(
    gh_code_of_conduct: dict | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map GitHub code of conduct presence to bio.tools documentation.

    If a code of conduct is configured on GitHub and an ``html_url`` is
    available, a documentation entry of type ``TypeEnum1.Code_of_conduct``
    is added when not already present.

    Parameters
    ----------
    gh_code_of_conduct : dict[str, Any] | None
        GitHub code of conduct metadata dictionary, expected to contain
        an ``"html_url"`` key when present.
    bt_documentation : list[DocumentationItem] | None
        Existing bio.tools documentation entries.

    Returns
    -------
    list[DocumentationItem] | None
        Updated documentation list, or the original list if nothing changed.
    """
    if gh_code_of_conduct and gh_code_of_conduct.get("html_url"):
        coc_url = gh_code_of_conduct.get("html_url")
        return _add_doc_if_not_exists(bt_documentation, coc_url, TypeEnum1.Code_of_conduct)

    return bt_documentation


def map_github_pages(
    gh_pages: GitHubPages | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map GitHub Pages configuration to bio.tools documentation.

    If a GitHub Pages URL is configured, a documentation entry of type
    ``TypeEnum1.General`` is added when not already present.

    Parameters
    ----------
    gh_pages : GitHubPages | None
        Parsed GitHub Pages information, expected to expose an ``html_url``
        attribute when configured.
    bt_documentation : list[DocumentationItem] | None
        Existing bio.tools documentation entries.

    Returns
    -------
    list[DocumentationItem] | None
        Updated documentation list, or the original list if nothing changed.
    """
    if gh_pages and gh_pages.html_url:
        pages_url = str(gh_pages.html_url)
        return _add_doc_if_not_exists(bt_documentation, pages_url, TypeEnum1.General)

    return bt_documentation


def map_documentation(
    gh_repo_data: dict | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map and reconcile GitHub documentation-related metadata to the
    bio.tools documentation field.

    This function applies the documentation mapping policies for all
    supported GitHub documentation sources:
    - Repository wiki
    - Code of conduct
    - GitHub Pages site

    Each source is mapped independently and contributes a
    ``DocumentationItem`` entry when a corresponding URL is present on
    GitHub and not already recorded in bio.tools.

    Parameters
    ----------
    gh_repo_data : dict[str, Any] | None
        GitHub repository metadata dictionary. Expected keys include:
        - ``"html_url"``
        - ``"has_wiki"``
        - ``"code_of_conduct"``
        - ``"github_pages"``
    bt_documentation : list[DocumentationItem] | None
        Existing bio.tools documentation entries.

    Returns
    -------
    list[DocumentationItem] | None
        The updated bio.tools documentation list after applying all
        documentation mappings.
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
