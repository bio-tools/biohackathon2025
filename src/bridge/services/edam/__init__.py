"""
EDAM integrations: async metadata ingestor from EMBL-EBI OLS4.
"""

from .edam_ingestor import EDAMTermByNameIngestor

__all__ = [
    "EDAMTermByNameIngestor",
]
