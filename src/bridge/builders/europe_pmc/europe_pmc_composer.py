"""
High-level coroutine that chains EuropePMCIngestor and EuropePMCTransformer
to produce a Publication model from a Europe PMC ID.
"""

import logging

from bridge.core import Publication
from bridge.services import EuropePMCIngestor

from .europe_pmc_transformer import EuropePMCTransformer

logger = logging.getLogger(__name__)


async def compose_europe_pmc_metadata(
    pmid: str | None = None, pmcid: str | None = None, doi: str | None = None
) -> Publication:
    """
    Fetch and transform Europe PMC entry into a Publication model.

    Parameters
    ----------
    pmid : str, optional
        PubMed identifier (e.g., "36173614").
    pmcid : str, optional
        PubMed Central identifier (e.g., "PMC9903320").
    doi : str, optional
        Digital Object Identifier (e.g., "10.1021/acs.jproteome.2c00457").

    Returns
    -------
    Publication
        A Publication model representing the Europe PMC metadata.

    Raises
    ------
    Exception
        If there is an error during ingestion or transformation.
    """
    logger.info(f"Composing Europe PMC metadata model for ID {pmid or pmcid or doi}")
    try:
        europe_pmc_ingestor = EuropePMCIngestor(pmid=pmid, pmcid=pmcid, doi=doi)
        europe_pmc_transformer = EuropePMCTransformer(europe_pmc_ingestor)
        europe_pmc_metadata = await europe_pmc_transformer.transform()
        logger.info(f"Composed Europe PMC metadata model for ID {pmid or pmcid or doi} successfully")
        return europe_pmc_metadata
    except Exception as e:
        logger.exception(f"Error composing Europe PMC metadata model for ID {pmid or pmcid or doi}: {e}")
        raise
