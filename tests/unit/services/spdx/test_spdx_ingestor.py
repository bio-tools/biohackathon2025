"""
Unit tests for SPDXLicenseIngestor.
"""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from bridge.config import settings
from bridge.services.spdx import SPDXLicenseIngestor
from bridge.services.spdx.spdx_ingestor import SPDXLicenseNotFoundError


def _license_url(spdx_id: str) -> str:
    base = settings.spdx_license_api_base
    return f"{base}/{spdx_id}.json"


@pytest.mark.asyncio
async def test_spdx_license_ingestor_requires_nonempty_id():
    with pytest.raises(ValueError, match="SPDX identifier must be a non-empty string"):
        SPDXLicenseIngestor("")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_fetch_returns_license_json_on_success(httpx_mock: HTTPXMock):
    spdx_id = "MIT"
    httpx_mock.add_response(
        method="GET",
        url=_license_url(spdx_id),
        status_code=200,
        json={
            "licenseId": "MIT",
            "name": "MIT License",
            "licenseText": "Permission is hereby granted...",
        },
    )

    ing = SPDXLicenseIngestor(spdx_id)
    data = await ing.fetch()

    assert data["licenseId"] == "MIT"
    assert data["name"] == "MIT License"
    assert "licenseText" in data


@pytest.mark.asyncio
async def test_fetch_raises_not_found_when_license_id_missing(httpx_mock: HTTPXMock):
    spdx_id = "MIT"
    httpx_mock.add_response(
        method="GET",
        url=_license_url(spdx_id),
        status_code=200,
        json={
            # missing "licenseId"
            "name": "MIT License",
            "licenseText": "Permission is hereby granted...",
        },
    )

    ing = SPDXLicenseIngestor(spdx_id)
    with pytest.raises(SPDXLicenseNotFoundError) as exc:
        await ing.fetch()

    msg = str(exc.value)
    assert "missing 'licenseId' field" in msg
    assert "MIT" in msg


@pytest.mark.asyncio
async def test_fetch_propagates_http_status_error(httpx_mock: HTTPXMock):
    spdx_id = "MIT"
    httpx_mock.add_response(
        method="GET",
        url=_license_url(spdx_id),
        status_code=404,
        json={"message": "Not Found"},
    )

    ing = SPDXLicenseIngestor(spdx_id)
    with pytest.raises(httpx.HTTPStatusError):
        await ing.fetch()


@pytest.mark.asyncio
async def test_fetch_propagates_request_error(monkeypatch):
    """
    Simulate a network error (httpx.RequestError) raised by httpx.AsyncClient.get.
    """

    class FakeClient:
        def __init__(self, *args, **kwargs): ...

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            raise httpx.RequestError("boom", request=httpx.Request("GET", url))

    monkeypatch.setattr("bridge.services.spdx.spdx_ingestor.httpx.AsyncClient", FakeClient)

    ing = SPDXLicenseIngestor("MIT")
    with pytest.raises(httpx.RequestError):
        await ing.fetch()
