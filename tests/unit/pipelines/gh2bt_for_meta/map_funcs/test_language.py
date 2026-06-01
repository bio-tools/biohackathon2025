"""
Unit tests for mapping GitHub languages to bio.tools languages (map_language).
"""

from __future__ import annotations

import pytest

from bridge.core.biotools import LanguageEnum
from bridge.core.github_languages import Language
from bridge.pipelines.gh2bt_for_meta.map_funcs.language import map_language


def _gh_langs(d: dict[str, int] | None) -> Language | None:
    """
    Create a Language model with .root mapping.
    The project uses a Pydantic RootModel-like type for GitHub languages.
    """
    if d is None:
        return None
    return Language(root=d)


@pytest.mark.parametrize(
    "gh, bt, expected",
    [
        # --- GitHub silent: preserve bio.tools (even if None) ---
        (None, None, None),
        (None, [LanguageEnum.Python], [LanguageEnum.Python]),
        (_gh_langs({}), [LanguageEnum.Python], [LanguageEnum.Python]),
        # --- bio.tools missing: GitHub drives result ---
        (_gh_langs({"Python": 10}), None, [LanguageEnum.Python]),
        (_gh_langs({"python": 10}), None, [LanguageEnum.Python]),  # case-insensitive
        # --- Exact match (set-based): preserve existing bt object/list ---
        (_gh_langs({"Python": 10}), [LanguageEnum.Python], [LanguageEnum.Python]),
        (
            _gh_langs({"Python": 10, "JavaScript": 5}),
            [LanguageEnum.JavaScript, LanguageEnum.Python],
            [LanguageEnum.JavaScript, LanguageEnum.Python],
        ),
        # --- Conflict: GitHub adds to bio.tools ---
        (_gh_langs({"Python": 10}), [LanguageEnum.R], [LanguageEnum.Python, LanguageEnum.R]),
        (
            _gh_langs({"Python": 10, "JavaScript": 5}),
            [LanguageEnum.Python],
            # GitHub includes JS too -> overwrite with both
            # Order may vary due to set iteration; we assert as a set below.
            [LanguageEnum.Python, LanguageEnum.JavaScript],
        ),
        # --- Unknown GitHub languages are skipped; result can become None ---
        (_gh_langs({"TotallyNotALang": 1}), None, None),
        (
            _gh_langs({"TotallyNotALang": 1}),
            [LanguageEnum.Python],
            [LanguageEnum.Python],
        ),  # GitHub mapped to None => keep bt?
    ],
)
async def test_map_language(gh, bt, expected):
    """
    Test map_language reconciliation behavior.

    Notes:
    - When GitHub has no languages (None or empty root), we preserve bt.
    - When GitHub provides languages, we map recognized ones to LanguageEnum.
    - Unknown languages are skipped; if all are unknown, build_bt_from_gh returns None.
      The generic reconciler then preserves bt_value.
    """
    out = await map_language(gh_languages=gh, bt_languages=bt)

    # For cases where expected list order isn't stable, compare as sets.
    if out is not None and expected is not None:
        # When both are lists, compare by set to avoid ordering sensitivity.
        assert set(out) == set(expected)
    else:
        assert out == expected
