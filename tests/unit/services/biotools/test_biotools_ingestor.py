"""
Unit tests for bridge.services.biotools.BiotoolsIngestor.
"""

import pytest
from pytest_httpx import HTTPXMock

from bridge.config import settings
from bridge.services.biotools import BiotoolsIngestor


@pytest.mark.asyncio
async def test_biotools_ingestor_fetch(httpx_mock: HTTPXMock):
    """
    Test that BiotoolsIngestor can fetch data from the BioTools API.

    Raises
    ------
    AssertionError
        If the fetched data does not match the expected values.
    """
    biotools_id = "mytool"
    url = f"{settings.biotools_api_base}/tool/{biotools_id}?format=json"
    httpx_mock.add_response(url=url, json={"name": "My Tool", "biotoolsID": biotools_id})

    ing = BiotoolsIngestor(biotools_id)
    data = await ing.fetch()
    assert data["name"] == "My Tool"
