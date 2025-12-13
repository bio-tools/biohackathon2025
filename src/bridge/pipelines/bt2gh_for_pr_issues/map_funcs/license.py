"""
Map license metadata from bio.tools to GitHub.

This module compares the license recorded in bio.tools with the license
detected on a GitHub repository and, when appropriate, proposes a pull
request that adds a full LICENSE file based on the SPDX canonical text.
It applies a bio.tools-over-GitHub policy.
"""

from bridge.builders import compose_spdx_license_metadata
from bridge.core import SPDXLicense
from bridge.core.biotools import License as BTLicense
from bridge.core.github_repo import License as GHLicense
from bridge.logging import get_user_logger
from bridge.pipelines.policies.bt2gh import reconcile_bt_over_gh
from bridge.pipelines.utils import find_matching_enum_member

logger = get_user_logger()


async def map_license(gh_license: GHLicense | None, bt_license: BTLicense | None) -> dict[str, str] | None:
    """
    Propose a GitHub pull request to add a LICENSE file based on bio.tools
    license metadata, using the generic bio.tools-over-GitHub policy.

    The GitHub license (when present) is normalized via its SPDX identifier
    and compared against the bio.tools license enum. If bio.tools provides
    a license, the full canonical license text is fetched from the SPDX service
    and proposed as a new ``LICENSE.txt`` file. If GitHub already declares a different license,
    that value is treated as authoritative, a conflict is logged, but the pull
    request is still proposed.

    Parameters
    ----------
    gh_license : GHLicense | None
        License metadata detected on the GitHub repository, or ``None``
        if no license is declared.
    bt_license : BTLicense | None
        License value from the bio.tools entry, represented as a bio.tools
        license enum, or ``None`` if not available.

    Returns
    -------
    dict[str, str] | None
        A dictionary with the filename ``LICENSE.txt`` as key and the
        full license text as value, or ``None`` if no pull request should
        be created under the policy.
    """
    gh_norm = find_matching_enum_member(gh_license.spdx_id, BTLicense) if gh_license else None
    bt_norm = bt_license

    async def make_pr(bt_value: BTLicense) -> dict[str, str] | None:
        spdx_id = bt_value.value
        try:
            license: SPDXLicense = await compose_spdx_license_metadata(spdx_id)
            full_text = license.licenseText
            logger.added(f"LICENSE.txt with full text for SPDX ID '{spdx_id}'")
            return {"LICENSE.txt": full_text}
        except Exception as e:
            logger.unchanged(f"could not retrieve full text for SPDX ID '{spdx_id}': {e}")
            return None

    return await reconcile_bt_over_gh(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        make_output=make_pr,
        log_label="license",
    )
