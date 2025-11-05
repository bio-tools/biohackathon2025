"""
Composition utilities for Europe PMC: fetch raw publication JSON and transform it into a validated Publication model.
"""

from .europe_pmc_composer import compose_europe_pmc_metadata

__all__ = ["compose_europe_pmc_metadata"]
