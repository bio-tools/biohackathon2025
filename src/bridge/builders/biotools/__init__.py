"""
Composition utilities for bio.tools: fetch raw tool JSON and transform it into a validated BiotoolsToolModel.
"""

from .biotools_composer import compose_biotools_metadata

__all__ = [
    "compose_biotools_metadata",
]
