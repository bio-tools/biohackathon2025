"""
High-level coroutine that chains EuropePMCIngestor and EuropePMCTransformer
to produce a Publication model from a Europe PMC ID.
"""

import logging

from bridge.core import SPDXLicense
from bridge.services import SPDXLicenseIngestor

from .spdx_transormer import SPDXLicenseTransformer

logger = logging.getLogger(__name__)


async def compose_spdx_license_metadata(spdx_id: str) -> SPDXLicense:
    """
    Fetch and transform SPDX license entry into a SPDXLicense model.

    Parameters
    ----------
    spdx_id : str
        SPDX license identifier (e.g. "MIT", "GPL-3.0-only").

    Returns
    -------
    SPDXLicense
        A SPDXLicense model representing the SPDX license metadata.

    Raises
    ------
    Exception
        If there is an error during ingestion or transformation.
    """
    logger.info(f"Composing SPDX license metadata model for ID {spdx_id}")
    try:
        spdx_license_ingestor = SPDXLicenseIngestor(spdx_id=spdx_id)
        spdx_license_transformer = SPDXLicenseTransformer(spdx_license_ingestor)
        spdx_license_metadata = await spdx_license_transformer.transform()
        logger.info(f"Composed SPDX license metadata model for ID {spdx_id} successfully")
        return spdx_license_metadata
    except Exception as e:
        logger.exception(f"Error composing SPDX license metadata model for ID {spdx_id}: {e}")
        raise
