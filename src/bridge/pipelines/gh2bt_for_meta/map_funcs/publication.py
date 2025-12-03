"""
Mapping functions for publication metadata from GitHub citation.cff to bio.tools.
"""

from typing import Any

from bridge.core.biotools import PublicationItem, TypeEnum2 as PublicationType
from bridge.logging import get_user_logger
from bridge.pipelines.shared.publications import deduplicate_references, extract_cff_references

logger = get_user_logger()


def _cff_ref_to_biotools(
    ref: dict[str, Any], pub_type: list[PublicationType] | PublicationType | None = None
) -> PublicationItem | None:
    """
    Convert a CITATION.cff reference dictionary to a bio.tools PublicationItem.

    Parameters
    ----------
    ref : dict[str, Any]
        A single reference entry from CITATION.cff.

    Returns
    -------
    PublicationItem | None
        The corresponding bio.tools PublicationItem instance, or ``None`` if no
        valid identifiers were found in the reference.
    """
    doi = ref.get("doi")
    pmid = ref.get("pmid")
    pmcid = ref.get("pmcid")

    if not doi and not pmid and not pmcid:
        return None

    pub_type_bt: list[PublicationType] | None = (
        pub_type if isinstance(pub_type, list) else [pub_type] if pub_type else None
    )

    return PublicationItem(
        doi=doi,
        pmid=pmid,
        pmcid=pmcid,
        type=pub_type_bt,
        note=None,
        version=None,
    )


def map_publication(
    gh_citation_cff: dict[str, Any], bt_publications: list[PublicationItem] | None
) -> list[PublicationItem] | None:
    """
    TODO
    """
    if not gh_citation_cff:
        logger.unchanged("No CITATION.cff data found in GitHub repository, nothing to map.")
        return bt_publications

    cff_references, cff_preferred = extract_cff_references(gh_citation_cff)

    gh_publications: list[PublicationItem] = []
    if cff_preferred:
        gh_publications.append(_cff_ref_to_biotools(cff_preferred, pub_type=PublicationType.Primary))
    gh_publications.extend([_cff_ref_to_biotools(ref) for ref in cff_references])
    gh_publications = [pub for pub in gh_publications if pub is not None]

    if not gh_publications:
        logger.unchanged("CITATION.cff exists but contains no references. Using only bio.tools metadata.")
        return bt_publications

    logger.added(f"{len(gh_publications)} reference(s) to merge with bio.tools metadata.")

    all_publications = gh_publications + (bt_publications or [])
    all_publications = deduplicate_references(all_publications)

    return all_publications
