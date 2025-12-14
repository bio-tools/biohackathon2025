"""
Unit tests for shared version parsing and comparison utilities.
"""

from datetime import date

import pytest

import bridge.pipelines.shared.version as vp
from bridge.core.biotools import VersionType as BiotoolsVersionType


def VT(s: str) -> BiotoolsVersionType:
    return BiotoolsVersionType(root=s)


class TestParseVersionLabel:
    @pytest.mark.parametrize(
        "label, expected_kind",
        [
            ("1.0 - 2.0", vp.VersionKind.RANGE),
            ("1.0 – 2.0", vp.VersionKind.RANGE),  # en dash with spaces
            ("2025-12-13", vp.VersionKind.DATE),
            ("2025.12.13", vp.VersionKind.DATE),
            ("20251213", vp.VersionKind.DATE),
            ("42", vp.VersionKind.INT),
            ("v1.2.3", vp.VersionKind.SEMVER),
            ("V1.2", vp.VersionKind.SEMVER),
            ("release-candidate", vp.VersionKind.RAW),
        ],
    )
    def test_kind_detection(self, label, expected_kind):
        parsed = vp._parse_version_label(label)
        assert parsed.kind == expected_kind
        assert parsed.raw == label.strip()

    def test_date_parsing_value(self):
        parsed = vp._parse_version_label("2025-12-13")
        assert parsed.kind == vp.VersionKind.DATE
        assert parsed.value == date(2025, 12, 13)


class TestParsedVersionComparison:
    def test_range_normalizes_to_upper_bound_for_equality(self):
        a = vp._parse_version_label("1.0 - 2.0")
        b = vp._parse_version_label("2.0")
        assert a == b

    def test_semver_ordering(self):
        a = vp._parse_version_label("1.2.3")
        b = vp._parse_version_label("1.2.4")
        assert a < b

    def test_incomparable_kinds_raise_typeerror_on_gt(self):
        a = vp._parse_version_label("2025-12-13")
        b = vp._parse_version_label("1.2.3")
        with pytest.raises(TypeError):
            _ = a > b


class TestAnyBtNewerThanGh:
    def test_true_when_bt_semver_newer(self):
        gh_latest = VT("1.2.3")
        bt_versions = [VT("1.2.4"), VT("1.0.0")]
        assert vp.any_bt_newer_than_gh(gh_latest, bt_versions) is True

    def test_ignores_incomparable_versions(self):
        gh_latest = VT("1.2.3")
        bt_versions = [VT("2025-12-13"), VT("release-candidate")]
        assert vp.any_bt_newer_than_gh(gh_latest, bt_versions) is False

    def test_range_compares_by_upper_bound(self):
        gh_latest = VT("1.2.3")
        bt_versions = [VT("1.0 - 2.0")]
        assert vp.any_bt_newer_than_gh(gh_latest, bt_versions) is True


class TestFindLatestBtVersion:
    def test_none_on_none_or_empty(self):
        assert vp.find_latest_bt_version(None) is None
        assert vp.find_latest_bt_version([]) is None

    def test_finds_latest_semver(self):
        bt_versions = [VT("1.2.3"), VT("1.10.0"), VT("1.3.0")]
        latest = vp.find_latest_bt_version(bt_versions)
        assert latest is not None
        assert latest.root == "1.10.0"

    def test_mixed_kinds_keeps_first_if_incomparable(self):
        """
        Current behavior: the first entry becomes the baseline even if RAW.
        Later comparable SEMVER entries are incomparable to RAW and won't replace it.
        """
        bt_versions = [VT("release-x"), VT("1.2.3"), VT("1.2.4")]
        latest = vp.find_latest_bt_version(bt_versions)
        assert latest is not None
        assert latest.root == "release-x"
