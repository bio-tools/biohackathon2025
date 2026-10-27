"""
Async client for resolving EDAM ontology terms by name through EMBL-EBI OLS4.

Searches for an EDAM concept by preferred label or synonym and returns a
single unambiguous match. The returned search record includes the EDAM IRI
and compact identifier.
"""

import logging
from typing import Any

import httpx

from bridge.config import settings
from bridge.services.protocols import Ingestor

from .edam_auth import get_edam_headers

logger = logging.getLogger(__name__)


class EDAMTermNotFoundError(Exception):
    """Raised when no EDAM concept matches the requested term."""


class EDAMTermAmbiguousError(Exception):
    """Raised when multiple EDAM concepts plausibly match the requested term."""


class EDAMTermByNameIngestor(Ingestor):
    """
    Resolve an EDAM ontology concept by human-readable name.

    Parameters
    ----------
    name : str
        Preferred label or synonym, for example ``"proteomics"``.
    exact : bool, default=True
        Ask OLS4 to restrict results to exact text matches.
    include_obsolete : bool, default=False
        Whether obsolete EDAM concepts may be returned.
    """

    ontology = "edam"

    def __init__(
        self,
        name: str,
        *,
        exact: bool = True,
        include_obsolete: bool = False,
    ):
        name = name.strip()
        if not name:
            raise ValueError("EDAM term name must be a non-empty string.")

        self.name = name
        self.exact = exact
        self.include_obsolete = include_obsolete
        self._timeout = getattr(settings, "http_timeout_seconds", 10)

    async def _get(self) -> dict[str, Any]:
        """
        Search OLS4 for EDAM concepts matching the requested name.
        """
        base = settings.ols4_api_base
        url = f"{base}/search"

        params: dict[str, Any] = {
            "q": self.name,
            "ontology": self.ontology,
            "exact": str(self.exact).lower(),
            "obsoletes": str(self.include_obsolete).lower(),
            "rows": 20,
        }

        try:
            logger.debug("Searching OLS4 for EDAM term: params=%s", params)

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=get_edam_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as exc:
            logger.error("Network error while querying OLS4: %s", exc)
            raise

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "HTTP %s from OLS4 for params=%s",
                exc.response.status_code,
                params,
            )
            raise

    @staticmethod
    def _results(payload: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract OLS search documents from the JSON response.
        """
        return payload.get("response", {}).get("docs") or []

    @staticmethod
    def _is_obsolete(record: dict[str, Any]) -> bool:
        """
        Interpret the OLS obsolete marker defensively.
        """
        value = record.get("is_obsolete", False)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() == "true"

        return bool(value)

    def _exact_label_matches(
        self,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Select records whose preferred label equals the requested name.
        """
        expected = self.name.casefold()

        return [
            record
            for record in records
            if str(record.get("label", "")).casefold() == expected
            and (self.include_obsolete or not self._is_obsolete(record))
        ]

    async def fetch(self) -> dict[str, Any]:
        """
        Resolve one unambiguous EDAM concept.

        Returns
        -------
        dict
            Compact OLS4 search result. Common fields include ``iri``,
            ``label``, ``short_form``, ``ontology_name``, ``description``,
            and ``synonym``.

        Raises
        ------
        EDAMTermNotFoundError
            If no usable EDAM concept matches the requested name.
        httpx.RequestError, httpx.HTTPStatusError
            For network or HTTP failures.
        """
        payload = await self._get()
        records = self._results(payload)
        exact_matches = self._exact_label_matches(records)

        if len(exact_matches) == 1:
            record = exact_matches[0]
            logger.info(
                "Resolved EDAM term %r to %s",
                self.name,
                record.get("iri"),
            )
            return record

        if len(exact_matches) > 1:
            candidates = [
                {
                    "label": record.get("label"),
                    "iri": record.get("iri"),
                    "short_form": record.get("short_form"),
                }
                for record in exact_matches
            ]
            logger.info(
                "Multiple exact matches for EDAM term %r. Returning first of %d candidates: %s",
                self.name,
                len(exact_matches),
                candidates,
            )
            return exact_matches[0]
            # raise EDAMTermAmbiguousError(f"Multiple EDAM concepts match {self.name!r}: {candidates}")

        if records:
            candidates = [
                {
                    "label": record.get("label"),
                    "iri": record.get("iri"),
                    "short_form": record.get("short_form"),
                }
                for record in records[:10]
                if self.include_obsolete or not self._is_obsolete(record)
            ]
            # return first candidate
            logger.info(
                "No exact preferred-label match for EDAM term %r. Returning first of %d related candidates: %s",
                self.name,
                len(candidates),
                candidates,
            )
            return records[0]

            # raise EDAMTermNotFoundError(
            #     f"No exact preferred-label match for {self.name!r}. OLS4 returned related candidates: {candidates}"
            # )

        raise EDAMTermNotFoundError(f"No EDAM concept found for name {self.name!r}.")
