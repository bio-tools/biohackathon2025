"""
Mapping functions for documentation field.
"""

from bridge.core.biotools import DocumentationItem, TypeEnum1


def map_documentation(
    gh_repo_data: dict | None, bt_documentation: list[DocumentationItem] | None
) -> list[DocumentationItem] | None:
    """
    Map GitHub wiki presence to bio.tools documentation field.
    """
    if gh_repo_data is None:
        # if there is no GitHub repo data, return the existing bio.tools documentation (which may also be None)
        return bt_documentation

    gh_has_wiki = gh_repo_data.get("has_wiki")
    gh_html_url = gh_repo_data.get("html_url")

    if gh_has_wiki is None or gh_html_url is None:
        # if there is no GitHub wiki info or repo URL, return the existing bio.tools documentation
        return bt_documentation

    if gh_has_wiki:
        repo_url = str(gh_html_url).rstrip("/")
        wiki_url = f"{repo_url}/wiki"

        # Initialize documentation list if None
        if bt_documentation is None:
            bt_documentation = []

        # Check if wiki URL already exists in documentation
        wiki_exists = any(str(doc.url.root) == wiki_url for doc in bt_documentation)

        if not wiki_exists:
            wiki_doc = DocumentationItem(url=wiki_url, type=[TypeEnum1.General])
            bt_documentation.append(wiki_doc)

        return bt_documentation

    return bt_documentation
