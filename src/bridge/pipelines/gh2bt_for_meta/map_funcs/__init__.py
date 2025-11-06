"""
Individual mapping functions for GitHub to bio.tools.
"""

from .description import map_description
from .homepage import map_homepage
from .license import map_license

__all__ = [
    "map_homepage",
    "map_description",
    "map_license",
]
