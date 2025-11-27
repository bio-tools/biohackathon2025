"""
Generate a CITATION.cff file from bio.tools publication metadata.

This module retrieves publications from a bio.tools entry,
resolves them via the Europe PMC REST API, and converts
the resulting bibliographic information into the Citation File Format (CFF).
The output is a valid `CITATION.cff` file that can be committed to a GitHub
repository to enable software citation.
"""

from collections.abc import Hashable, Mapping
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


def _ref_key(ref: Publication | Mapping[str, Any]) -> Hashable:
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
        current_ids = _ref_key(ref)

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


def _compose_citation(
    base_cff: dict[str, Any],
    references: list[Publication | dict[str, Any]],
    primary_references: list[Publication | dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate a CITATION.cff dict from bio.tools metadata and references.
    If there are no references, a minimal CITATION.cff is created.
    If there are primary references, most recent one of them is selected as preferred citation.
    Otherwise, the most recent reference is selected.

    Parameters
    ----------
    base_cff : dict[str, Any]
        The base CITATION.cff content.
    references : list[Publication | dict[str, Any]]
        List of all publications to be included in CITATION.cff.
    primary_references : list[Publication | dict[str, Any]]
        List of publications marked as primary to be included in CITATION.cff.

    Returns
    -------
    dict[str, Any]
        A dictionary with the CITATION.cff content.
    """

    def key_func(r):
        if isinstance(r, Publication):
            return (r.year or 0, r.title or "")
        return (r.get("year", 0) or 0, r.get("title", "") or "")

    if not references:
        base_cff["message"] = "If you use this software, please cite it using this CITATION.cff."
        logger.added("No publications found in bio.tools. Creating CITATION.cff with minimal metadata.")
    else:
        selection_list_for_preferred = primary_references if primary_references else references
        preferred = max(selection_list_for_preferred, key=key_func)
        base_cff.update(
            {
                "message": ("If you use this software, please cite it and the Primary publications below."),
                "preferred-citation": object_to_primitive(preferred),
                "references": object_to_primitive(references),
            }
        )
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

    Raises
    ------
    SystemExit
        If no primary publications could be resolved.
    """
    bt_publication = bt_params.get("publication", None)

    bt_references: list[Publication] = []
    bt_primary_references: list[Publication] = []

    gh_references: list[dict[str, Any]] = 1  # TODO using gh_citation_cff

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

    _deduplicate_references(bt_references + gh_references)

    base_cff = _compose_base_cff(bt_params=bt_params)
    cff = _compose_citation(base_cff=base_cff, references=bt_references, primary_references=bt_primary_references)

    return {"CITATION.cff": yaml.dump(cff, sort_keys=False, allow_unicode=True)}
