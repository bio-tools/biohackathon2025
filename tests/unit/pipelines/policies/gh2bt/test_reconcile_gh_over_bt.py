"""
Unit tests for reconcile_gh_over_bt.

These tests focus strictly on reconciliation behavior, not logging.
"""

import bridge.pipelines.policies.gh2bt as recon


class TestReconcileGhOverBt:
    def test_github_silent_preserves_bt_value(self):
        bt_value = "existing-bt"

        result = recon.reconcile_gh_over_bt(
            gh_norm=None,
            bt_norm="whatever",
            bt_value=bt_value,
            build_bt_from_gh=lambda x: f"bt:{x}",
            log_label="license",
        )

        assert result == bt_value

    def test_github_value_added_when_bt_missing(self):
        result = recon.reconcile_gh_over_bt(
            gh_norm="MIT",
            bt_norm=None,
            bt_value=None,
            build_bt_from_gh=lambda x: f"bt:{x}",
            log_label="license",
        )

        assert result == "bt:MIT"

    def test_github_value_ignored_if_cannot_build_bt(self):
        bt_value = "keep-this"

        result = recon.reconcile_gh_over_bt(
            gh_norm="something",
            bt_norm=None,
            bt_value=bt_value,
            build_bt_from_gh=lambda _x: None,
            log_label="homepage",
        )

        assert result == bt_value

    def test_equal_values_preserve_existing_bt(self):
        bt_value = "keep-bt"

        result = recon.reconcile_gh_over_bt(
            gh_norm="same",
            bt_norm="same",
            bt_value=bt_value,
            build_bt_from_gh=lambda x: x,
            log_label="homepage",
        )

        assert result == bt_value

    def test_conflict_overwrites_with_github_value(self):
        result = recon.reconcile_gh_over_bt(
            gh_norm="new",
            bt_norm="old",
            bt_value="old-bt",
            build_bt_from_gh=lambda x: f"bt:{x}",
            log_label="languages",
        )

        assert result == "bt:new"

    def test_custom_equality_fn_is_used(self):
        """
        Equality is determined by the custom equality_fn, not by ==.
        """

        bt_value = ["preserve-this"]

        def build_bt_from_gh(gh_norm):
            return set(gh_norm)

        def equality_fn(built_bt, bt_norm):
            return built_bt == bt_norm

        result = recon.reconcile_gh_over_bt(
            gh_norm=["py", "c++"],
            bt_norm={"c++", "py"},
            bt_value=bt_value,
            build_bt_from_gh=build_bt_from_gh,
            log_label="languages",
            equality_fn=equality_fn,
        )

        assert result == bt_value
