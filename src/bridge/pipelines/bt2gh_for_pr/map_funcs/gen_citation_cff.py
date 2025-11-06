"""
Generate a CITATION.cff file from bio.tools publication metadata.

This module retrieves metadata for a given bio.tools entry, identifies its
Primary publications, resolves them via the Europe PMC REST API, and converts
the resulting bibliographic information into the Citation File Format (CFF).
The output is a valid `CITATION.cff` file that can be committed to a GitHub
repository to enable software citation.
"""

import sys

import yaml

from bridge.builders import compose_europe_pmc_metadata
from bridge.core import BiotoolsToolModel, Publication
from bridge.core.biotools import PublicationItem, TypeEnum2

TIMEOUT = 20


def _require_primary_publications(meta: BiotoolsToolModel) -> list[PublicationItem]:
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
    pubs = meta.publication or []
    primary = [p for p in pubs if p.type and TypeEnum2.Primary in p.type]
    if not primary:
        raise LookupError("No primary publication found in ToolModel.publication.")
    return primary


async def main(meta: BiotoolsToolModel) -> dict[str, str]:
    """
    Generate CITATION.cff content from the primary publications of a bio.tools tool.
    It uses Europe PMC to resolve publication metadata.

    Parameters
    ----------
    meta : BiotoolsToolModel
        The bio.tools tool metadata model.

    Returns
    -------
    dict[str, str]
        A dictionary with the filename as key and the CITATION.cff content as value.

    Raises
    ------
    SystemExit
        If no primary publications could be resolved.
    """
    primary_publications = _require_primary_publications(meta)
    references: list[Publication] = []

    for primary_pub in primary_publications:
        try:
            epmc_publication = await compose_europe_pmc_metadata(
                pmid=primary_pub.pmid,
                pmcid=primary_pub.pmcid,
                doi=primary_pub.doi,
            )
            references.append(epmc_publication)
        except Exception as e:
            print(f"Warning: could not resolve {primary_pub}: {e}", file=sys.stderr)

    if not references:
        # Compose CITATION.cff without publications
        cff = {
            "cff-version": "1.2.0",
            "message": "If you use this software, please cite it using this CITATION.cff.",
            # Minimal software metadata inferred from bio.tools
            "title": meta.name or meta.biotoolsID,
            "version": None,
            "type": "software",
            "repository": meta.homepage,
            "identifiers": [{"type": "other", "value": meta.biotoolsID, "description": "bio.tools"}],
            "license": meta.license,
            "keywords": meta.topic,
            "abstract": meta.description,
        }
        return {"CITATION.cff": yaml.dump(cff, sort_keys=False)}
        raise SystemExit("Resolved 0 Primary publications; creating CITATION.cff without publications.")

    # Choose one preferred-citation (e.g., the most recent Primary, or first and most recent)
    preferred = max(references, key=lambda r: (r.year or 0, r.title or ""))

    # Compose CITATION.cff with publication(s)
    cff = {
        "cff-version": "1.2.0",
        "message": "If you use this software, please cite it and the Primary publications below.",
        # Minimal software metadata inferred from bio.tools
        "title": meta.name or meta.biotoolsID,
        "version": None,
        "type": "software",
        "repository": meta.homepage,
        "preferred-citation": preferred,
        "references": references,
        "identifiers": [{"type": "other", "value": meta.biotoolsID, "description": "bio.tools"}],
        "license": meta.license,
        "keywords": meta.topic,
        "abstract": meta.description,
    }

    return {"CITATION.cff": yaml.dump(cff, sort_keys=False)}
