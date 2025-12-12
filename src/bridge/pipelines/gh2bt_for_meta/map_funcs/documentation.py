"""
Mapping functions for documentation metadata.

This module maps GitHub repository features (wiki, code of conduct, GitHub Pages)
to the bio.tools ``documentation`` field by adding appropriate
``DocumentationItem`` entries when they are not already present.
"""

import subprocess
from typing import Any
from urllib.parse import urljoin

from pydantic import AnyUrl

from bridge.core.biotools import DocumentationItem, TypeEnum1
from bridge.core.github_pages import GitHubPages
from bridge.core.github_repo import CodeOfConduct
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
        logger.added(f"documentation URL '{url}' as type '{doc_type.value}'.")
    else:
        logger.exact(f"documentation URL '{url}' of type '{doc_type.value}' already exists, not adding.")

    return bt_documentation


def _wiki_repo_exists(gh_html_url: AnyUrl | None, timeout: float = 5.0) -> bool:
    """
    Check if the GitHub wiki repository exists by probing with `git ls-remote`.
    """
    if not gh_html_url:
        return False

    try:
        wiki_git_url = str(gh_html_url).rstrip("/") + ".wiki.git"

        result = subprocess.run(
            ["git", "ls-remote", wiki_git_url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout expired while checking wiki repository at '{wiki_git_url}'.")
        return False


def _map_wiki(
    gh_html_url: AnyUrl | None, gh_has_wiki: bool | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map GitHub wiki presence to bio.tools documentation.

    If the repository has a wiki enabled and a repository URL is available,
    a documentation entry of type ``TypeEnum1.General`` pointing to
    ``<repo_url>/wiki`` is added when not already present.

    Parameters
    ----------
    gh_html_url : AnyUrl | None
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
    if gh_has_wiki and gh_html_url and _wiki_repo_exists(gh_html_url):
        repo_url = str(gh_html_url)
        wiki_raw = urljoin(repo_url.rstrip("/") + "/", "wiki")
        wiki_url = canonicalize_url(wiki_raw)
        return _add_doc_if_not_exists(bt_documentation, wiki_url, TypeEnum1.General)

    logger.unchanged("no GitHub wiki found, nothing to map.")
    return bt_documentation


def _map_code_of_conduct(
    gh_code_of_conduct: CodeOfConduct | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map GitHub code of conduct presence to bio.tools documentation.

    If a code of conduct is configured on GitHub and an ``html_url`` is
    available, a documentation entry of type ``TypeEnum1.Code_of_conduct``
    is added when not already present.

    Parameters
    ----------
    gh_code_of_conduct : CodeOfConduct | None
        GitHub code of conduct metadata, expected to contain
        an ``"html_url"`` key when present.
    bt_documentation : list[DocumentationItem] | None
        Existing bio.tools documentation entries.

    Returns
    -------
    list[DocumentationItem] | None
        Updated documentation list, or the original list if nothing changed.
    """
    if gh_code_of_conduct and gh_code_of_conduct.html_url:
        coc_url = gh_code_of_conduct.html_url
        coc_url_str = canonicalize_url(str(coc_url))
        return _add_doc_if_not_exists(bt_documentation, coc_url_str, TypeEnum1.Code_of_conduct)

    logger.unchanged("no GitHub code of conduct found, nothing to map.")
    return bt_documentation


def _map_github_pages(
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
        pages_url = gh_pages.html_url
        pages_url_str = canonicalize_url(str(pages_url))
        return _add_doc_if_not_exists(bt_documentation, pages_url_str, TypeEnum1.General)

    logger.unchanged("no GitHub Pages site found, nothing to map.")
    return bt_documentation


def map_documentation(
    gh_repo_data: dict[str, Any] | None, bt_documentation: list[DocumentationItem] | None
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
        logger.unchanged("no GitHub repository documentation data found, nothing to map.")
        return bt_documentation

    gh_html_url: AnyUrl | None = gh_repo_data.get("html_url")
    gh_has_wiki: bool | None = gh_repo_data.get("has_wiki")
    gh_code_of_conduct: CodeOfConduct | None = gh_repo_data.get("code_of_conduct")
    gh_pages: GitHubPages | None = gh_repo_data.get("github_pages")

    bt_documentation = _map_wiki(gh_html_url, gh_has_wiki, bt_documentation)
    bt_documentation = _map_code_of_conduct(gh_code_of_conduct, bt_documentation)
    bt_documentation = _map_github_pages(gh_pages, bt_documentation)

    return bt_documentation
