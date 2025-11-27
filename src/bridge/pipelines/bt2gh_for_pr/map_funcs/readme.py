"""
Map bio.tools metadata to GitHub README, add badges.
"""

import re
from collections.abc import Iterable
from typing import Any

from bridge.core.biotools import ToolTypeEnum
from bridge.pipelines.utils import (
    Badge,
    compose_badge,
    fill_template,
    remove_first_snippet_from_text,
)

BRIDGE_BADGE_LOGO_PATH = "assets/logos/bridge.svg"
BIOTOOLS_BADGE_LOGO_PATH = "assets/logos/biotools.svg"
BADGE_PATTERN = re.compile(
    r"""
    \[
        !\[(?P<alt1>[^\]]*)\]
        \((?P<img1>[^)]+)\)
    \]
    \((?P<link1>[^)]+)\)
    |
    !\[(?P<alt2>[^\]]*)\]
    \((?P<img2>[^)]+)\)
    """,
    re.VERBOSE,
)
ATX_H1_PATTERN = re.compile(r"^\s*#(?!#)\s+(.*\S.*)$")
SETEXT_UNDERLINE_PATTERN = re.compile(r"^[=-]{3,}\s*$")
HTML_H1_PATTERN = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE)
README_TEMPLATE = """\
{{ TITLE }}

{{ BADGES }}

{{ CONTENT }}
"""


def _deduplicate_badges(badges: Iterable[Badge]) -> list[Badge]:
    """
    Deduplicate badges while:
    - preserving original order
    - preferring earliest occurrence

    Parameters
    ----------
    badges : Iterable[Badge]
        An iterable of Badge objects.

    Returns
    -------
    list[Badge]
        A list of unique Badge objects in their original order.
    """
    seen: set[Badge] = set()
    result: list[Badge] = []

    for badge in badges:
        if badge in seen:
            continue
        seen.add(badge)
        result.append(badge)

    return result


def _extract_existing_badges(gh_readme: str | None) -> list[Badge]:
    """
    Extract existing badges from a GitHub README.

    Parameters
    ----------
    gh_readme : str | None
        The content of the GitHub README.

    Returns
    -------
    list[Badge]
        A list of extracted Badge objects.
    """
    badges: list[Badge] = []

    for match in BADGE_PATTERN.finditer(gh_readme or ""):
        if match.group("alt1") is not None:
            alt = match.group("alt1").strip()
            img = match.group("img1").strip()
            link = match.group("link1").strip()
        else:
            alt = match.group("alt2").strip()
            img = match.group("img2").strip()
            link = None

        try:
            badge = Badge(
                alt_text=alt,
                image_url=img,
                link_url=link,
                full_match=match.group(0),
            )
        except Exception:
            # invalid URL or malformed badge, skip
            continue

        badges.append(badge)

    return badges


def _extract_project_title(gh_readme: str | None) -> str | None:
    """
    Best-effort extraction of a project title from a README.

    Order of preference:
    1. First ATX H1 (# Title)
    2. First Setext H1 (Title + =====)
    3. First HTML <h1>...</h1>

    Parameters
    ----------
    gh_readme : str | None
        The content of the GitHub README.

    Returns
    -------
    str | None
        The joined lines extracted raw project title text, or None if not found.
    """
    if gh_readme is None:
        return None

    lines = (gh_readme or "").splitlines()

    # "# Title"
    for line in lines:
        m = ATX_H1_PATTERN.match(line)
        if m:
            # return whatever comes after the leading "# " together with #
            return m.group(0)

    # "Title" + "====="
    for i in range(len(lines) - 1):
        title_line = lines[i]
        underline = lines[i + 1]
        if not title_line.strip():
            continue
        if SETEXT_UNDERLINE_PATTERN.match(underline):
            # return the title line as-is together with underline
            return title_line + "\n" + underline

    # HTML <h1>Title</h1>
    for line in lines:
        m = HTML_H1_PATTERN.search(line)
        if m:
            # return the lines spanning the tags
            return m.group(0)

    # No title found
    return None


def _build_readme(gh_readme: str | None, bt_name: str, bt_id: str, bt_tool_types: list[ToolTypeEnum] | None) -> str:
    # handle badges
    new_badges = []

    bridge_badge = compose_badge(
        label="bridge",
        message="bio.tools → github",
        color="blue",
        label_color="orange",
        alt_text="Bridge",
        url="https://bio-tools.github.io/biohackathon2025/",
        svg_path=BRIDGE_BADGE_LOGO_PATH,
    )
    new_badges.append(bridge_badge)

    biotools_badge = compose_badge(
        label="bio.tools",
        message=bt_id,
        color="blue",
        label_color="gray",
        alt_text="bio.tools",
        url=f"https://bio.tools/{bt_id}",
        svg_path=BIOTOOLS_BADGE_LOGO_PATH,
    )
    new_badges.append(biotools_badge)

    if bt_tool_types is not None:
        tool_types_badge = compose_badge(
            label="tool type",
            message=" | ".join(sorted(tt.value for tt in bt_tool_types)),
            color="blue",
            label_color="gray",
            alt_text="Tool Type",
        )
        new_badges.append(tool_types_badge)

    existing_badges = _extract_existing_badges(gh_readme)
    badges = _deduplicate_badges(new_badges + existing_badges)

    # handle title
    existing_title = _extract_project_title(gh_readme)
    title = existing_title or f"# {bt_name}"

    # extract remaining content after title & badges
    content = gh_readme or ""
    if existing_title is not None:
        content = remove_first_snippet_from_text(gh_readme, existing_title)
    for badge in existing_badges:
        if badge.full_match is not None:
            content = remove_first_snippet_from_text(content, badge.full_match)
    lines = content.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    content = "\n".join(lines)

    # compose final README
    placeholders = {
        "TITLE": title,
        "BADGES": "\n".join(badge.as_markdown() for badge in badges) or "",
        "CONTENT": content,
    }

    readme_top = fill_template(README_TEMPLATE, placeholders)
    return readme_top


def map_readme(gh_readme: str | None, bt_params: dict[str, Any]) -> dict[str, str]:
    """
    Map and merge bio.tools metadata with GitHub README content.

    Parameters
    ----------
    gh_readme : str | None
        The content of the GitHub README.
    bt_params : dict[str, Any]
        The bio.tools tool relevant metadata as a dictionary.
        Should contain:
        - name - Name of the tool.
        - biotoolsID - The bio.tools ID of the tool.
        - toolType - List of tool types (ToolTypeEnum).

    Returns
    -------
    dict[str, str]
        A dictionary with the updated README content under the key "README.md".

    Raises
    ------
    ValueError
        If required fields are missing in bt_params.
    """
    bt_name = bt_params.get("name", None)
    bt_id = bt_params.get("biotoolsID", None)
    bt_tool_types = bt_params.get("toolType", None)
    if bt_name is None:
        raise ValueError("bt_params must contain 'name' field.")
    if bt_id is None:
        raise ValueError("bt_params must contain 'biotoolsID' field.")
    if bt_tool_types is None or not isinstance(bt_tool_types, list) or not bt_tool_types:
        bt_tool_types = None
    gh_readme = _build_readme(gh_readme, bt_name, bt_id, bt_tool_types)
    return {"README.md": gh_readme}
