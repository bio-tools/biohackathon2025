"""
Unit tests for shared publication utilities for pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import pytest

import bridge.pipelines.shared.publications as pubmod
from bridge.pipelines.shared.publications import (
    deduplicate_references,
    extract_cff_references,
    ref_ids,
)


# ------------------------------------------------------------------
# Minimal model stubs (used via monkeypatch to hit "model branch")
# ------------------------------------------------------------------


@dataclass
class _Pub:
    doi: str | None = None
    pmid: str | int | None = None
    pmcid: str | None = None
    title: str | None = None


@dataclass
class _PubItem:
    doi: str | None = None
    pmid: str | int | None = None
    pmcid: str | None = None
    title: str | None = None


# ------------------------------------------------------------------
# ref_ids
# ------------------------------------------------------------------


@pytest.mark.parametrize(
    "ref, expected",
    [
        (
            {"doi": "10.1000/ABC", "pmid": " 123 ", "pmcid": " PMC7 ", "title": " Hello  \nWorld "},
            {"doi:10.1000/ABC", "pmid:123", "pmcid:PMC7", "title:Hello World"},
        ),
        ({"doi": "10.1/x"}, {"doi:10.1/x"}),
        ({"pmid": 42}, {"pmid:42"}),
        ({"pmcid": "PMC999"}, {"pmcid:PMC999"}),
        # Tabs are NOT printable => removed (no space inserted)
        ({"title": "  A\tB  "}, {"title:AB"}),
        ({}, set()),
    ],
)
def test_ref_ids_mapping_extracts_and_normalizes(ref: Mapping[str, Any], expected: set[str]):
    assert ref_ids(ref) == expected


def test_ref_ids_model_objects_extracts_and_normalizes(monkeypatch):
    """
    ref_ids() checks isinstance(ref, (Publication, PublicationItem)).
    To test that branch without depending on the real models, we patch the
    module's Publication / PublicationItem types to our stubs.
    """
    monkeypatch.setattr(pubmod, "Publication", _Pub)
    monkeypatch.setattr(pubmod, "PublicationItem", _PubItem)

    r1 = _Pub(doi="10.2/y", title="T")
    r2 = _PubItem(pmid="7", pmcid=" PMC8 ")

    assert ref_ids(r1) == {"doi:10.2/y", "title:T"}
    assert ref_ids(r2) == {"pmid:7", "pmcid:PMC8"}


def test_ref_ids_raises_for_unsupported_type():
    with pytest.raises(TypeError):
        ref_ids(object())  # type: ignore[arg-type]


# ------------------------------------------------------------------
# deduplicate_references
# ------------------------------------------------------------------


def test_deduplicate_references_keeps_first_and_drops_later_duplicates_by_shared_ids():
    refs = [
        {"doi": "10.1000/ABC", "title": "Paper A"},
        {"doi": "10.1000/ABC", "pmid": "123"},  # duplicate via DOI
        {"pmid": "123"},  # duplicate via PMID after merge
        {"pmcid": "PMC9"},  # unique
    ]

    out = deduplicate_references(refs)

    assert out == [
        {"doi": "10.1000/ABC", "title": "Paper A"},
        {"pmcid": "PMC9"},
    ]


def test_deduplicate_references_dedupes_across_model_and_dict_when_model_types_match(monkeypatch):
    """
    Same trick: patch module Publication/PublicationItem to our stubs so
    deduplicate_references -> ref_ids accepts them.
    """
    monkeypatch.setattr(pubmod, "Publication", _Pub)
    monkeypatch.setattr(pubmod, "PublicationItem", _PubItem)

    refs = [
        _Pub(doi="10.1/x", title="X"),
        {"doi": "10.1/x"},  # duplicate of first via DOI
        _PubItem(title="X"),  # duplicate via title
        {"pmid": "7"},  # unique
    ]

    out = deduplicate_references(refs)
    assert out == [refs[0], refs[3]]


def test_deduplicate_references_treats_no_identifier_items_as_unique(monkeypatch):
    monkeypatch.setattr(pubmod, "Publication", _Pub)
    monkeypatch.setattr(pubmod, "PublicationItem", _PubItem)

    refs = [
        {"foo": "bar"},  # no ids
        {"foo": "bar"},  # no ids again -> kept
        _Pub(),  # no ids -> kept
        _Pub(),  # no ids -> kept
    ]

    out = deduplicate_references(refs)
    assert out == refs


def test_deduplicate_references_title_whitespace_normalization_can_dedupe():
    """
    Title normalization collapses newlines/multiple spaces,
    but does NOT lower-case.
    """
    refs = [
        {"title": "Hello \nworld"},
        {"title": "Hello  world"},  # collapses to "Hello world" like above
        {"title": "HELLO world"},  # different case => NOT deduped
    ]

    out = deduplicate_references(refs)
    assert out == [refs[0], refs[2]]


# ------------------------------------------------------------------
# extract_cff_references
# ------------------------------------------------------------------


def test_extract_cff_references_none_or_empty_returns_empty():
    assert extract_cff_references(None) == ([], None)
    assert extract_cff_references({}) == ([], None)


def test_extract_cff_references_filters_non_mappings_in_references():
    cff = {
        "references": [
            {"doi": "10.1/x"},
            "not a mapping",
            123,
            ["also not"],
            {"pmid": "7"},
        ]
    }
    refs, preferred = extract_cff_references(cff)
    assert preferred is None
    assert refs == [{"doi": "10.1/x"}, {"pmid": "7"}]


def test_extract_cff_references_returns_preferred_and_appends_if_missing():
    cff = {
        "references": [{"doi": "10.1/x"}],
        "preferred-citation": {"pmid": "7", "title": "Preferred"},
    }
    refs, preferred = extract_cff_references(cff)

    assert preferred is not None
    assert preferred["pmid"] == "7"
    assert preferred["title"] == "Preferred"

    # preferred should be appended since it shares no ids with the DOI-only ref
    assert refs == [{"doi": "10.1/x"}, preferred]


def test_extract_cff_references_does_not_append_preferred_if_already_present_by_shared_id():
    cff = {
        "references": [{"pmid": "7", "title": "Already there"}],
        "preferred-citation": {"pmid": "7", "title": "Preferred"},
    }
    refs, preferred = extract_cff_references(cff)

    assert preferred is not None
    assert len(refs) == 1
    assert refs[0]["pmid"] == "7"


def test_extract_cff_references_normalizes_strings_in_cff_structures():
    cff = {
        "references": [{"title": "  Hello &amp; <i>world</i> \n"}],
        "preferred-citation": {"title": "Hello & world"},
    }
    refs, preferred = extract_cff_references(cff)

    assert refs[0]["title"] == "Hello & world"
    assert preferred is not None
    assert preferred["title"] == "Hello & world"
    # preferred matches existing reference by normalized title => not appended
    assert len(refs) == 1
