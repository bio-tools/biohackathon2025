"""
Individual mapping functions for GitHub to bio.tools.
"""

from .biotools_id import map_biotools_id
from .description import map_description
from .documentation import map_documentation
from .functions import map_functions
from .homepage import map_homepage
from .language import map_language
from .license import map_license
from .maturity import map_maturity
from .name import map_name
from .publication import map_publication
from .version import map_version

__all__ = [
    "map_documentation",
    "map_homepage",
    "map_description",
    "map_language",
    "map_license",
    "map_maturity",
    "map_version",
    "map_publication",
    "map_name",
    "map_biotools_id",
    "map_functions",
]
