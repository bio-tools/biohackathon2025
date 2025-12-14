"""
Unit tests for mapping name from GitHub to bio.tools (map_name).
"""

import pytest

from bridge.pipelines.gh2bt_for_meta.map_funcs.name import map_name


@pytest.mark.parametrize(
    "gh_name, bt_name, expected",
    [
        # --- GitHub silent -> preserve bio.tools (even if None) ---
        (None, None, None),
        (None, "Existing", "Existing"),
        # --- bio.tools missing -> take normalized GitHub ---
        ("Repo", None, "Repo"),
        ("  Hello \nWorld  ", None, "Hello World"),  # normalize_text collapses whitespace
        ("Hello &lt;i&gt;World&lt;/i&gt;", None, "Hello World"),  # entities + tag stripping
        # --- Both present, and they contain each other -> preserve original bt_value ---
        ("Tool", "tool", "tool"),  # case-insensitive containment -> keep bt value
        ("toolkit", "Tool", "Tool"),  # bt contained in gh -> keep bt value
        ("Tool", "  tool  ", "  tool  "),  # preserves bt_value formatting (not bt_norm)
        # --- Conflict -> GitHub wins (normalized GitHub returned) ---
        ("NewName", "OldName", "NewName"),
        ("  New \t Name ", "OldName", "New Name"),  # normalized gh output when overwriting
    ],
)
def test_map_name(gh_name, bt_name, expected):
    assert map_name(gh_name=gh_name, bt_name=bt_name) == expected
