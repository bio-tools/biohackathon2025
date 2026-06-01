"""
Transformer converting raw EDAM term data into an EDAMTerm model.
"""

import logging

from bridge.builders.protocols import Transformer
from bridge.core import EDAMTerm
from bridge.services import EDAMTermByNameIngestor

logger = logging.getLogger(__name__)


class EDAMTransformer(Transformer):
    """
    Transform raw EDAM term data into an EDAMTerm model.

    Parameters
    ----------
    ingestor : EDAMTermByNameIngestor
        An instance of EDAMTermByNameIngestor to fetch raw EDAM term data.

    Attributes
    ----------
    ingestor : EDAMTermByNameIngestor
        The ingestor instance used to fetch raw EDAM term data.
    """

    def __init__(self, ingestor: EDAMTermByNameIngestor):
        self.ingestor = ingestor

    async def transform(self) -> EDAMTerm:
        """
        Transform raw EDAM term data into an EDAMTerm model.

        Returns
        -------
        EDAMTerm
            The transformed EDAMTerm model.
        """
        logger.info(f"Transforming data for EDAM term name '{self.ingestor.name}'")
        raw_data = await self.ingestor.fetch()
        logger.debug(f"Raw data keys: {list(raw_data.keys())}")
        result = EDAMTerm(**raw_data)
        logger.info(f"Transformed data for EDAM term name '{self.ingestor.name}' successfully")
        return result
