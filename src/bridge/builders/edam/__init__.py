"""
Composition utilities for EMBL-EBI OLS4: fetch raw term JSON and transform it into a validated EDAM term model.
"""

from .edam_composer import compose_edam_term_metadata

__all__ = [
    "compose_edam_term_metadata",
]
