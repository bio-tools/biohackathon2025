"""
Generate a CITATION.cff file from bio.tools publication metadata.

This module retrieves metadata for a given bio.tools entry, identifies its
Primary publications, resolves them via the Europe PMC REST API, and converts
the resulting bibliographic information into the Citation File Format (CFF).
The output is a valid `CITATION.cff` file that can be committed to a GitHub
repository to enable software citation.

Functions
---------
epmc_lookup_by_ids(pmid=None, pmcid=None, doi=None)
    Retrieve a publication record from Europe PMC using one or more identifiers.
author_list_to_cff(epmc)
    Convert an EPMC-style author list to a CFF-compatible structure.
page_range(epmc)
    Extract start and end page numbers from a Europe PMC record.
epmc_to_cff_reference(epmc)
    Map a Europe PMC record to a CFF-formatted reference dictionary.
main(biotools_id, outfile="CITATION.cff")
    Build and write the complete CFF file for a specified bio.tools entry.

Notes
-----
Part of the BioHackathon Europe 2025 project *“Bidirectional bridge: GitHub ⇄ bio.tools.”*
Requires network access to the bio.tools and Europe PMC APIs.

Example
-------
Run from the command line:

    poetry run python bh2gh_publications_to_citationscff.py compareMS2 CITATION.cff
"""

import re
import sys

import requests
import yaml

TIMEOUT = 20


def epmc_lookup_by_ids(pmid=None, pmcid=None, doi=None):
    """
    Retrieve a publication record from Europe PMC using one or more identifiers.

    The function sequentially queries the Europe PMC REST API with the provided
    PubMed ID (PMID), PubMed Central ID (PMCID), or Digital Object Identifier (DOI),
    returning the first matching record in JSON format.

    Parameters
    ----------
    pmid : str, optional
        PubMed identifier (e.g., "36173614").
    pmcid : str, optional
        PubMed Central identifier (e.g., "PMC9903320").
    doi : str, optional
        Digital Object Identifier (e.g., "10.1021/acs.jproteome.2c00457").

    Returns
    -------
    dict or None
        A dictionary representing the first matching Europe PMC record,
        or None if no record is found.

    Raises
    ------
    requests.HTTPError
        If the HTTP request to the Europe PMC API fails.
    requests.Timeout
        If the request exceeds the configured TIMEOUT.
    """
    base = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    # Try a sequence of Europe PMC queries, first exact (should work), then fallbacks.
    queries = []
    if pmid:
        queries.append(f"EXT_ID:{pmid} AND SRC:MED")
    if pmcid:
        queries.append(f"EXT_ID:{pmcid} AND SRC:PMC")
    if doi:
        queries.extend([f"DOI:{doi}", f'EXT_ID:"{doi}"'])  # DOI query variants

    for q in queries:
        r = requests.get(
            base,
            params={"query": q, "format": "json", "resultType": "core", "pageSize": 1},
            headers={"Accept": "application/json"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        res = data.get("resultList", {}).get("result", [])
        if res:
            return res[0]
    return None


def author_list_to_cff(epmc):
    """
    Convert an EPMC-style author list dictionary to a CFF-compatible author list.

    Parameters
    ----------
    epmc : dict
        Dictionary representing a record (as returned by Europe PMC),
        expected to contain an "authorList" key with nested "author" entries.

    Returns
    -------
    list of dict
        A list of author dictionaries formatted according to the
        Citation File Format (CFF) specification, where each entry contains
        "family-names" and "given-names" or a combined "name" field.
    """
    out = []
    for a in epmc.get("authorList", {}).get("author", []):
        if a.get("lastName") or a.get("firstName"):
            out.append({"family-names": a.get("lastName", ""), "given-names": a.get("firstName", "")})
        elif a.get("fullName"):
            out.append({"name": a["fullName"]})
    return out


def page_range(epmc):
    """
    Extract the page range from an Europe PMC record.

    Parses the "pageInfo" field of an EPMC record and returns the start and end
    page numbers, if available. Supports both hyphen and en-dash separators.

    Parameters
    ----------
    epmc : dict
        Dictionary representing a Europe PMC record, expected to contain a
        "pageInfo" key with page information (e.g., "514–519").

    Returns
    -------
    tuple of (str or None, str or None)
        A tuple containing the start and end pages. If the page information
        cannot be parsed, both values are None.
    """
    pg = epmc.get("pageInfo") or ""
    m = re.match(r"^\s*([\w\-]+)\s*[-–]\s*([\w\-]+)\s*$", pg)
    return (m.group(1), m.group(2)) if m else (None, None)


def epmc_to_cff_reference(epmc):
    """
    Convert a Europe PMC record to a Citation File Format (CFF) reference entry.

    Extracts bibliographic metadata from an EPMC record and maps it to fields
    compatible with the Citation File Format (CFF) specification. Page range,
    author list, and publication year are parsed and normalized.

    Parameters
    ----------
    epmc : dict
        Dictionary representing a publication record retrieved from Europe PMC.
        Expected to contain fields such as "title", "authorList", "journalTitle",
        "pubYear" or "pubYearOrRange", "issue", "journalVolume", "pageInfo", and
        optionally "doi".

    Returns
    -------
    dict
        A dictionary representing the reference in CFF format, including keys such as
        "type", "title", "authors", "year", "journal", "volume", "issue",
        "start", "end", and optionally "doi".
    """
    start, end = page_range(epmc)
    year = None
    if epmc.get("pubYear"):
        year = int(epmc["pubYear"])
    elif epmc.get("pubYearOrRange"):
        year = int(epmc["pubYearOrRange"].split("-")[0])

    ref = {
        "type": "article",
        "title": epmc.get("title"),
        "authors": author_list_to_cff(epmc),
        "year": year,
        "journal": epmc.get("journalTitle"),
        "volume": epmc.get("journalVolume"),
        "issue": epmc.get("issue"),
    }
    if start:
        ref["start"] = start
    if end:
        ref["end"] = end
    if epmc.get("doi"):
        ref["doi"] = epmc["doi"]
    return ref


def main(biotools_id, outfile="CITATION.cff"):
    """
    Generate a CITATION.cff file for a bio.tools entry based on its Primary publications.

    This function retrieves metadata for a given bio.tools identifier, extracts
    Primary publication references, resolves their metadata via Europe PMC, and
    writes a complete Citation File Format (CFF) file suitable for software citation.

    Parameters
    ----------
    biotools_id : str
        The bio.tools identifier of the software entry (e.g., "proteomics-tool").
    outfile : str, optional
        Output filename for the generated CFF file. Defaults to "CITATION.cff".

    Raises
    ------
    SystemExit
        If no Primary publications are found or none can be resolved.
    requests.HTTPError
        If the bio.tools API request fails.
    requests.Timeout
        If a network timeout occurs when contacting bio.tools or Europe PMC.

    Side Effects
    ------------
    Writes a YAML-formatted CFF file to disk and prints a summary message to stdout.

    Notes
    -----
    The function is designed for command-line execution but can also be called
    programmatically. It depends on helper functions for resolving Europe PMC
    records and formatting them as CFF references.
    """
    # 1) Fetch the bio.tools record
    url = f"https://bio.tools/api/tool/{biotools_id}/?format=json"
    r = requests.get(url, headers={"Accept": "application/json"}, timeout=TIMEOUT)
    r.raise_for_status()
    tool = r.json()

    # 2) Collect "Primary" publications
    prim = []
    for pub in tool.get("publication", []):
        types = pub.get("type") or []
        if any(t.lower() == "primary" for t in types if isinstance(t, str)):
            prim.append({"pmid": pub.get("pmid"), "pmcid": pub.get("pmcid"), "doi": pub.get("doi")})

    if not prim:
        raise SystemExit(f'No "Primary" publications for {biotools_id}')

    # 3) Resolve each via Europe PMC and convert to CFF references
    references = []
    for p in prim:
        epmc = epmc_lookup_by_ids(pmid=p["pmid"], pmcid=p["pmcid"], doi=p["doi"])
        if not epmc:
            print(f"Warning: could not resolve {p}", file=sys.stderr)
            continue
        references.append(epmc_to_cff_reference(epmc))

    if not references:
        raise SystemExit("Resolved 0 Primary publications; aborting.")

    # Choose one preferred-citation (e.g., the most recent Primary, or first and most recent)
    preferred = max(references, key=lambda r: (r.get("year") or 0, r.get("title") or ""))

    # 4) Compose CITATION.cff
    cff = {
        "cff-version": "1.2.0",
        "message": "If you use this software, please cite it and the Primary publications below.",
        # Minimal software metadata inferred from bio.tools
        "title": tool.get("name") or biotools_id,
        "version": None,
        "type": "software",
        "preferred-citation": preferred,
        "references": references,
    }

    with open(outfile, "w", encoding="utf-8") as f:
        yaml.safe_dump(cff, f, sort_keys=False, allow_unicode=True)
    print(f"Wrote {outfile} with {len(references)} Primary publication(s).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: poetry run python bh2gh_publications_to_citationscff.py <biotools_id> [outfile]")
    biotools_id = sys.argv[1]
    outfile = sys.argv[2] if len(sys.argv) > 2 else "CITATION.cff"
    main(biotools_id, outfile)
