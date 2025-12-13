"""
Unit tests for EuropePMCIngestor.

These tests register one mocked response per expected HTTP request,
because some pytest-httpx versions treat callbacks as single-use.
"""

import urllib.parse

import httpx
import pytest
from pytest_httpx import HTTPXMock

from bridge.config import settings
from bridge.services.europe_pmc import EuropePMCIngestor
from bridge.services.europe_pmc.europe_pmc_ingestor import EuropePMCNotFoundError


def _search_base_url() -> str:
    return f"{settings.europepmc_api_base}/search"


def _search_url_for_query(query: str) -> str:
    """
    Build the exact URL that httpx will request given EuropePMCIngestor._get() defaults.
    """
    params = {
        "format": "json",
        "resultType": "core",
        "pageSize": 1,
        "query": query,
    }
    return f"{_search_base_url()}?{urllib.parse.urlencode(params)}"


def test_first_result_helper():
    assert EuropePMCIngestor._first_result({"resultList": {"result": [{"id": 1}]}}) == {"id": 1}
    assert EuropePMCIngestor._first_result({"resultList": {"result": []}}) is None
    assert EuropePMCIngestor._first_result({}) is None


@pytest.mark.asyncio
async def test_fetch_falls_back_to_next_query(httpx_mock: HTTPXMock):
    """
    If the first query returns no results, fetch() tries the next query.
    """
    ing = EuropePMCIngestor(pmid="111", pmcid="PMC222")

    q1 = "EXT_ID:111 AND SRC:MED"
    q2 = "EXT_ID:PMC222 AND SRC:PMC"

    httpx_mock.add_response(
        method="GET",
        url=_search_url_for_query(q1),
        json={"resultList": {"result": []}},
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=_search_url_for_query(q2),
        json={"resultList": {"result": [{"pmcid": "PMC222"}]}},
        status_code=200,
    )

    rec = await ing.fetch()
    assert rec["pmcid"] == "PMC222"


@pytest.mark.asyncio
async def test_fetch_tries_both_doi_query_variants(httpx_mock: HTTPXMock):
    """
    For DOI, the ingestor tries DOI:<doi> and EXT_ID:"<doi>".
    """
    doi = "10.1021/acs.jproteome.2c00457"
    ing = EuropePMCIngestor(doi=doi)

    q1 = f"DOI:{doi}"
    q2 = f'EXT_ID:"{doi}"'

    httpx_mock.add_response(
        method="GET",
        url=_search_url_for_query(q1),
        json={"resultList": {"result": []}},
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=_search_url_for_query(q2),
        json={"resultList": {"result": [{"doi": doi}]}},
        status_code=200,
    )

    rec = await ing.fetch()
    assert rec["doi"] == doi


@pytest.mark.asyncio
async def test_fetch_raises_not_found_when_all_queries_empty(httpx_mock: HTTPXMock):
    """
    If all queries return no results, fetch() raises EuropePMCNotFoundError.
    """
    ing = EuropePMCIngestor(pmid="999", doi="10.9999/nope")

    # The ingestor will try: EXT_ID:<pmid> AND SRC:MED, then DOI:<doi>, then EXT_ID:"<doi>"
    queries = [
        "EXT_ID:999 AND SRC:MED",
        "DOI:10.9999/nope",
        'EXT_ID:"10.9999/nope"',
    ]

    for q in queries:
        httpx_mock.add_response(
            method="GET",
            url=_search_url_for_query(q),
            json={"resultList": {"result": []}},
            status_code=200,
        )

    with pytest.raises(EuropePMCNotFoundError) as exc:
        await ing.fetch()

    msg = str(exc.value)
    assert "No Europe PMC record found" in msg
    assert "pmid='999'" in msg
    assert "doi='10.9999/nope'" in msg


@pytest.mark.asyncio
async def test_fetch_propagates_http_status_error(httpx_mock: HTTPXMock):
    """
    HTTP errors from Europe PMC should propagate as httpx.HTTPStatusError.
    """
    ing = EuropePMCIngestor(pmid="123")

    q = "EXT_ID:123 AND SRC:MED"

    httpx_mock.add_response(
        method="GET",
        url=_search_url_for_query(q),
        json={"message": "server error"},
        status_code=500,
    )

    with pytest.raises(httpx.HTTPStatusError):
        await ing.fetch()
