"""
Unit tests for EuropePMCTransformer.

Covers:
- transform() calls ingestor.fetch() and builds a Publication with parsed authors + page range
- _get_authors(): first/last name vs fullName vs empty author entries
- _get_page_range(): hyphen/en-dash parsing + whitespace + non-matching cases
- basic passthrough of key fields and pubYear -> int

No logging assertions.
"""

from __future__ import annotations

from dataclasses import dataclass
import pytest

# Adjust to your real module path
import bridge.builders.europe_pmc.europe_pmc_transformer as mod


# -----------------------------
# Minimal model stubs (avoid depending on generated Pydantic models)
# -----------------------------


@dataclass
class _Author:
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None


@dataclass
class _Publication:
    doi: str | None = None
    title: str | None = None
    authors: list[_Author] | None = None
    year: int | None = None
    journal: str | None = None
    volume: str | None = None
    issue: str | None = None
    page_start: str | None = None
    page_end: str | None = None


class _DummyIngestor:
    def __init__(self, payload: dict):
        self._payload = payload
        self.fetch_calls = 0

    async def fetch(self) -> dict:
        self.fetch_calls += 1
        return self._payload


@pytest.fixture()
def patch_models(monkeypatch):
    """
    Patch transformer module's Publication/Author symbols to small dataclasses.
    """
    monkeypatch.setattr(mod, "Publication", _Publication)
    monkeypatch.setattr(mod, "Author", _Author)


# -----------------------------
# _get_authors
# -----------------------------


@pytest.mark.parametrize(
    "author_list, expected",
    [
        (
            {"author": [{"firstName": "Ada", "lastName": "Lovelace"}]},
            [_Author(first_name="Ada", last_name="Lovelace")],
        ),
        (
            {"author": [{"firstName": "Ada"}]},
            [_Author(first_name="Ada", last_name=None)],
        ),
        (
            {"author": [{"lastName": "Lovelace"}]},
            [_Author(first_name=None, last_name="Lovelace")],
        ),
        (
            {"author": [{"fullName": "Ada Lovelace"}]},
            [_Author(name="Ada Lovelace")],
        ),
        (
            {
                "author": [
                    {"firstName": "Ada", "lastName": "Lovelace"},
                    {"fullName": "Grace Hopper"},
                    {},  # skipped
                    {"firstName": None, "lastName": None, "fullName": None},  # skipped
                ]
            },
            [
                _Author(first_name="Ada", last_name="Lovelace"),
                _Author(name="Grace Hopper"),
            ],
        ),
        (
            {},  # missing author key
            [],
        ),
        (
            {"author": []},
            [],
        ),
    ],
)
def test_get_authors_parses_author_structures(patch_models, author_list, expected):
    t = mod.EuropePMCTransformer(ingestor=_DummyIngestor({}))
    raw = {"authorList": author_list} if author_list else {"authorList": {}}

    out = t._get_authors(raw)
    assert out == expected


# -----------------------------
# _get_page_range
# -----------------------------


@pytest.mark.parametrize(
    "page_info, expected",
    [
        ("123-130", ("123", "130")),
        ("S12-S19", ("S12", "S19")),
        (" e12 - e19 ", ("e12", "e19")),
        ("A1–A9", ("A1", "A9")),  # en dash
        ("A1 – A9", ("A1", "A9")),  # spaced en dash
        ("", (None, None)),
        (None, (None, None)),
        ("nope", (None, None)),
        ("12-", (None, None)),
        ("-12", (None, None)),
        ("12 - 13 - 14", (None, None)),
    ],
)
def test_get_page_range_parsing(patch_models, page_info, expected):
    t = mod.EuropePMCTransformer(ingestor=_DummyIngestor({}))
    raw = {"pageInfo": page_info} if page_info is not None else {}
    assert t._get_page_range(raw) == expected


# -----------------------------
# transform()
# -----------------------------


@pytest.mark.asyncio
async def test_transform_builds_publication_from_raw(patch_models):
    payload = {
        "doi": "10.1000/x",
        "title": "A Paper",
        "pubYear": "2023",
        "journalTitle": "J Test",
        "journalVolume": "12",
        "issue": "3",
        "pageInfo": "101-110",
        "authorList": {
            "author": [
                {"firstName": "Ada", "lastName": "Lovelace"},
                {"fullName": "Grace Hopper"},
                {},  # ignored
            ]
        },
    }
    ing = _DummyIngestor(payload)
    t = mod.EuropePMCTransformer(ingestor=ing)

    pub = await t.transform()

    assert ing.fetch_calls == 1
    assert isinstance(pub, _Publication)

    assert pub.doi == "10.1000/x"
    assert pub.title == "A Paper"
    assert pub.year == 2023
    assert pub.journal == "J Test"
    assert pub.volume == "12"
    assert pub.issue == "3"
    assert pub.page_start == "101"
    assert pub.page_end == "110"

    assert pub.authors == [
        _Author(first_name="Ada", last_name="Lovelace"),
        _Author(name="Grace Hopper"),
    ]


@pytest.mark.asyncio
async def test_transform_raises_if_pubyear_not_int_convertible(patch_models):
    payload = {
        "pubYear": "not-a-year",
        "authorList": {"author": []},
        "pageInfo": "1-2",
    }
    t = mod.EuropePMCTransformer(ingestor=_DummyIngestor(payload))

    with pytest.raises(ValueError):
        await t.transform()
