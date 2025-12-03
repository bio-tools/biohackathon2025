"""
Map bio.tools metadata onto a GitHub README and inject badges.

This module takes an existing README.md (if any) and bio.tools metadata
for a tool and produces an updated README that:

- preserves an existing project title when possible,
- preserves existing badges,
- adds "bridge" and "bio.tools" badges,
- adds a "tool type" badge based on bio.tools metadata (if available),
- keeps the rest of the README content intact (below the title and badges).
"""

import re
from collections.abc import Iterable
from typing import Any

from bridge.core.biotools import ToolTypeEnum
from bridge.logging import get_user_logger
from bridge.pipelines.utils import (
    Badge,
    compose_badge,
    fill_template,
    remove_first_snippet_from_text,
)

logger = get_user_logger()

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
    Deduplicate a sequence of badges while preserving order.

    Two badges are considered duplicates if their `Badge` instances compare
    equal. The first occurrence is kept; all later duplicates
    are discarded.

    Parameters
    ----------
    badges : Iterable[Badge]
        An iterable of `Badge` objects, typically combining newly generated
        and already existing badges.

    Returns
    -------
    list[Badge]
        A list of unique badges in their original order of first appearance.
    """
    seen: set[Badge] = set()
    result: list[Badge] = []

    for badge in badges:
        if badge in seen:
            logger.unchanged(f"Badge already exists: {badge.alt_text}")
            continue
        seen.add(badge)
        result.append(badge)

    return result


def _is_likely_badge_image_url(url: str) -> bool:
    """
    Heuristic check whether a URL likely points to a badge image.

    Parameters
    ----------
    url : str
        The URL to evaluate.

    Returns
    -------
    bool
        True if the URL likely points to a badge image, False otherwise.
    """
    u = url.lower()
    if "shields.io" in u:
        return True
    if u.startswith("http://") or u.startswith("https://"):
        return False
    if "badge" in u and u.endswith(".svg"):
        return True
    return False


def _extract_existing_badges(gh_readme: str | None) -> list[Badge]:
    """
    Parse and extract badge definitions from a README.

    This function scans the README content for Markdown-style badges, both
    with and without links:
    - `[![alt](img)](link)` (badge wrapped in a link)
    - `![alt](img)` (image-only badge)

    For each match, a `Badge` object is created if the image URL appears to
    point to a badge (based on simple heuristics).
    Invalid or unparseable badges are skipped.

    Parameters
    ----------
    gh_readme : str | None
        The README content as a string, or ``None`` if no README exists.

    Returns
    -------
    list[Badge]
        A list of `Badge` objects representing all parseable badges found
        in the README. The list may be empty.
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

        if not _is_likely_badge_image_url(img):
            continue

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
    Attempt to extract the project's top-level title from the README.

    This is a best-effort heuristic that tries three common heading styles,
    in order of preference:
    1. ATX H1:    '# Title'
    2. Setext H1: 'Title' on one line, followed by '=====' or '-----'
    3. HTML H1:   '<h1>Title</h1>'

    The function returns the exact snippet representing the title block:
    - For ATX: the full line including '#'.
    - For Setext: the title line plus its underline, separated by a newline.
    - For HTML: the full `<h1>...</h1>` element.

    Parameters
    ----------
    gh_readme : str | None
        The README content as a string, or ``None`` if no README exists.

    Returns
    -------
    str | None
        The raw title snippet as it appears in the README, or ``None`` if no
        title-like structure is found.
    """
    if gh_readme is None:
        return None

    lines = (gh_readme or "").splitlines()

    # "# Title"
    for line in lines:
        m = ATX_H1_PATTERN.match(line)
        if m:
            return m.group(0)

    # "Title" + "====="
    for i in range(len(lines) - 1):
        title_line = lines[i]
        underline = lines[i + 1]
        if not title_line.strip():
            continue
        if SETEXT_UNDERLINE_PATTERN.match(underline):
            return title_line + "\n" + underline

    # HTML <h1>Title</h1>
    for line in lines:
        m = HTML_H1_PATTERN.search(line)
        if m:
            return m.group(0)

    # No title found
    return None


def _build_readme(gh_readme: str | None, bt_name: str, bt_id: str, bt_tool_types: list[ToolTypeEnum] | None) -> str:
    """
    Construct an updated README from existing content and bio.tools metadata.

    Steps performed:
    1. Builds a set of new badges:
       - A 'bridge' badge indicating the README was generated/updated by
         the bridge pipeline.
       - A 'bio.tools' badge linking to the corresponding bio.tools entry.
       - A 'tool type' badge summarizing the `toolType` values (if available).
    2. Extracts existing badges from the README.
    3. Merges new and existing badges, deduplicating so that existing badges
       are not duplicated.
    4. Extracts a project title from the README if possible; otherwise, uses
       '# <bt_name>' as the title.
    5. Strips the original title and badges from the README to obtain the
       remaining content body.
    6. Renders a new README using a simple template that places the title, badges,
       and remaining content in order.

    Parameters
    ----------
    gh_readme : str | None
        The current README content, or ``None`` for an empty README.
    bt_name : str
        The `name` of the tool from bio.tools metadata.
    bt_id : str
        The `biotoolsID` of the tool from bio.tools metadata.
    bt_tool_types : list[ToolTypeEnum] | None
        A list of tool types (`toolType` field from bio.tools), or ``None``
        if not available or not valid.

    Returns
    -------
    str
        The updated README content including title, badges, and the remaining
        original content.
    """
    # handle badges

    bridge_badge = compose_badge(
        label="bridge",
        message="bio.tools → github",
        color="blue",
        label_color="orange",
        alt_text="Bridge",
        url="https://bio-tools.github.io/biohackathon2025/",
        svg_path=BRIDGE_BADGE_LOGO_PATH,
    )

    new_badges = []
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
    badges = _deduplicate_badges(new_badges + existing_badges + [bridge_badge])

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
    Map bio.tools metadata onto a GitHub README and return updated content.

    Steps performed:
    1. Validates and interprets the required fields are present in `bt_params`.
    2. Calls `_build_readme` to construct a new README that includes:
       - an existing title (if any), or a new one based on `bt_params['name']`,
       - merged badges (new bridge/bio.tools/tool type + existing badges),
       - the remaining original README content.
    3. Returns the updated README under the key `"README.md"`.

    Parameters
    ----------
    gh_readme : str | None
        The current README content from GitHub, or ``None`` if the file does
        not exist yet.
    bt_params : dict[str, Any]
        The bio.tools tool metadata as a dictionary.
        Expected fields:
        - 'name'       : Name of the tool.
        - 'biotoolsID' : bio.tools identifier of the tool.
        - 'toolType'   : Optional list of tool types (typically `ToolTypeEnum`).

    Returns
    -------
    dict[str, str]
        A dictionary with the filename `"README.md"` as key,
        and the updated README content as value.

    Raises
    ------
    ValueError
        If required fields are missing from `bt_params`.
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

    gh_readme_updated = _build_readme(gh_readme, bt_name, bt_id, bt_tool_types)

    if gh_readme == gh_readme_updated:
        logger.unchanged("README.md remains unchanged.")
    else:
        logger.added("Updated README.md with bio.tools metadata and badges.")

    return {"README.md": gh_readme_updated}
