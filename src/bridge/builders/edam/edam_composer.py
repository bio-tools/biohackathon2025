"""
High-level coroutine that chains EDAMTermByNameIngestor and EDAMTermTransformer
to produce an EDAMTerm model from an EDAM term name.
"""

import logging

from bridge.core import EDAMTerm
from bridge.services import EDAMTermByNameIngestor

from .edam_transformer import EDAMTransformer

logger = logging.getLogger(__name__)


async def compose_edam_term_metadata(
    term_name: str,
) -> EDAMTerm:
    """
    Fetch and transform EDAM term data into an EDAMTerm model.

    Parameters
    ----------
    term_name : str
        The name of the EDAM term to fetch and transform.

    Returns
    -------
    EDAMTerm
        An EDAMTerm model representing the metadata of the specified EDAM term.

    Raises
    ------
    Exception
        If there is an error during ingestion or transformation.
    """
    logger.info(f"Composing EDAM term metadata model for term name '{term_name}'")
    try:
        edam_ingestor = EDAMTermByNameIngestor(name=term_name)
        edam_transformer = EDAMTransformer(edam_ingestor)
        edam_term_metadata = await edam_transformer.transform()
        logger.info(f"Composed EDAM term metadata model for term name '{term_name}' successfully")
        return edam_term_metadata
    except Exception as e:
        logger.exception(f"Error composing EDAM term metadata model for term name '{term_name}': {e}")
        raise
