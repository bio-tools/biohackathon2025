"""
Mapping functions for language field.
"""

from bridge.core.biotools import LanguageEnum
from bridge.core.github_languages import Language


def map_language(gh_languages: Language | None, bt_languages: list[LanguageEnum] | None) -> None:
    """
    Map languages from GitHub to bio.tools.
    """
    pass
