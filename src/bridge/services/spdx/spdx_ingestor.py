"""
Async client for the SPDX license list.
Fetches a license by SPDX identifier and returns the full JSON payload,
including the canonical license text.
"""

import logging
from typing import Any

import httpx

from bridge.config import settings
from bridge.services.protocols import Ingestor

logger = logging.getLogger(__name__)


class SPDXLicenseNotFoundError(Exception):
    """Raised when no SPDX license matches the given SPDX identifier."""


class SPDXLicenseIngestor(Ingestor):
    """
    Ingest license metadata from the SPDX license list by SPDX identifier.

    This client fetches the JSON representation of a single license from
    the SPDX license list, which includes the canonical license text
    (``licenseText``), name, and other metadata.

    Parameters
    ----------
    spdx_id : str
        SPDX license identifier (e.g. ``"MIT"``, ``"GPL-3.0-only"``).
    """

    def __init__(self, spdx_id: str):
        if not spdx_id:
            raise ValueError("SPDX identifier must be a non-empty string.")
        self.spdx_id = spdx_id

    async def _get(self) -> dict[str, Any]:
        """
        Perform async GET request to the SPDX license JSON endpoint.

        Returns
        -------
        dict
            JSON response for the given SPDX license.

        Raises
        ------
        httpx.RequestError
            For network-related issues.
        httpx.HTTPStatusError
            For non-2xx HTTP responses.
        """
        # SPDX per-license JSON: {base}/{ID}.json, e.g. https://spdx.org/licenses/MIT.json
        base = settings.spdx_license_api_base
        url = f"{base}/{self.spdx_id}.json"
        try:
            logger.debug(f"Fetching SPDX license JSON: {url}")
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                logger.debug(f"Fetched SPDX license data for ID {self.spdx_id} successfully")
                return data
        except httpx.RequestError as e:
            logger.error(f"Network error while fetching {url}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error from SPDX license endpoint: {e.response.status_code} for {url}")
            raise

    async def fetch(self) -> dict[str, Any]:
        """
        Fetch the SPDX license record for the specified SPDX identifier.

        Returns
        -------
        dict
            JSON metadata for the SPDX license, including at least
            ``licenseId``, ``name``, and ``licenseText`` fields.

        Raises
        ------
        SPDXLicenseNotFoundError
            If the SPDX service does not return a valid license record.
        httpx.RequestError, httpx.HTTPStatusError
            For network/HTTP issues.
        """
        data = await self._get()

        # SPDX license JSON should have a "licenseId" matching the request.
        license_id = data.get("licenseId")
        if not license_id:
            msg = f"SPDX license JSON for ID {self.spdx_id!r} missing 'licenseId' field"
            logger.warning(msg)
            raise SPDXLicenseNotFoundError(msg)

        logger.info(f"Ingested SPDX license data for {self.spdx_id} successfully")
        return data
