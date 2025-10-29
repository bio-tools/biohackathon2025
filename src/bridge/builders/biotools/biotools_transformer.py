"""
Transformer converting raw bio.tools API JSON into a BiotoolsToolModel.
"""

import logging

from bridge.builders.protocols import Transformer
from bridge.core import BiotoolsToolModel
from bridge.services import BiotoolsIngestor

logger = logging.getLogger(__name__)


class BiotoolsToolTransformer(Transformer):
    """
    Transform raw data from BiotoolsIngestor into a BiotoolsToolModel.

    Parameters
    ----------
    ingestor : BiotoolsIngestor
        An instance of BiotoolsIngestor to fetch raw tool metadata.

    Attributes
    ----------
    ingestor : BiotoolsIngestor
        The ingestor instance used to fetch raw tool metadata.
    """

    def __init__(self, ingestor: BiotoolsIngestor):
        self.ingestor = ingestor

    async def transform(self) -> BiotoolsToolModel:
        """
        Transform raw data into a BiotoolsToolModel.

        Returns
        -------
        BiotoolsToolModel
            The transformed tool model.
        """
        logger.info(f"Transforming data for bio.tools ID {self.ingestor.biotools_id}")
        raw_data = await self.ingestor.fetch()
        logger.debug(f"Raw data keys: {list(raw_data.keys())}")
        result = BiotoolsToolModel(**raw_data)
        logger.info(f"Transformed data for bio.tools ID {self.ingestor.biotools_id} successfully")
        return result
