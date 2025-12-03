"""
Shared publication utilities for pipelines.
"""

from collections.abc import Mapping
from typing import Any

from bridge.core import Publication
from bridge.core.biotools import PublicationItem
from bridge.pipelines.utils import normalize_dict_strings, normalize_text


def ref_ids(ref: Publication | PublicationItem | Mapping[str, Any]) -> set[str]:
    """
    Extract a normalized set of identifiers for a publication-like object.
    This function collects all available identifiers and returns
    them as normalized strings, which can then be used for deduplication.

    Supports:
    - Europe PMC Publication model
    - bio.tools PublicationItem model
    - plain dict-like mappings

    Normalized identifiers include (when present):
    - DOI
    - PMID
    - PMCID
    - title

    Parameters
    ----------
    ref : Publication | Mapping[str, Any]
        The Publication object or dictionary representing a publication.

    Returns
    -------
    set[str]
        A set of normalized identifier strings.
        The set may be empty if no identifiers are present.

    Raises
    ------
    TypeError
        If `ref` is neither a `Publication` instance nor a mapping.
    """
    if isinstance(ref, Mapping):
        doi = ref.get("doi", None)
        pmid = ref.get("pmid", None)
        pmcid = ref.get("pmcid", None)
        title = ref.get("title", None)
    elif isinstance(ref, (Publication, PublicationItem)):
        doi = getattr(ref, "doi", None)
        pmid = getattr(ref, "pmid", None)
        pmcid = getattr(ref, "pmcid", None)
        title = getattr(ref, "title", None)
    else:
        raise TypeError("ref must be a Publication, PublicationItem, or a Mapping")

    ids: set[str] = set()

    if doi:
        ids.add(f"doi:{normalize_text(str(doi))}")
    if pmid:
        ids.add(f"pmid:{str(pmid).strip()}")
    if pmcid:
        ids.add(f"pmcid:{str(pmcid).strip()}")
    if title:
        ids.add(f"title:{normalize_text(str(title))}")

    return ids


def deduplicate_references(
    references: list[Publication | PublicationItem | Mapping[str, Any]],
) -> list[Publication | PublicationItem | Mapping[str, Any]]:
    """
    Deduplicate a list of publication-like objects based on shared identifiers.

    Two references are considered duplicates if they share at least one
    normalized identifier (DOI, PMID, PMCID, or title). The first occurrence
    in the input list is retained; all later duplicates are dropped.

    Parameters
    ----------
    references : list[Publication | Mapping[str, Any]]
        List of references (models or dicts) to deduplicate.

    Returns
    -------
    list[Publication | Mapping[str, Any]]
        Deduplicated list of references, preserving original order for
        the first occurrence of each logical publication.
    """
    seen_identifier_sets: list[set[str]] = []
    deduplicated: list[Publication | PublicationItem | Mapping[str, Any]] = []

    for ref in references:
        current_ids = ref_ids(ref)

        # if we have no identifiers at all, treat as unique
        if not current_ids:
            deduplicated.append(ref)
            continue

        duplicate = False
        for seen_ids in seen_identifier_sets:
            if current_ids & seen_ids:  # intersection
                duplicate = True
                # merge identifier sets to strengthen future matching
                seen_ids.update(current_ids)
                break

        if duplicate:
            continue

        seen_identifier_sets.append(set(current_ids))
        deduplicated.append(ref)

    return deduplicated


def extract_cff_references(
    citation_cff: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """
    Extract publication information from CITATION.cff dictionary.

    This helper parses an existing CFF structure and returns:
    - the list of reference entries, and
    - the preferred-citation entry, if present.

    The preferred citation is ensured to be part of the references list:
    if it is not already present, it is appended.

    Parameters
    ----------
    citation_cff : dict[str, Any] | None
        Parsed content of an existing CITATION.cff file,
        or ``None`` if no file exists.

    Returns
    -------
    tuple[list[dict[str, Any]], dict[str, Any] | None]
        A tuple of:
        - A list of reference dictionaries extracted from the CFF.
        - The preferred-citation dictionary, or ``None`` if not present.
    """
    if not citation_cff:
        return [], None

    citation_cff = normalize_dict_strings(citation_cff)

    references = citation_cff.get("references") or []
    references = [r for r in references if isinstance(r, Mapping)]

    preferred = citation_cff.get("preferred-citation")
    if isinstance(preferred, Mapping):
        preferred = dict(preferred)  # shallow copy
    else:
        preferred = None

    # ensure preferred-citation is included in references if present
    if preferred is not None:
        pref_ids = ref_ids(preferred)
        in_refs = any(ref_ids(r) & pref_ids for r in references)
        if not in_refs:
            references.append(preferred)

    return references, preferred
