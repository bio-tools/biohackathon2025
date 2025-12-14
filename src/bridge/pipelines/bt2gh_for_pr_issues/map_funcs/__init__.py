"""
Individual mapping functions for bio.tools to GitHub.
"""

from .citation import map_citation
from .description import map_description
from .homepage import map_homepage
from .license import map_license
from .name import map_name
from .readme import map_readme
from .topics import map_topics
from .version import map_version

__all__ = [
    "map_citation",
    "map_description",
    "map_topics",
    "map_homepage",
    "map_readme",
    "map_license",
    "map_version",
    "map_name",
]
