"""
Unit tests for mapping bio.tools metadata onto a GitHub README (map_readme).
"""

from __future__ import annotations

import pytest

import bridge.pipelines.bt2gh_for_pr_issues.map_funcs.readme as mod


TITLE_KEY = "README.md"


def _out_text(out: dict[str, str]) -> str:
    assert list(out.keys()) == [TITLE_KEY]
    return out[TITLE_KEY]


@pytest.fixture(autouse=True)
def _patch_badge_helpers(monkeypatch):
    """
    Keep tests stable by stubbing compose_badge + fill_template and making Badge predictable.

    - compose_badge(...) => returns a simple Badge-like object with .as_markdown()
    - fill_template(...) => does a naive placeholder replacement
    - remove_first_snippet_from_text => simple first-occurrence removal
    """

    class FakeBadge:
        def __init__(self, alt_text: str, image_url: str, link_url: str | None = None, full_match: str | None = None):
            self.alt_text = alt_text
            self.image_url = image_url
            self.link_url = link_url
            self.full_match = full_match

        def as_markdown(self) -> str:
            if self.link_url:
                return f"[![{self.alt_text}]({self.image_url})]({self.link_url})"
            return f"![{self.alt_text}]({self.image_url})"

        # crucial: allow deduplication via set()
        def __hash__(self) -> int:
            return hash((self.alt_text, self.image_url, self.link_url))

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, FakeBadge):
                return False
            return (self.alt_text, self.image_url, self.link_url) == (other.alt_text, other.image_url, other.link_url)

    def fake_compose_badge(
        *,
        label: str,
        message: str,
        color: str,
        label_color: str,
        alt_text: str,
        url: str | None = None,
        svg_path: str | None = None,
    ):
        # encode label+message into the image url so we can assert it later
        image_url = f"badges/{label}--{message}.svg"
        link_url = url
        return FakeBadge(alt_text=alt_text, image_url=image_url, link_url=link_url)

    def fake_fill_template(template: str, placeholders: dict[str, str]) -> str:
        s = template
        for k, v in placeholders.items():
            s = s.replace(f"{{{{ {k} }}}}", v)
        return s

    def fake_remove_first_snippet(text: str, snippet: str) -> str:
        idx = text.find(snippet)
        if idx < 0:
            return text
        return text[:idx] + text[idx + len(snippet) :]

    monkeypatch.setattr(mod, "compose_badge", fake_compose_badge)
    monkeypatch.setattr(mod, "fill_template", fake_fill_template)
    monkeypatch.setattr(mod, "remove_first_snippet_from_text", fake_remove_first_snippet)

    # we also need to ensure mod.Badge points to our FakeBadge for type checks in helpers
    monkeypatch.setattr(mod, "Badge", FakeBadge)

    return FakeBadge


@pytest.fixture
def _patch_extract_existing_badges(monkeypatch):
    """
    Patch _extract_existing_badges to be deterministic (so we don't need to rely on regex parsing here).
    Each test can override by re-patching if needed.
    """

    def _default(_readme: str | None):
        return []

    monkeypatch.setattr(mod, "_extract_existing_badges", _default)


@pytest.mark.parametrize(
    "bt_params, missing_key",
    [
        ({}, "name"),
        ({"name": "X"}, "biotoolsID"),
        ({"biotoolsID": "x"}, "name"),
    ],
)
def test_map_readme_requires_fields(bt_params, missing_key):
    with pytest.raises(ValueError) as e:
        mod.map_readme(gh_readme=None, bt_params=bt_params)
    assert missing_key in str(e.value)


@pytest.mark.parametrize(
    "gh_readme, expected_title_line",
    [
        (None, "# My Tool"),  # fallback title when README missing
        ("", "# My Tool"),  # fallback title when no title exists
    ],
)
def test_map_readme_creates_title_when_missing(gh_readme, expected_title_line, _patch_extract_existing_badges):
    out = mod.map_readme(
        gh_readme=gh_readme,
        bt_params={"name": "My Tool", "biotoolsID": "mytool"},
    )
    text = _out_text(out)
    assert expected_title_line in text


@pytest.mark.parametrize(
    "existing_title, readme",
    [
        ("# Existing Title", "# Existing Title\n\nSome content\n"),
        ("Project Name\n=====", "Project Name\n=====\n\nSome content\n"),
        ("<h1>HTML Title</h1>", "<h1>HTML Title</h1>\n\nSome content\n"),
    ],
)
def test_map_readme_preserves_existing_title(existing_title, readme, _patch_extract_existing_badges):
    out = mod.map_readme(
        gh_readme=readme,
        bt_params={"name": "Ignored Tool Name", "biotoolsID": "toolid"},
    )
    text = _out_text(out)
    assert existing_title in text
    # and should not include fallback title for bt_name
    assert "# Ignored Tool Name" not in text


def test_map_readme_always_adds_biotools_and_bridge_badges(_patch_extract_existing_badges):
    out = mod.map_readme(
        gh_readme="# Title\n\nBody\n",
        bt_params={"name": "Tool", "biotoolsID": "toolid"},
    )
    text = _out_text(out)

    # From fake_compose_badge image_url encoding:
    assert "badges/bio.tools--toolid.svg" in text
    assert "badges/bridge--bio.tools → github.svg" in text


def test_map_readme_adds_tool_type_badge_when_tooltype_list_present(_patch_extract_existing_badges):
    # Avoid importing real ToolTypeEnum; we only need objects with .value
    class TT:
        def __init__(self, value: str):
            self.value = value

    out = mod.map_readme(
        gh_readme="# Title\n\nBody\n",
        bt_params={"name": "Tool", "biotoolsID": "toolid", "toolType": [TT("Workflow"), TT("Command-line tool")]},
    )
    text = _out_text(out)

    # message is sorted join with " | "
    assert "badges/tool type--Command-line tool | Workflow.svg" in text


@pytest.mark.parametrize(
    "tooltype_value",
    [
        None,
        [],
        "not-a-list",
        [None],  # treated as list, but map_readme checks list and non-empty only; still allowed through,
        # yet _build_readme sorts tt.value which would explode. So map_readme *must* convert these to None.
    ],
)
def test_map_readme_ignores_invalid_tooltype(tooltype_value, _patch_extract_existing_badges):
    out = mod.map_readme(
        gh_readme="# Title\n\nBody\n",
        bt_params={"name": "Tool", "biotoolsID": "toolid", "toolType": tooltype_value},
    )
    text = _out_text(out)
    # tool type badge should not be added
    assert "badges/tool type--" not in text


def test_map_readme_preserves_existing_badges_and_deduplicates(monkeypatch):
    """
    Existing badge should be carried into output.
    If it duplicates a newly generated badge, it should only appear once.
    """
    # Use the same FakeBadge class the autouse fixture installed as mod.Badge
    FakeBadge = mod.Badge

    existing = [
        # this will be unique
        FakeBadge(alt_text="CI", image_url="badges/ci--passing.svg", link_url="https://ci.example"),
        # duplicate of the generated bio.tools badge (same alt/img/link as our fake_compose_badge emits)
        FakeBadge(alt_text="bio.tools", image_url="badges/bio.tools--toolid.svg", link_url="https://bio.tools/toolid"),
    ]

    monkeypatch.setattr(mod, "_extract_existing_badges", lambda _readme: existing)

    out = mod.map_readme(
        gh_readme="# Title\n\n[![CI](badges/ci--passing.svg)](https://ci.example)\n\nBody\n",
        bt_params={"name": "Tool", "biotoolsID": "toolid"},
    )
    text = _out_text(out)

    # CI badge preserved
    assert "badges/ci--passing.svg" in text

    # bio.tools badge appears only once
    assert text.count("badges/bio.tools--toolid.svg") == 1


def test_map_readme_keeps_rest_of_content_below_title_and_badges(monkeypatch):
    FakeBadge = mod.Badge
    existing_badges = [
        FakeBadge(
            alt_text="CI", image_url="badges/ci--passing.svg", link_url=None, full_match="![CI](badges/ci--passing.svg)"
        )
    ]

    monkeypatch.setattr(mod, "_extract_existing_badges", lambda _readme: existing_badges)

    gh_readme = (
        "# Existing Title\n"
        "\n"
        "![CI](badges/ci--passing.svg)\n"
        "\n"
        "## Usage\n"
        "Run `tool --help`.\n"
        "\n"
        "More text.\n"
    )

    out = mod.map_readme(
        gh_readme=gh_readme,
        bt_params={"name": "Tool", "biotoolsID": "toolid"},
    )
    text = _out_text(out)

    # Content should still be present
    assert "## Usage" in text
    assert "Run `tool --help`." in text
    assert "More text." in text

    # Title should be preserved, not duplicated
    assert text.count("# Existing Title") == 1

    # Original badge line should not remain in the "content" section
    # (it will exist once in the badges section though)
    assert "![CI](badges/ci--passing.svg)\n\n## Usage" not in text


def test_map_readme_returns_readme_md_key(_patch_extract_existing_badges):
    out = mod.map_readme(
        gh_readme=None,
        bt_params={"name": "Tool", "biotoolsID": "toolid"},
    )
    assert out.keys() == {"README.md"}
    assert isinstance(out["README.md"], str)
    assert out["README.md"]
