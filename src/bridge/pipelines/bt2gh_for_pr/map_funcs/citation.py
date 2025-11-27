"""
Generate a CITATION.cff file from bio.tools publication metadata.

This module retrieves metadata for a given bio.tools entry, identifies its
Primary publications, resolves them via the Europe PMC REST API, and converts
the resulting bibliographic information into the Citation File Format (CFF).
The output is a valid `CITATION.cff` file that can be committed to a GitHub
repository to enable software citation.
"""

import sys
from typing import Any

import yaml

from bridge.builders import compose_europe_pmc_metadata
from bridge.core import Publication
from bridge.core.biotools import PublicationItem, TypeEnum2
from bridge.pipelines.utils import normalize_dict_strings, normalize_pydantic_model_strings, object_to_primitive

# TODO: add logging

TIMEOUT = 20


def _require_primary_publications(bt_publication: list[PublicationItem] | None) -> list[PublicationItem]:
    """
    Return the PublicationItem marked as Primary, if exists.

    Parameters
    ----------
    meta : BiotoolsToolModel
        The bio.tools tool metadata model.

    Returns
    -------
    PublicationItem
        The PublicationItem marked as Primary.

    Raises
    ------
    LookupError
        If no Primary publication is found in the provided metadata.
    """
    pubs = bt_publication or []
    primary = [p for p in pubs if p.type and TypeEnum2.Primary in p.type]
    if not primary:
        raise LookupError("No primary publication found in ToolModel.publication.")
    return primary


def _compose_citation(bt_params: dict[str, Any], references: list[Publication]):
    """Generate a CITATION.cff dict from bio.tools metadata and references."""
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

    if not references:
        base_cff["message"] = "If you use this software, please cite it using this CITATION.cff."
        print("Resolved 0 Primary publications; creating CITATION.cff without publications.")
    else:
        preferred = max(references, key=lambda r: (r.year or 0, r.title or ""))
        base_cff.update(
            {
                "message": ("If you use this software, please cite it and the Primary publications below."),
                "preferred-citation": preferred,
                "references": references,
            }
        )

    primitive_cff = object_to_primitive(base_cff)
    return {"CITATION.cff": yaml.dump(primitive_cff, sort_keys=False, allow_unicode=True)}


async def map_citation(gh_citation_cff_exists: bool, bt_params: dict[str, Any]) -> dict[str, str]:
    """
    Generate CITATION.cff content from the primary publications of a bio.tools tool.
    It uses Europe PMC to resolve publication metadata.

    Parameters
    ----------
    gh_citation_cff_exists : bool
        Whether a CITATION.cff file already exists in the GitHub repository.
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
    if gh_citation_cff_exists:
        raise SystemExit("CITATION.cff already exists in the GitHub repository; skipping creation.")

    bt_publication = bt_params.get("publication", None)

    primary_publications = _require_primary_publications(bt_publication)
    references: list[Publication] = []

    for primary_pub in primary_publications:
        try:
            epmc_publication = await compose_europe_pmc_metadata(
                pmid=primary_pub.pmid,
                pmcid=primary_pub.pmcid,
                doi=primary_pub.doi,
            )
            empc_publication_norm = normalize_pydantic_model_strings(epmc_publication)
            references.append(empc_publication_norm)
        except Exception as e:
            print(f"Warning: could not resolve {primary_pub}: {e}", file=sys.stderr)

    cff = _compose_citation(bt_params=bt_params, references=references)

    return cff
