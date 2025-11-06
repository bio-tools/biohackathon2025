"""
Individual mapping functions for GitHub to bio.tools.
"""

from .documentation import map_documentation
from .homepage import map_homepage
from .description import map_description
from .license import map_license

__all__ = [
    "map_documentation",
    "map_homepage",
    "map_description",
    "map_license",
]
