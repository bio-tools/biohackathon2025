"""
TODO
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any

from packaging.version import InvalidVersion, Version

from bridge.core.biotools import VersionType as BiotoolsVersionType

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

    Used to classify free-text version strings into comparable groups:
    semantic versions, dates, integers, numeric ranges, and raw labels.
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
        The kind of version parsed (SEMVER, DATE, INT, RANGE, RAW).
    value : Any
        The parsed value:
        - SEMVER: packaging.version.Version
        - DATE  : datetime.date
        - INT   : int
        - RANGE : (ParsedVersion, ParsedVersion)  # [low, high]
        - RAW   : str
    raw : str
        The original version string.
    """

    kind: VersionKind
    value: Any  # Version | date | int | (ParsedVersion, ParsedVersion) | str
    raw: str

    def _normalized_for_comparison(self) -> tuple[VersionKind, Any] | None:
        """
        Normalize the version into a comparable (kind, value) pair.

        RANGE values are reduced to their upper bound. RAW values and
        unsupported kinds return ``None``.

        Returns
        -------
        tuple[VersionKind, Any] | None
            Normalized comparison tuple, or ``None`` if the version is
            not safely comparable.
        """
        if self.kind == VersionKind.RANGE:
            lo, hi = self.value
            # represent range by upper bound
            return hi._normalized_for_comparison()

        if self.kind in {VersionKind.SEMVER, VersionKind.DATE, VersionKind.INT}:
            return (self.kind, self.value)

        # raw and anything else: not safely comparable
        return None

    def __eq__(self, other: object) -> bool:
        """
        Compare two parsed versions for equality.

        If both versions can be normalized, equality is based on their
        normalized (kind, value) pair. Otherwise, equality falls back
        to raw string comparison.
        """
        if not isinstance(other, ParsedVersion):
            return NotImplemented

        # same normalized (kind, value) if possible,
        # otherwise fall back to raw string equality.
        self_norm = self._normalized_for_comparison()
        other_norm = other._normalized_for_comparison()

        if self_norm is not None and other_norm is not None:
            return self_norm == other_norm

        return self.raw == other.raw

    def __lt__(self, other: object) -> bool:
        """
        Define strict ordering between comparable parsed versions.

        Ordering is only defined when both versions normalize to the same
        comparable kind. In all other cases, the versions are treated as
        incomparable and ``NotImplemented`` is returned.
        """
        if not isinstance(other, ParsedVersion):
            return NotImplemented

        self_norm = self._normalized_for_comparison()
        other_norm = other._normalized_for_comparison()

        # if either cannot be normalized or kinds differ, treat as incomparable
        if self_norm is None or other_norm is None:
            return NotImplemented

        kind_a, val_a = self_norm
        kind_b, val_b = other_norm

        if kind_a != kind_b:
            return NotImplemented

        return val_a < val_b


def _parse_version_label(label: str) -> ParsedVersion:
    """
    Parse a free-text version label into a structured ``ParsedVersion``.

    The following formats are recognized, in order:
    - Numeric ranges (e.g. "1.0 - 2.0")
    - Dates (YYYY-MM-DD, YYYY.MM.DD, YYYYMMDD)
    - Plain integers
    - Semantic-style versions (with optional "v" prefix)
    - Raw strings (fallback)

    Parameters
    ----------
    label : str
        Raw version label.

    Returns
    -------
    ParsedVersion
        Structured parsed representation of the version label.
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


def any_bt_newer_than_gh(
    gh_latest: BiotoolsVersionType,
    bt_versions: list[BiotoolsVersionType],
) -> bool:
    """
    Check whether any bio.tools version appears newer than the GitHub latest.

    Versions are parsed into ``ParsedVersion`` objects and compared using
    their defined partial ordering. Incomparable versions (e.g. raw or
    differing kinds) are ignored.

    Parameters
    ----------
    gh_latest : BiotoolsVersionType
        GitHub latest release tag.
    bt_versions : list[BiotoolsVersionType]
        Existing bio.tools versions.

    Returns
    -------
    bool
        ``True`` if any bio.tools version is strictly newer than the GitHub
        latest version under the comparison rules, otherwise ``False``.
    """
    gh_parsed = _parse_version_label(gh_latest.root)

    for bt in bt_versions:
        bt_parsed = _parse_version_label(bt.root)
        try:
            if bt_parsed > gh_parsed:
                return True
        except TypeError:
            # incomparable (different kind / raw) -> ignore
            continue

    return False


def find_latest_bt_version(bt_versions: list[BiotoolsVersionType] | None) -> BiotoolsVersionType | None:
    """
    Find the latest bio.tools version from a list of versions.

    Versions are parsed into ``ParsedVersion`` objects and compared using
    their defined partial ordering. Incomparable versions (e.g. raw or
    differing kinds) are ignored.

    Parameters
    ----------
    bt_versions : list[BiotoolsVersionType] | None
        Existing bio.tools versions, or ``None``.

    Returns
    -------
    BiotoolsVersionType | None
        The latest bio.tools version, or ``None`` if no comparable versions
        were found.
    """
    latest_bt: BiotoolsVersionType | None = None
    latest_parsed: ParsedVersion | None = None

    if not bt_versions:
        return None

    for bt in bt_versions:
        bt_parsed = _parse_version_label(bt.root)
        if latest_parsed is None:
            latest_bt = bt
            latest_parsed = bt_parsed
            continue

        try:
            if bt_parsed > latest_parsed:
                latest_bt = bt
                latest_parsed = bt_parsed
        except TypeError:
            # incomparable (different kind / raw) -> ignore
            continue

    return latest_bt
