"""
Unit tests for mapping GitHub CITATION.cff publications to bio.tools (map_publication).

Public-only focus:
- No CITATION.cff => preserve existing bio.tools publications
- CITATION.cff present => convert + merge + deduplicate, with CITATION.cff taking priority
- preferred-citation becomes Primary type
"""

from __future__ import annotations

from typing import Any

import pytest

import bridge.pipelines.gh2bt_for_meta.map_funcs.publication as pubmod
from bridge.core.biotools import PublicationItem, TypeEnum2 as PublicationType
from bridge.pipelines.gh2bt_for_meta.map_funcs.publication import map_publication


def _bt_pub(*, doi: str | None = None, pmid: str | None = None, pmcid: str | None = None) -> PublicationItem:
    # Must satisfy PublicationItem validators (notably DOI regex)
    return PublicationItem(doi=doi, pmid=pmid, pmcid=pmcid, type=None, note=None, version=None)


@pytest.mark.parametrize(
    "gh_citation_cff, bt_factory, expected_factory",
    [
        ({}, lambda: None, lambda: None),
        ({}, lambda: [_bt_pub(doi="10.1000/x")], lambda: [_bt_pub(doi="10.1000/x")]),
        (None, lambda: [_bt_pub(pmid="123")], lambda: [_bt_pub(pmid="123")]),  # type: ignore[arg-type]
    ],
)
def test_map_publication_no_citation_cff_preserves_bt(gh_citation_cff: Any, bt_factory, expected_factory):
    bt_publications = bt_factory()
    expected = expected_factory()
    out = map_publication(gh_citation_cff=gh_citation_cff, bt_publications=bt_publications)
    assert out == expected


def test_map_publication_citation_present_but_no_refs_uses_only_bt(monkeypatch):
    """
    If CITATION.cff exists but extract returns no references and no preferred-citation,
    mapper should return existing bt publications unchanged.
    """
    monkeypatch.setattr(pubmod, "extract_cff_references", lambda _cff: ([], None))

    bt = [_bt_pub(doi="10.1000/x")]
    out = map_publication(gh_citation_cff={"anything": "here"}, bt_publications=bt)

    assert out == bt


def test_map_publication_citation_refs_without_ids_are_ignored_and_falls_back_to_bt(monkeypatch):
    """
    If CITATION.cff references exist but none have DOI/PMID/PMCID,
    conversion yields no gh publications => return bt unchanged.
    """
    refs = [{"title": "No identifiers"}, {"author": "Someone"}]
    monkeypatch.setattr(pubmod, "extract_cff_references", lambda _cff: (refs, None))

    bt = [_bt_pub(pmid="7")]
    out = map_publication(gh_citation_cff={"references": refs}, bt_publications=bt)

    assert out == bt


def test_map_publication_merges_and_calls_dedup_with_cff_first(monkeypatch):
    """
    Verify merge order and preferred-citation handling:
    - preferred-citation is converted and has type Primary
    - gh publications are placed before bt publications before dedup
    """
    preferred = {"doi": "10.1000/preferred"}
    refs = [{"doi": "10.1000/a"}, {"pmid": "123"}]

    monkeypatch.setattr(pubmod, "extract_cff_references", lambda _cff: (refs, preferred))

    captured: dict[str, Any] = {}

    def fake_dedup(items):
        captured["items"] = items
        return items  # keep order so we can inspect it

    monkeypatch.setattr(pubmod, "deduplicate_references", fake_dedup)

    bt = [_bt_pub(doi="10.1000/bt-only")]
    out = map_publication(gh_citation_cff={"dummy": True}, bt_publications=bt)

    assert out is not None
    assert "items" in captured

    passed = captured["items"]
    assert len(passed) == 1 + len(refs) + len(bt)

    # CFF publications should come first
    assert isinstance(passed[0], PublicationItem)
    assert passed[0].doi == "10.1000/preferred"
    assert passed[0].type == [PublicationType.Primary]

    assert passed[-1].doi == "10.1000/bt-only"


def test_map_publication_prefers_cff_when_duplicates_exist(monkeypatch):
    """
    If CITATION.cff includes a publication that duplicates one already in bt,
    the output should keep the CFF version first (priority) after dedup.

    We provide a deterministic minimal dedup stub that keeps first occurrence
    by DOI/PMID/PMCID.
    """
    refs = [{"doi": "10.1000/dup"}, {"pmid": "7"}]
    monkeypatch.setattr(pubmod, "extract_cff_references", lambda _cff: (refs, None))

    def dedup_keep_first(items):
        seen = set()
        out = []
        for it in items:
            doi = getattr(it, "doi", None)
            pmid = getattr(it, "pmid", None)
            pmcid = getattr(it, "pmcid", None)

            key = ("doi", doi) if doi else ("pmid", pmid) if pmid else ("pmcid", pmcid) if pmcid else None
            if key is None:
                out.append(it)
                continue
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        return out

    monkeypatch.setattr(pubmod, "deduplicate_references", dedup_keep_first)

    bt = [_bt_pub(doi="10.1000/dup"), _bt_pub(pmcid="PMC1")]
    out = map_publication(gh_citation_cff={"references": refs}, bt_publications=bt)

    assert out is not None

    # The duplicate DOI should appear once, and it should be first (CFF priority)
    dois = [p.doi for p in out if isinstance(p, PublicationItem)]
    assert dois.count("10.1000/dup") == 1
    assert out[0].doi == "10.1000/dup"
    assert any(getattr(p, "pmcid", None) == "PMC1" for p in out)
