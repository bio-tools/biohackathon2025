"""
Composition utilities for SPDX: fetch raw license JSON and transform it into a validated SPDXLicense model.
"""

from .spdx_composer import compose_spdx_license_metadata

__all__ = ["compose_spdx_license_metadata"]
