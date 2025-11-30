"""
TODO
"""

from bridge.core.biotools import License as BTLicense
from bridge.core.github_repo import License as GHLicense
from bridge.pipelines.policies.bt2gh import reconcile_bt_over_gh
from bridge.pipelines.utils import find_matching_enum_member


def map_license(gh_license: GHLicense | None, bt_license: BTLicense | None) -> dict[str, str] | None:
    """
    TODO
    """
    gh_norm = find_matching_enum_member(gh_license.spdx_id, BTLicense) if gh_license else None
    bt_norm = bt_license

    def make_pr(bt_value: BTLicense) -> dict[str, str]:
        return {"a": "b"}

    return reconcile_bt_over_gh(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        make_output=make_pr,
        log_label="license",
    )
