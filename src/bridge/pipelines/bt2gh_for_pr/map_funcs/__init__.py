"""
Individual mapping functions for bio.tools to GitHub.
"""

from .citation import map_citation
from .description import map_description
from .function import map_function2topics
from .homepage import map_homepage

__all__ = [
    "map_citation",
    "map_description",
    "map_function2topics",
    "map_homepage",
]
