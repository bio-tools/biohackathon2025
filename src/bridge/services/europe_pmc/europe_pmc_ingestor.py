"""
Async client for the Europe PMC API.
Fetches a publication by PMID/PMCID/DOI and returns the first matching record.
Raises EuropePMCNotFoundError if no record is found.
"""

import logging
from typing import Any

import httpx

from bridge.config import settings
from bridge.services.protocols import Ingestor

from .europe_pmc_auth import get_europe_pmc_headers

logger = logging.getLogger(__name__)


class EuropePMCNotFoundError(Exception):
    """Raised when no Europe PMC record matches the given identifiers."""


class EuropePMCIngestor(Ingestor):
    """
    Ingest a publication record from Europe PMC using one or more identifiers.

    Parameters
    ----------
    pmid : str, optional
        PubMed identifier (e.g., "36173614").
    pmcid : str, optional
        PubMed Central identifier (e.g., "PMC9903320").
    doi : str, optional
        Digital Object Identifier (e.g., "10.1021/acs.jproteome.2c00457").
    """

    def __init__(self, pmid: str | None = None, pmcid: str | None = None, doi: str | None = None):
        if not any([pmid, pmcid, doi]):
            raise ValueError("Provide at least one of: pmid, pmcid, doi.")
        self.pmid = pmid
        self.pmcid = pmcid
        self.doi = doi
        self._timeout = getattr(settings, "http_timeout_seconds", 10)

    def _build_queries(self) -> list[str]:
        queries: list[str] = []
        if self.pmid:
            queries.append(f"EXT_ID:{self.pmid} AND SRC:MED")
        if self.pmcid:
            queries.append(f"EXT_ID:{self.pmcid} AND SRC:PMC")
        if self.doi:
            # Try both DOI: and EXT_ID:"<doi>" variants
            queries.append(f"DOI:{self.doi}")
            queries.append(f'EXT_ID:"{self.doi}"')
        return queries

    async def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        default_params = {"format": "json", "resultType": "core", "pageSize": 1}
        all_params = {**default_params, **params}
        base = f"{settings.europepmc_api_base}/search"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(base, params=all_params, headers=get_europe_pmc_headers())
                resp.raise_for_status()
                return resp.json()
        except httpx.RequestError as e:
            logger.error(f"Network error while querying Europe PMC: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} from Europe PMC for params={all_params}")
            raise

    @staticmethod
    def _first_result(payload: dict[str, Any]) -> dict[str, Any] | None:
        return payload.get("resultList", {}).get("result", [None])[0]

    async def fetch(self) -> dict[str, Any]:
        """
        Fetch the Europe PMC record matching the provided identifiers.

        Returns
        -------
        dict
            The first matching Europe PMC record.

        Raises
        ------
        EuropePMCNotFoundError
            If no record matches the provided identifiers.
        httpx.RequestError, httpx.HTTPStatusError
            For network/HTTP issues.
        """
        queries = self._build_queries()
        logger.debug(f"EuropePMCIngestor queries: {queries}")

        for q in queries:
            logger.debug(f"Querying Europe PMC with: {q}")
            data = await self._get({"query": q})
            rec = self._first_result(data)
            if rec:
                logger.info("Found Europe PMC record")
                return rec

        msg = f"No Europe PMC record found for identifiers pmid={self.pmid!r}, pmcid={self.pmcid!r}, doi={self.doi!r}"
        logger.info(msg)
        raise EuropePMCNotFoundError(msg)
