"""
High-level coroutine that chains BiotoolsIngestor and BiotoolsToolTransformer
to produce a BiotoolsToolModel from a bio.tools ID.
"""

import logging

from bridge.core import BiotoolsToolModel
from bridge.services import BiotoolsIngestor
from bridge.utils import require_args

from .biotools_transformer import BiotoolsToolTransformer

logger = logging.getLogger(__name__)


@require_args("identifier")
async def compose_biotools_metadata(**kwargs) -> BiotoolsToolModel:
    """
    Fetch and transform bio.tools entry into a BiotoolsToolModel.

    Parameters
    ----------
    **kwargs
        Expected to contain identifier representing the bio.tools ID.

    Returns
    -------
    BiotoolsToolModel
        A BiotoolsToolModel representing the bio.tools metadata.

    Raises
    ------
    Exception
        If there is an error during ingestion or transformation.
    """
    biotools_id = kwargs.get("identifier")
    logger.info(f"Composing bio.tools metadata model for ID {biotools_id}")
    try:
        biotools_ingestor = BiotoolsIngestor(biotools_id)
        biotools_transformer = BiotoolsToolTransformer(biotools_ingestor)
        biotools_metadata = await biotools_transformer.transform()
        logger.info(f"Composed bio.tools metadata model for ID {biotools_id} successfully")
        return biotools_metadata
    except Exception as e:
        logger.exception(f"Error composing bio.tools metadata model for ID {biotools_id}: {e}")
        raise
