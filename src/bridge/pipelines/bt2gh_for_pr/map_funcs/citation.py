"""
Generate a CITATION.cff file from bio.tools publication metadata.

This module retrieves publications from a bio.tools entry,
resolves them via the Europe PMC REST API, and converts
the resulting bibliographic information into the Citation File Format (CFF).
The output is a valid `CITATION.cff` file that can be committed to a GitHub
repository to enable software citation.
"""

from collections.abc import Mapping
from typing import Any

import yaml

from bridge.builders import compose_europe_pmc_metadata
from bridge.core import Publication
from bridge.core.biotools import TypeEnum2
from bridge.logging import get_user_logger
from bridge.pipelines.utils import (
    normalize_dict_strings,
    normalize_pydantic_model_strings,
    normalize_text,
    object_to_primitive,
)

logger = get_user_logger()

TIMEOUT = 20


def _ref_ids(ref: Publication | Mapping[str, Any]) -> set[str]:
    """
    Extract all usable identifiers from a Publication as a normalized set.

    Parameters
    ----------
    ref : Publication | Mapping[str, Any]
        The Publication object or dictionary representing a publication.

    Returns
    -------
    set[str]
        A set of normalized identifier strings.

    Raises
    ------
    TypeError
        If ref is neither a Publication nor a Mapping.
    """
    if isinstance(ref, Mapping):
        doi = ref.get("doi", None)
        pmid = ref.get("pmid", None)
        pmcid = ref.get("pmcid", None)
        title = ref.get("title", None)
    elif isinstance(ref, Publication):
        doi = getattr(ref, "doi", None)
        pmid = getattr(ref, "pmid", None)
        pmcid = getattr(ref, "pmcid", None)
        title = getattr(ref, "title", None)
    else:
        raise TypeError("ref must be a Publication or a Mapping")

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


def _deduplicate_references(references: list[Publication | Mapping[str, Any]]) -> list[Publication | Mapping[str, Any]]:
    """
    Deduplicate Publication objects: if ANY identifier overlaps, they are treated
    as the same reference. First occurrence wins.

    Parameters
    ----------
    references : list[Publication | Mapping[str, Any]]
        List of references to deduplicate.

    Returns
    -------
    list[Publication | Mapping[str, Any]]
        Deduplicated list of references.
    """
    seen_identifier_sets: list[set[str]] = []
    deduplicated: list[Publication | Mapping[str, Any]] = []

    for ref in references:
        current_ids = _ref_ids(ref)

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


def _key_func(r: Publication | dict[str, Any]) -> tuple[int, str]:
    """
    Key function to select the most recent publication based on year and title.

    Parameters
    ----------
    r : Publication | dict[str, Any]
        The publication to evaluate.

    Returns
    -------
    tuple[int, str]
        A tuple containing the year (as int) and title (as str) for comparison.
    """
    if isinstance(r, Publication):
        return (r.year or 0, r.title or "")
    return (int(r.get("year", 0) or 0), r.get("title", "") or "")


def _choose_preferred_citation(
    references: list[Publication | dict[str, Any]],
    bt_primary_references: list[Publication],
    gh_preferred_reference: dict[str, Any] | None = None,
) -> Publication | dict[str, Any] | None:
    """
    Choose the preferred citation from the list of references.
    If there is a preferred citation from the existing GitHub CITATION.cff file, it is used.
    If not, but there are primary references in bio.tools, the most recent one is selected as the preferred citation.
    Otherwise, the most recent reference of any other type is chosen.


    Parameters
    ----------
    references : list[Publication | dict[str, Any]]
        List of all publications.
    bt_primary_references: list[Publication]
        List of publications in bio.tools marked as primary.
    gh_preferred_reference : dict[str, Any] | None, optional
        The preferred citation from GitHub CITATION.cff, if any.

    Returns
    -------
    Publication | dict[str, Any] | None
        The selected preferred citation, or None if no references are available.
    """
    if gh_preferred_reference is not None:
        return gh_preferred_reference
    selection_list = bt_primary_references if bt_primary_references else references
    if not selection_list:
        return None
    preferred = max(selection_list, key=_key_func)
    return preferred


def _compose_base_cff(bt_params: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a base CITATION.cff dict from bio.tools metadata.

    Parameters
    ----------
    bt_params : dict[str, Any]
        The bio.tools tool relevant metadata as a dictionary.
        Should contain:
        - name - Name of the tool.
        - biotoolsID - bio.tools identifier of the tool.
        - homepage - Homepage URL of the tool.
        - license - License of the tool.
        - topic - List of topics associated with the tool.
        - description - Description of the tool.

    Returns
    -------
    dict[str, Any]
        A dictionary with the CITATION.cff base content.
    """
    name = bt_params.get("name", None)
    biotools_id = bt_params.get("biotoolsID", None)
    homepage = bt_params.get("homepage", None)
    license = bt_params.get("license", None)
    topic = bt_params.get("topic", None)
    description = bt_params.get("description", None)

    base_cff = normalize_dict_strings(
        {
            "cff-version": "1.2.0",
            "title": name or biotools_id,
            "version": None,
            "type": "software",
            "repository": homepage,
            "identifiers": [{"type": "other", "value": biotools_id, "description": "bio.tools"}],
            "license": license,
            "keywords": topic,
            "abstract": description,
        }
    )
    return base_cff


def _extract_gh_references(
    gh_citation_cff: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """
    Extract references and preferred-citation from an existing CITATION.cff dict.

    Parameters
    ----------
    gh_citation_cff : dict[str, Any] | None
        The existing CITATION.cff content from the GitHub repository.

    Returns
    -------
    tuple[list[dict[str, Any]], dict[str, Any] | None]
        A tuple containing:
        - A list of references extracted from the CITATION.cff.
        - The preferred-citation extracted from the CITATION.cff, or None if not present
    """
    if not gh_citation_cff:
        return [], None

    gh_citation_cff = normalize_dict_strings(gh_citation_cff)

    gh_references = gh_citation_cff.get("references") or []
    gh_references = [r for r in gh_references if isinstance(r, Mapping)]

    gh_preferred = gh_citation_cff.get("preferred-citation")
    if isinstance(gh_preferred, Mapping):
        gh_preferred = dict(gh_preferred)  # shallow copy
    else:
        gh_preferred = None

    # ensure preferred-citation is included in references if present
    if gh_preferred is not None:
        pref_ids = _ref_ids(gh_preferred)
        in_refs = any(_ref_ids(r) & pref_ids for r in gh_references)
        if not in_refs:
            gh_references.append(gh_preferred)

    if gh_references:
        logger.note(
            f"CITATION.cff is not empty. Found {len(gh_references)} reference(s) to merge with bio.tools metadata."
        )
    else:
        logger.note("CITATION.cff exists but contains no references. Using only bio.tools metadata.")

    return gh_references, gh_preferred


def _compose_citation(
    base_cff: dict[str, Any],
    references: list[Publication | dict[str, Any]],
    preferred: Publication | dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Generate a CITATION.cff dict from bio.tools metadata and references.
    If there are no references, a minimal CITATION.cff is created.

    Parameters
    ----------
    base_cff : dict[str, Any]
        The base CITATION.cff content.
    references : list[Publication | dict[str, Any]]
        List of all publications to be included in CITATION.cff.
    preferred : Publication | dict[str, Any] | None
        The selected preferred citation to be included in CITATION.cff, if any.

    Returns
    -------
    dict[str, Any]
        A dictionary with the CITATION.cff content.
    """
    if not references:
        base_cff["message"] = "If you use this software, please cite it using this CITATION.cff."
        logger.added(
            "No publications found in bio.tools or existing CITATION.cff. Creating CITATION.cff with minimal metadata."
        )
    else:
        update_data = {
            "message": ("If you use this software, please cite it and the Primary publications below."),
            "references": object_to_primitive(references),
        }
        if preferred is not None:
            update_data["preferred-citation"] = object_to_primitive(preferred)

        base_cff.update(normalize_dict_strings(update_data))
        logger.added(f"Added {len(references)} publication(s) to CITATION.cff.")

    return base_cff


async def map_citation(gh_citation_cff: dict[str, Any], bt_params: dict[str, Any]) -> dict[str, str]:
    """
    Generate CITATION.cff content from the publications of a bio.tools tool.
    It uses Europe PMC to resolve publication metadata.

    Parameters
    ----------
    gh_citation_cff : dict[str, Any]
        The existing CITATION.cff content from the GitHub repository.
    bt_params : dict[str, Any]
        The bio.tools tool relevant metadata as a dictionary.
        Should contain:
        - publication - List of publication items from bio.tools metadata.
        - name - Name of the tool.
        - biotoolsID - bio.tools identifier of the tool.
        - homepage - Homepage URL of the tool.
        - license - License of the tool.
        - topic - List of topics associated with the tool.
        - description - Description of the tool.

    Returns
    -------
    dict[str, str]
        A dictionary with the filename as key and the CITATION.cff content as value.
    """
    bt_publication = bt_params.get("publication", None)

    bt_references: list[Publication] = []
    bt_primary_references: list[Publication] = []

    gh_references, gh_preferred = _extract_gh_references(gh_citation_cff)

    for pub in bt_publication or []:
        try:
            epmc_publication = await compose_europe_pmc_metadata(
                pmid=pub.pmid,
                pmcid=pub.pmcid,
                doi=pub.doi,
            )
            empc_publication_norm = normalize_pydantic_model_strings(epmc_publication)
            bt_references.append(empc_publication_norm)
            if pub.type and TypeEnum2.Primary in pub.type:
                bt_primary_references.append(empc_publication_norm)
        except Exception as e:
            logger.note(f"Could not resolve publication {pub}: {e}")

    references = _deduplicate_references(gh_references + bt_references)

    preferred_reference = _choose_preferred_citation(
        references=references,
        bt_primary_references=bt_primary_references,
        gh_preferred_reference=gh_preferred,
    )

    base_cff = _compose_base_cff(bt_params=bt_params)
    cff = _compose_citation(base_cff=base_cff, references=references, preferred=preferred_reference)

    return {"CITATION.cff": yaml.dump(cff, sort_keys=False, allow_unicode=True)}
