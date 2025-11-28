"""
Mapping functions for language field.
"""

from bridge.core.biotools import LanguageEnum
from bridge.core.github_languages import Language
from bridge.logging import get_user_logger

logger = get_user_logger()


def _find_matching_bt_language(str_lang: str) -> LanguageEnum | None:
    """
    Find the matching bio.tools language enum for a given string.
    """
    for lang in LanguageEnum:
        if lang.value.lower() == str_lang.lower():
            return lang
    return None


def _cast_to_biotools_languages(languages: set[str]) -> list[LanguageEnum]:
    """
    Cast a set of string languages to a list of bio.tools LanguageEnum.
    """
    bt_languages = []
    for lang in languages:
        matched_lang = _find_matching_bt_language(lang)
        if matched_lang:
            bt_languages.append(matched_lang)
        else:
            logger.note(f"Unknown language '{lang}' not found in bio.tools LanguageEnum.")
    return bt_languages


def map_language(gh_languages: Language | None, bt_languages: list[LanguageEnum] | None) -> list[LanguageEnum] | None:
    """
    Map languages from GitHub to bio.tools.
    """
    if gh_languages is None:
        logger.note("No GitHub languages found, nothing to map.")
        return None

    gh_languages_dict = gh_languages.root

    gh_languages_set = set(gh_languages_dict.keys()) if gh_languages_dict else set()
    gh_languages_set_lower = {lang.lower() for lang in gh_languages_set} if gh_languages_set else set()

    bt_languages_set = {lang.value for lang in bt_languages} if bt_languages else set()
    bt_languages_set_lower = {lang.lower() for lang in bt_languages_set} if bt_languages_set else set()

    if gh_languages_set_lower == bt_languages_set_lower:
        logger.exact("GitHub languages match bio.tools languages.")
        return bt_languages

    if gh_languages is not None and bt_languages is not None:
        if gh_languages_set_lower != bt_languages_set_lower:
            logger.conflict(
                f"Existing GitHub languages '{gh_languages_set}'"
                f" differ from bio.tools languages '{bt_languages_set}'"
            )
        return _cast_to_biotools_languages(gh_languages_set)

    if gh_languages is not None:
        logger.added(f"GitHub languages '{gh_languages_set}'")
        return _cast_to_biotools_languages(gh_languages_set)

    if bt_languages is not None:
        logger.unchanged(f"bio.tools languages '{bt_languages_set}'")
        return bt_languages
