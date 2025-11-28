"""
Map language metadata from GitHub to bio.tools.

This module aligns programming language information
between GitHub and bio.tools. It compares the languages
reported by GitHub for a repository with those listed
in the bio.tools metadata, and suggests updates when
discrepancies are found.
"""

from bridge.core.biotools import LanguageEnum
from bridge.core.github_languages import Language
from bridge.logging import get_user_logger
from bridge.pipelines.policies.gh2bt import reconcile_gh_over_bt
from bridge.pipelines.utils import find_matching_enum_member

logger = get_user_logger()


def _to_lang_set_gh(gh_languages: Language | None) -> set[str] | None:
    if gh_languages is None or not gh_languages.root:
        return None
    return {lang.lower() for lang in gh_languages.root.keys()}


def _to_lang_set_bt(bt_languages: list[LanguageEnum] | None) -> set[str] | None:
    if not bt_languages:
        return None
    return {lang.value.lower() for lang in bt_languages}


def _cast_to_biotools_languages(languages: set[str]) -> list[LanguageEnum] | None:
    """
    Convert a set of GitHub language names to a list of bio.tools language enums.

    For each language name in the input set, this function tries to resolve it
    to a `LanguageEnum` using `_find_matching_bt_language`. Languages that
    cannot be resolved are skipped, and a log message is emitted to indicate
    that an unknown language value was encountered.

    Parameters
    ----------
    languages : set[str]
        Set of language names as reported by GitHub.

    Returns
    -------
    list[LanguageEnum] | None
        List of successfully mapped languages as `LanguageEnum` members.
        The order corresponds to the iteration order of the input set.
        Returns ``None`` if no languages could be mapped.
    """
    bt_languages: list[LanguageEnum] = []
    for lang in languages:
        # matched_lang = _find_matching_bt_language(lang)
        matched_lang = find_matching_enum_member(lang, LanguageEnum)
        if matched_lang:
            bt_languages.append(matched_lang)
        else:
            logger.note(f"Unknown language '{lang}' not found in bio.tools LanguageEnum.")
    return bt_languages or None


def map_language(gh_languages: Language | None, bt_languages: list[LanguageEnum] | None) -> list[LanguageEnum] | None:
    """
    Map and reconcile language metadata from GitHub and bio.tools.

    This function compares the set of languages reported by GitHub for a
    repository (`gh_languages`) with the existing language annotations in
    bio.tools (`bt_languages`).

    Policy:
    1. GitHub is considered the authoritative source when present.
       If GitHub provides a non-empty set of languages, that set is mapped to
       `LanguageEnum` values and returned (unknown values are skipped with a log
       message).
    2. bio.tools is preserved only when GitHub provides no language data.
       If GitHub reports no languages (missing or empty), the existing
       bio.tools language annotations are returned unchanged.
    3. Exact matches are treated as no-ops.
       If the GitHub language set (case-insensitive) exactly matches the
       bio.tools language set, the existing bio.tools values are returned
       unchanged and an exact-match log message is emitted.
    4. Conflicts are logged and resolved in favor of GitHub.
       If both GitHub and bio.tools provide languages but they differ, a
       conflict is logged and the GitHub-derived mapping replaces the
       bio.tools values.

    Parameters
    ----------
    gh_languages : Language | None
        GitHub languages object, or ``None`` if no language data is available.
    bt_languages : list[LanguageEnum] | None
        Existing bio.tools language annotations for the tool, or ``None`` if
        no languages are currently recorded in bio.tools.

    Returns
    -------
    list[LanguageEnum] | None
        The reconciled list of bio.tools language enums following the policy.
        May be ``None`` if both inputs are ``None``.
    """
    gh_norm = _to_lang_set_gh(gh_languages)
    bt_norm = _to_lang_set_bt(bt_languages)

    # if GitHub has nothing, keep existing
    if gh_norm is None or len(gh_norm) == 0:
        logger.unchanged("No GitHub languages found, nothing to map.")
        return bt_languages

    # use the generic reconciler on the *set* representation
    return reconcile_gh_over_bt(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        bt_value=bt_languages,
        build_bt_from_gh=_cast_to_biotools_languages,
        log_label="languages",
    )
