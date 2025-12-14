"""
Unit tests for generating/updating CITATION.cff from bio.tools publications (map_citation).

These tests validate the *public* behavior of map_citation:
- minimal CFF output when no references exist
- preferred-citation precedence:
    existing GH preferred > bio.tools Primary (most recent) > most recent overall
- merging existing top-level metadata while preserving non-empty values
- merge order: GH references come first, then bio.tools-resolved references
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import yaml

import bridge.pipelines.bt2gh_for_pr_issues.map_funcs.citation as mod

pytestmark = pytest.mark.asyncio

TITLE = "CITATION.cff"


# -----------------------------
# Helpers
# -----------------------------


def BT_PUB(*, doi=None, pmid=None, pmcid=None, type_=None):
    """
    Minimal stand-in for a bio.tools PublicationItem-like object.
    map_citation accesses: .doi .pmid .pmcid .type
    """
    return SimpleNamespace(doi=doi, pmid=pmid, pmcid=pmcid, type=type_)


def _load_yaml(out: dict[str, str]) -> dict:
    assert list(out.keys()) == [TITLE]
    return yaml.safe_load(out[TITLE])


def _refs(cff: dict) -> list[dict]:
    return cff.get("references") or []


# -----------------------------
# Fixtures: patch external deps
# -----------------------------


@pytest.fixture()
def patch_citation_deps(monkeypatch):
    """
    Patch external dependencies so tests don't hit the network and remain deterministic.

    Important: we do NOT patch deduplicate_references or extract_cff_references here.
    Those are separately tested, and patching them here would make these tests
    diverge from real behavior.
    """

    async def _compose_europe_pmc_metadata(*, pmid=None, pmcid=None, doi=None):
        # Deterministic "resolved" publication payloads.
        # Include year/title so preferred selection can work.
        if doi == "10.5555/primary-2023":
            return {"doi": doi, "title": "Primary paper", "year": 2023}
        if doi == "10.5555/primary-2020":
            return {"doi": doi, "title": "Older primary paper", "year": 2020}
        if doi == "10.5555/other-2024":
            return {"doi": doi, "title": "Other paper", "year": 2024}
        if doi == "10.1111/gh-ref":
            return {"doi": doi, "title": "GH ref resolved", "year": 2019}
        return {"doi": doi, "title": "Unknown", "year": 2000}

    monkeypatch.setattr(mod, "compose_europe_pmc_metadata", _compose_europe_pmc_metadata)

    # We return dicts already, so these can be identity.
    monkeypatch.setattr(mod, "normalize_pydantic_model_strings", lambda x: x)
    monkeypatch.setattr(mod, "object_to_primitive", lambda x: x)


# -----------------------------
# Tests
# -----------------------------


async def test_map_citation_minimal_cff_when_no_refs(monkeypatch, patch_citation_deps):
    # No GH refs, no BT publications
    monkeypatch.setattr(mod, "extract_cff_references", lambda _cff: ([], None))

    bt_params = {
        "name": "ToolName",
        "biotoolsID": "toolid",
        "homepage": "https://example.org",
        "license": "MIT",
        "topic": ["bioinformatics"],
        "description": "A tool.",
        "publication": None,
    }

    out = await mod.map_citation(gh_citation_cff={}, bt_params=bt_params)
    cff = _load_yaml(out)

    assert cff["cff-version"] == "1.2.0"
    assert cff["type"] == "software"
    assert cff["title"] == "ToolName"
    assert "message" in cff
    assert "references" not in cff
    assert "preferred-citation" not in cff


async def test_map_citation_prefers_existing_gh_preferred_citation(monkeypatch, patch_citation_deps):
    gh_refs = [{"doi": "10.1111/gh-ref", "title": "GH ref", "year": 2019}]
    gh_preferred = {"doi": "10.2222/gh-preferred", "title": "GH preferred", "year": 2018}
    monkeypatch.setattr(mod, "extract_cff_references", lambda _cff: (gh_refs, gh_preferred))

    bt_params = {
        "name": "ToolName",
        "biotoolsID": "toolid",
        "homepage": None,
        "license": None,
        "topic": None,
        "description": None,
        "publication": [
            BT_PUB(doi="10.5555/primary-2023", type_=[mod.TypeEnum2.Primary]),
        ],
    }

    out = await mod.map_citation(gh_citation_cff={"some": "cff"}, bt_params=bt_params)
    cff = _load_yaml(out)

    # Preferred must be preserved exactly as provided by extract_cff_references
    assert cff["preferred-citation"]["doi"] == "10.2222/gh-preferred"
    assert cff["preferred-citation"]["title"] == "GH preferred"

    # Both GH refs and BT refs can appear in references (after merge/dedupe)
    dois = [r.get("doi") for r in _refs(cff)]
    assert "10.1111/gh-ref" in dois
    assert "10.5555/primary-2023" in dois


async def test_map_citation_prefers_most_recent_primary_when_no_gh_preferred(monkeypatch, patch_citation_deps):
    monkeypatch.setattr(mod, "extract_cff_references", lambda _cff: ([], None))

    bt_params = {
        "name": "ToolName",
        "biotoolsID": "toolid",
        "homepage": None,
        "license": None,
        "topic": None,
        "description": None,
        "publication": [
            BT_PUB(doi="10.5555/primary-2020", type_=[mod.TypeEnum2.Primary]),
            BT_PUB(doi="10.5555/primary-2023", type_=[mod.TypeEnum2.Primary]),
            BT_PUB(doi="10.5555/other-2024", type_=None),
        ],
    }

    out = await mod.map_citation(gh_citation_cff={}, bt_params=bt_params)
    cff = _load_yaml(out)

    assert len(_refs(cff)) == 3

    # Preferred should be most recent *PRIMARY* -> 2023, not the 2024 "other"
    pref = cff["preferred-citation"]
    assert pref["doi"] == "10.5555/primary-2023"
    assert pref["year"] == 2023


async def test_map_citation_prefers_most_recent_overall_when_no_primary(monkeypatch, patch_citation_deps):
    monkeypatch.setattr(mod, "extract_cff_references", lambda _cff: ([], None))

    bt_params = {
        "name": "ToolName",
        "biotoolsID": "toolid",
        "homepage": None,
        "license": None,
        "topic": None,
        "description": None,
        "publication": [
            BT_PUB(doi="10.5555/primary-2020", type_=None),
            BT_PUB(doi="10.5555/other-2024", type_=None),
        ],
    }

    out = await mod.map_citation(gh_citation_cff={}, bt_params=bt_params)
    cff = _load_yaml(out)

    assert len(_refs(cff)) == 2

    # No primary => most recent overall should win -> 2024
    pref = cff["preferred-citation"]
    assert pref["doi"] == "10.5555/other-2024"
    assert pref["year"] == 2024


async def test_map_citation_merges_top_level_metadata_preserving_existing(monkeypatch, patch_citation_deps):
    monkeypatch.setattr(mod, "extract_cff_references", lambda _cff: ([], None))

    gh_citation_cff = {
        "cff-version": "1.2.0",
        "title": "Existing GH Title",  # preserved (non-empty)
        "repository": "",  # filled from BT (empty)
        "license": None,  # filled from BT (None)
        "keywords": [],  # filled from BT (empty list)
        "abstract": "Existing abstract",  # preserved (non-empty)
        "some-custom-field": "keep me",  # preserved
        # these are ignored here and recomputed later:
        "references": [{"doi": "10.x/y"}],
        "preferred-citation": {"doi": "10.x/z"},
    }

    bt_params = {
        "name": "ToolName",
        "biotoolsID": "toolid",
        "homepage": "https://example.org/repo",
        "license": "MIT",
        "topic": ["t1", "t2"],
        "description": "BT description",
        "publication": None,
    }

    out = await mod.map_citation(gh_citation_cff=gh_citation_cff, bt_params=bt_params)
    cff = _load_yaml(out)

    assert cff["title"] == "Existing GH Title"  # preserved
    assert cff["repository"] == "https://example.org/repo"  # filled
    assert cff["license"] == "MIT"  # filled
    assert cff["keywords"] == ["t1", "t2"]  # filled
    assert cff["abstract"] == "Existing abstract"  # preserved
    assert cff["some-custom-field"] == "keep me"  # preserved

    # No publications => minimal citation behavior
    assert "references" not in cff
    assert "preferred-citation" not in cff
    assert "message" in cff


async def test_map_citation_merges_references_with_gh_first_order(monkeypatch, patch_citation_deps):
    """
    Public behavior: reference merge order is GH refs first, then bio.tools refs.
    This test does NOT assert deduplication on "same DOI" because normalization
    differences can prevent overlap and that is valid under current utilities.
    """
    gh_refs = [{"doi": "10.5555/primary-2023", "title": "GH version", "year": 2023}]
    monkeypatch.setattr(mod, "extract_cff_references", lambda _cff: (gh_refs, None))

    bt_params = {
        "name": "ToolName",
        "biotoolsID": "toolid",
        "homepage": None,
        "license": None,
        "topic": None,
        "description": None,
        "publication": [
            BT_PUB(doi="10.5555/primary-2023", type_=[mod.TypeEnum2.Primary]),
        ],
    }

    out = await mod.map_citation(gh_citation_cff={"x": "y"}, bt_params=bt_params)
    cff = _load_yaml(out)

    refs = _refs(cff)
    assert len(refs) >= 1

    # GH reference should appear first
    assert refs[0]["title"] == "GH version"
    assert refs[0]["doi"] == "10.5555/primary-2023"

    # BT-resolved reference should be present somewhere (dedupe may or may not drop it)
    dois = [r.get("doi") for r in refs]
    assert "10.5555/primary-2023" in dois
