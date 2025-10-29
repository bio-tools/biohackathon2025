"""
Async client for the bio.tools API.
Fetches a Tool entry by ID and returns raw JSON consumed by the bio.tools builder.
"""

import logging
from typing import Any

import httpx

from bridge.config import settings
from bridge.services.protocols import Ingestor

logger = logging.getLogger(__name__)


class BiotoolsIngestor(Ingestor):
    """
    Ingest metadata from bio.tools ID via the bio.tools REST API.

    Parameters
    ----------
    biotools_id : str
        The bio.tools identifier for the tool to fetch.
    """

    def __init__(self, biotools_id: str):
        self.biotools_id = biotools_id

    async def _get(self, endpoint: str = "", params: dict | None = None) -> dict[str, Any]:
        """
        Perform async GET requests to bio.tools API.

        Parameters
        ----------
        endpoint : str
            Specific API endpoint to query (default is root tool endpoint).
        params : dict, optional
            Query parameters for the request. Defaults to None.

        Returns
        -------
        dict
            JSON response from the bio.tools API.
        """
        base = f"{settings.biotools_api_base}/tool/{self.biotools_id}"
        url = f"{base}{endpoint}?format=json"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Fetched data from bio.tools for ID {self.biotools_id} successfully")
                return data
        except httpx.RequestError as e:
            logger.error(f"Network error while fetching {url}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error from bio.tools: {e.response.status_code} for {url}")
            raise

    async def fetch(self) -> dict[str, Any]:
        """
        Fetch the bio.tools entry for the specified tool ID.

        Returns
        -------
        dict
            JSON metadata for the bio.tools entry.
        """
        logger.debug(f"Fetching bio.tools entry for {self.biotools_id}")
        data = await self._get()
        if not data.get("name"):
            logger.warning(f"bio.tools entry {self.biotools_id} missing 'name' field")
        logger.info(f"Ingested bio.tools entry for {self.biotools_id} successfully")
        return data
