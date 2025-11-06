"""
Mapping functions for documentation field.
"""

from bridge.core.biotools import DocumentationItem, TypeEnum1


def _add_doc_if_not_exists(
    bt_documentation: list[DocumentationItem] | None, url: str, doc_type: TypeEnum1
) -> list[DocumentationItem]:
    """
    Add documentation item if it doesn't already exist.
    """
    if bt_documentation is None:
        bt_documentation = []

    # Check if URL already exists in documentation
    url_exists = any(str(doc.url.root) == url for doc in bt_documentation)

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
        repo_url = str(gh_html_url).rstrip("/")
        wiki_url = f"{repo_url}/wiki"
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


def map_documentation(
    gh_repo_data: dict | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map GitHub wiki presence to bio.tools documentation field.
    """
    if gh_repo_data is None:
        return bt_documentation

    gh_html_url = gh_repo_data.get("html_url")
    gh_has_wiki = gh_repo_data.get("has_wiki")
    gh_code_of_conduct = gh_repo_data.get("code_of_conduct")

    bt_documentation = map_wiki(gh_html_url, gh_has_wiki, bt_documentation)
    bt_documentation = map_code_of_conduct(gh_code_of_conduct, bt_documentation)

    return bt_documentation
