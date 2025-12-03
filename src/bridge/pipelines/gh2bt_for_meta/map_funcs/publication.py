"""
Mapping functions for publication metadata from GitHub citation.cff to bio.tools.
"""

from typing import Any

from bridge.core.biotools import PublicationItem


def map_publication(
    gh_citation_cff: dict[str, Any], bt_publication: list[PublicationItem] | None
) -> list[PublicationItem] | None:
    """
    TODO
    """
    return bt_publication
