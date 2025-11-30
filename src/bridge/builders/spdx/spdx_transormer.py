"""
Transformer converting raw SPDX license data into a SPDXLicenseModel.
"""

import logging

from bridge.builders.protocols import Transformer
from bridge.core.license import SPDXLicenseModel
from bridge.services import SPDXLicenseIngestor

logger = logging.getLogger(__name__)


class SPDXLicenseTransformer(Transformer):
    """
    Transform raw data from SPDXLicenseIngestor into a SPDXLicenseModel.

    Parameters
    ----------
    ingestor : SPDXLicenseIngestor
        An instance of SPDXLicenseIngestor to fetch raw license metadata.

    Attributes
    ----------
    ingestor : SPDXLicenseIngestor
        The ingestor instance used to fetch raw license metadata.
    """

    def __init__(self, ingestor: SPDXLicenseIngestor):
        self.ingestor = ingestor

    async def transform(self) -> SPDXLicenseModel:
        """
        Transform raw data into a SPDXLicenseModel.

        Returns
        -------
        SPDXLicenseModel
            The transformed license model.
        """
        logger.info(f"Transforming data for SPDX license ID {self.ingestor.spdx_id}")
        raw_data = await self.ingestor.fetch()
        logger.debug(f"Raw data keys: {list(raw_data.keys())}")
        result = SPDXLicenseModel(**raw_data)
        logger.info(f"Transformed data for SPDX license ID {self.ingestor.spdx_id} successfully")
        return result
