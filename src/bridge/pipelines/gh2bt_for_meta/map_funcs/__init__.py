"""
Individual mapping functions for GitHub to bio.tools.
"""

from .description import map_description
from .documentation import map_documentation
from .homepage import map_homepage
from .license import map_license
from .maturity import map_maturity
from .version import map_version

__all__ = [
    "map_documentation",
    "map_homepage",
    "map_description",
    "map_license",
    "map_maturity",
    "map_version",
]
