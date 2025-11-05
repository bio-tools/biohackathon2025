"""
Transformer converting raw Europe PMC API JSON into a Publication model.
"""

import re

from bridge.builders.protocols import Transformer
from bridge.core import Publication
from bridge.core.publication import Author
from bridge.services import EuropePMCIngestor


class EuropePMCTransformer(Transformer):
    """
    Transform raw data from EuropePMCIngestor into a Publication model.

    Parameters
    ----------
    ingestor : EuropePMCIngestor
        An instance of EuropePMCIngestor to fetch raw publication data.


    Attributes
    ----------
    ingestor : EuropePMCIngestor
        The ingestor instance used to fetch raw publication data.
    """

    def __init__(self, ingestor: EuropePMCIngestor):
        self.ingestor = ingestor

    async def transform(self) -> Publication:
        """
        Transform raw Europe PMC data into a Publication model.

        Parameters
        ----------
        data : dict
            The raw data from Europe PMC.

        Returns
        -------
        Publication
            The transformed Publication model.
        """
        raw_data = await self.ingestor.fetch()

        authors = self._get_authors(raw_data)
        page_start, page_end = self._get_page_range(raw_data)

        return Publication(
            doi=raw_data.get("doi"),
            title=raw_data.get("title"),
            authors=authors,
            year=int(raw_data.get("pubYear")),
            journal=raw_data.get("journalTitle"),
            volume=raw_data.get("journalVolume"),
            issue=raw_data.get("issue"),
            page_start=page_start,
            page_end=page_end,
        )

    def _get_authors(self, raw_data: dict) -> list[Author]:
        """
        Extract authors from raw Europe PMC data.

        Parameters
        ----------
        raw_data : dict
            The raw data from Europe PMC.

        Returns
        -------
        list[Author]
            A list of Author models.
        """
        out = []
        for a in raw_data.get("authorList", {}).get("author", []):
            if a.get("lastName") or a.get("firstName"):
                out.append(Author(first_name=a.get("firstName", None), last_name=a.get("lastName", None)))
            elif a.get("fullName"):
                out.append(Author(name=a["fullName"]))
        return out

    def _get_page_range(self, raw_data: dict) -> tuple[str | None, str | None]:
        """
        Extract the page range from raw Europe PMC data.

        Parameters
        ----------
        raw_data : dict
            The raw data from Europe PMC.

        Returns
        -------
        tuple[str or None, str or None]
            A tuple containing the start and end pages. If the page information
            cannot be parsed, both values are None.
        """
        pg = raw_data.get("pageInfo") or ""
        m = re.match(r"^\s*([\w\-]+)\s*[-–]\s*([\w\-]+)\s*$", pg)
        return (m.group(1), m.group(2)) if m else (None, None)
