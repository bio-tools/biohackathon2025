"""
Mapping releases for version metadata.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any

from packaging.version import InvalidVersion, Version

from bridge.core.biotools import VersionType
from bridge.logging import get_user_logger

logger = get_user_logger()

_SEMVER_PREFIX_RE = re.compile(r"^[vV]?(\d+\.\d+(?:\.\d+)?(?:[^\s]*)?)$")
_RANGE_SEP_RE = re.compile(r"\s*[-–]\s*")  # hyphen or en dash
_DATE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("%Y-%m-%d", re.compile(r"^\d{4}-\d{2}-\d{2}$")),
    ("%Y.%m.%d", re.compile(r"^\d{4}\.\d{2}\.\d{2}$")),
    ("%Y%m%d", re.compile(r"^\d{8}$")),
]


class VersionKind(Enum):
    """
    Enumeration of version kinds.
    """

    SEMVER = auto()
    DATE = auto()
    INT = auto()
    RANGE = auto()
    RAW = auto()


@dataclass(frozen=True)
class ParsedVersion:
    """
    Parsed version representation.

    Parameters
    ----------
    kind : VersionKind
        The kind of version parsed.
    value : Any
        The parsed value, type depends on `kind`.
    raw : str
        The original version string.
    """

    kind: VersionKind
    value: Any  # Version | date | int | (ParsedVersion, ParsedVersion) | str
    raw: str


def _parse_version_label(label: str) -> ParsedVersion:
    """
    Parse a free-text version label into a typed representation
    (semver-ish, date, integer, range, or raw).
    """
    s = label.strip()

    # range: "A - B" or "A – B"
    if _RANGE_SEP_RE.search(s):
        parts = _RANGE_SEP_RE.split(s, maxsplit=1)
        if len(parts) == 2:
            lo = _parse_version_label(parts[0])
            hi = _parse_version_label(parts[1])
            return ParsedVersion(VersionKind.RANGE, (lo, hi), s)

    # date formats
    for fmt, pattern in _DATE_PATTERNS:
        if pattern.match(s):
            try:
                dt = datetime.strptime(s, fmt).date()
                return ParsedVersion(VersionKind.DATE, dt, s)
            except ValueError:
                pass

    # plain integer
    if re.fullmatch(r"\d+", s):
        return ParsedVersion(VersionKind.INT, int(s), s)

    # semver-ish via packaging.Version (optional "v" prefix)
    candidate = s
    m = _SEMVER_PREFIX_RE.match(s)
    if m:
        candidate = m.group(1)

    try:
        v = Version(candidate)
        return ParsedVersion(VersionKind.SEMVER, v, s)
    except InvalidVersion:
        # not semver; fall through
        pass

    # fallback: raw string, not safely comparable
    return ParsedVersion(VersionKind.RAW, s, s)


def map_version(gh_latest_version_tag: str | None, bt_versions: list[VersionType] | None) -> list[VersionType] | None:
    """
    Map GitHub releases smetadata to bio.tools version metadata.
    """
    if not gh_latest_version_tag:
        # if no GitHub version, return bio.tools version, which may be None
        logger.unchanged("GitHub has no latest version tag, nothing to map")
        return bt_versions

    latest_version_tag_as_bt = VersionType(root=gh_latest_version_tag)

    if not bt_versions:
        # if no bio.tools version, return GitHub version as list
        logger.added(f"version '{gh_latest_version_tag}'")
        return [latest_version_tag_as_bt]

    # if gh version not in bt versions
    if not any(v.root == latest_version_tag_as_bt.root for v in bt_versions):
        if any(bt > latest_version_tag_as_bt for bt in bt_versions):
            # if any version in bt_version is newer than gh_version, consider conflict
            logger.conflict(
                f"bio.tools version(s) '{bt_versions}' is/are newer than"
                f" GitHub latest version '{gh_latest_version_tag}'"
            )
            return [latest_version_tag_as_bt]
        # if both versions exist, but GitHub version not in bio.tools, add it
        logger.added(f"version '{gh_latest_version_tag}' to existing bio.tools versions '{bt_versions}'")
        return bt_versions + [latest_version_tag_as_bt]

    logger.exact(f"latest version '{gh_latest_version_tag}' already in bio.tools")
    return bt_versions
