"""
Generate a CITATION.cff file from bio.tools publication metadata.

This module retrieves publications from a bio.tools entry, resolves them via the
Europe PMC REST API, and converts the resulting bibliographic information into
the Citation File Format (CFF).

If a CITATION.cff already exists in the GitHub repository, its non-publication
metadata is preserved where present, and its publication list is merged with
publications discovered via bio.tools / Europe PMC. References are
deduplicated, and a preferred citation is chosen with a clear precedence:
existing preferred-citation (if any) > bio.tools primary publications > other
publications.
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


def _ref_ids(ref: Publication | Mapping[str, Any]) -> set[str]:
    """
    Extract a normalized set of identifiers for a publication-like object.
    This function collects all available identifiers and returns
    them as normalized strings, which can then be used for deduplication.

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
    Key function for ordering publications by recency and title.

    Publications are ordered primarily by year (descending when used with `max`)
    and secondarily by title (lexicographically). This is used to select a
    "most recent" publication when choosing a preferred citation.

    Parameters
    ----------
    r : Publication | dict[str, Any]
        The publication to evaluate, as either a `Publication` instance or a
        reference dictionary.

    Returns
    -------
    tuple[int, str]
        A tuple `(year, title)` suitable for use as a sort key.
        Missing years are treated as 0; missing titles as an empty string.
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
    Select the preferred citation among all available references.

    Precedence rules:
    1. If the existing GitHub CITATION.cff contains a `preferred-citation`,
       it is preserved and returned unchanged.
    2. Otherwise, if there are primary publications in the bio.tools metadata,
       the most recent primary publication is selected.
    3. Otherwise, the most recent publication from the full reference list
       is selected.
    4. If no references are available, returns ``None``.

    Parameters
    ----------
    references : list[Publication | dict[str, Any]]
        List of all resolved references.
    bt_primary_references: list[Publication]
        List (subset) of bio.tools publications that are marked as primary.
    gh_preferred_reference : dict[str, Any] | None, optional
        Existing `preferred-citation` from a CITATION.cff file, if any.

    Returns
    -------
    Publication | dict[str, Any] | None
        The selected preferred citation, or ``None`` if no references exist.
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
    Build a base CITATION.cff structure from bio.tools tool metadata.

    This function creates a minimal, publication-agnostic CFF dictionary based
    on the fields exposed in the bio.tools API. It does not include any
    references or preferred-citation; those are added later.

    Parameters
    ----------
    bt_params : dict[str, Any]
        The bio.tools tool metadata as a dictionary.
        Expected keys include:
        - 'name'       : Name of the tool.
        - 'biotoolsID' : bio.tools identifier of the tool.
        - 'homepage'   : Homepage or repository URL of the tool.
        - 'license'    : License identifier.
        - 'topic'      : List of topics associated with the tool.
        - 'description': Textual description of the tool.

    Returns
    -------
    dict[str, Any]
        A base CFF dictionary containing core tool metadata
        and a `cff-version` of 1.2.0.
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


def _merge_top_level_metadata(
    existing_cff: dict[str, Any] | None,
    base_cff: dict[str, Any],
) -> dict[str, Any]:
    """
    Merge top-level metadata from an existing CITATION.cff with bio.tools metadata.

    Policy:
    - If no existing CITATION.cff is provided, `base_cff` is returned as-is.
    - Otherwise, start from the existing CFF.
    - For keys present in `base_cff`:
      - If the existing CFF has a non-empty value, it is kept.
      - If the existing value is missing or empty (None, "", []), the value
        from `base_cff` is used.
    - The keys 'references' and 'preferred-citation' are removed here and are
      handled separately by publication-specific logic.

    Parameters
    ----------
    existing_cff : dict[str, Any] | None
        The parsed content of an existing CITATION.cff file,
        or ``None`` if no file exists.
    base_cff : dict[str, Any]
        The base CFF content derived from bio.tools metadata.

    Returns
    -------
    dict[str, Any]
        A merged CFF dictionary containing top-level metadata from both
        sources, with existing values preserved where present.
    """
    if existing_cff is None:
        return base_cff

    merged = dict(existing_cff)

    # handle preferred and references separately
    merged.pop("references", None)
    merged.pop("preferred-citation", None)

    # add bio.tools metadata where missing
    for key, val in base_cff.items():
        if val is None:
            continue

        existing_val = merged.get(key, None)
        if existing_val in (None, "", []):
            merged[key] = val

    return merged


def _extract_gh_references(
    gh_citation_cff: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """
    Extract publication information from an existing CITATION.cff dictionary.

    This helper parses an existing CFF structure and returns:
    - the list of reference entries, and
    - the preferred-citation entry, if present.

    The preferred citation is ensured to be part of the references list:
    if it is not already present, it is appended.

    Parameters
    ----------
    gh_citation_cff : dict[str, Any] | None
        TParsed content of an existing CITATION.cff file,
        or ``None`` if no file exists.

    Returns
    -------
    tuple[list[dict[str, Any]], dict[str, Any] | None]
        A tuple of:
        - A list of reference dictionaries extracted from the CFF.
        - The preferred-citation dictionary, or ``None`` if not present.
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
    Combine top-level metadata and publication information into a CFF structure.

    This function takes a base CFF dictionary (already merged with any
    existing CITATION.cff metadata), a list of references, and an optional
    preferred-citation, and produces the final CFF dictionary that will be
    written to `CITATION.cff`.

    Behaviour:
    - If no references are provided, a minimal CFF file is created with a
      generic citation message.
    - If references exist, they are added as a `references` list, and a
      `preferred-citation` entry is included if one was selected.

    Parameters
    ----------
    base_cff : dict[str, Any]
        The top-level CFF metadata.
    references : list[Publication | dict[str, Any]]
        All references to include in the CFF file.
    preferred : Publication | dict[str, Any] | None
        The preferred citation to include, or ``None`` if no preferred
        citation should be set.

    Returns
    -------
    dict[str, Any]
        The complete CFF dictionary.
    """
    if not references:
        base_cff["message"] = "If you use this software, please cite it using this CITATION.cff."
        logger.added(
            "No publications found in bio.tools or existing CITATION.cff. Creating CITATION.cff with minimal metadata."
        )
    else:
        update_data = {
            "message": ("If you use this software, please cite it and the Primary publications below."),
            "references": references,
        }
        if preferred is not None:
            update_data["preferred-citation"] = preferred

        base_cff.update(normalize_dict_strings(update_data))
        logger.added(f"Added {len(references)} publication(s) to CITATION.cff.")

    return base_cff


async def map_citation(gh_citation_cff: dict[str, Any], bt_params: dict[str, Any]) -> dict[str, str]:
    """
    Generate or update a CITATION.cff file based on bio.tools and Europe PMC metadata.

    Steps performed:
    1. Reads publication metadata from a bio.tools tool entry.
    2. Resolves each publication via the Europe PMC API to obtain
       bibliographic metadata.
    3. Optionally parses an existing CITATION.cff (if provided) and extracts
       existing references and a preferred-citation.
    4. Merges existing references and new references, deduplicating based on
       DOI/PMID/PMCID/title.
    5. Chooses a preferred citation following the configured precedence rules.
    6. Merges top-level metadata from the existing CFF and bio.tools.
    7. Returns a dictionary mapping `"CITATION.cff"` to the YAML-serialized
       CFF content.

    Parameters
    ----------
    gh_citation_cff : dict[str, Any]
        Parsed content of an existing CITATION.cff file from the GitHub
        repository, or ``None`` if no file exists.
    bt_params : dict[str, Any]
        The bio.tools tool metadata as a dictionary.
        Expected keys include:
        - 'publication' : list of publication items from bio.tools metadata.
        - 'name'        : name of the tool.
        - 'biotoolsID'  : bio.tools identifier.
        - 'homepage'    : homepage or repository URL.
        - 'license'     : license identifier.
        - 'topic'       : list of topics.
        - 'description' : description of the tool.

    Returns
    -------
    dict[str, str]
        A dictionary with the filename `"CITATION.cff"` as key,
        and the YAML-formatted CFF content as value.
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
    base_cff = _merge_top_level_metadata(existing_cff=gh_citation_cff, base_cff=base_cff)
    cff = _compose_citation(base_cff=base_cff, references=references, preferred=preferred_reference)
    primitive_cff = object_to_primitive(cff)

    return {"CITATION.cff": yaml.dump(primitive_cff, sort_keys=False, allow_unicode=True)}
