"""
TODO
"""

from bridge.builders import compose_spdx_license_metadata
from bridge.core import SPDXLicense
from bridge.core.biotools import License as BTLicense
from bridge.core.github_repo import License as GHLicense
from bridge.logging import get_user_logger
from bridge.pipelines.policies.bt2gh import reconcile_bt_over_gh
from bridge.pipelines.utils import find_matching_enum_member

logger = get_user_logger()


def map_license(gh_license: GHLicense | None, bt_license: BTLicense | None) -> dict[str, str] | None:
    """
    TODO
    """
    gh_norm = find_matching_enum_member(gh_license.spdx_id, BTLicense) if gh_license else None
    bt_norm = bt_license

    def make_pr(bt_value: BTLicense) -> dict[str, str]:
        spdx_id = bt_value.spdx_id
        try:
            license: SPDXLicense = compose_spdx_license_metadata(spdx_id)
            full_text = license.full_text
            logger.added(f"LICENSE.txt with full text for SPDX ID '{spdx_id}'")
            return {"LICENSE.txt": full_text}
        except Exception:
            logger.unchanged(f"could not retrieve full text for SPDX ID '{spdx_id}'")
            return None

    return reconcile_bt_over_gh(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        make_output=make_pr,
        log_label="license",
    )
