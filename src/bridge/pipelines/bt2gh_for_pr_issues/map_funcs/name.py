"""
Map repository name from bio.tools to GitHub.

This module compares the bio.tools name and ID with the GitHub repository name.
If the GitHub name does not match either, it proposes an issue suggesting
to update the repository name to the bio.tools ID.
It applies a bio.tools-over-GitHub issue policy.
"""

from bridge.logging import get_user_logger
from bridge.pipelines.policies.bt2gh import reconcile_bt_over_gh
from bridge.pipelines.utils import normalize_text, str_contain_each_other

logger = get_user_logger()


async def map_name(gh_name: str | None, bt_params: dict[str, str | None] | None) -> dict[str, str] | None:
    """
    Propose a GitHub issue to update the GitHub repository name based on bio.tools name and ID metadata,
    using the generic bio.tools-over-GitHub issue policy.

    Parameters
    ----------
    gh_name : str | None
        GitHub repository name.
    bt_params : dict[str, str | None] | None
        A dictionary containing existing bio.tools metadata parameters.
        Expected keys:
        - ``"name"``       : bio.tools name
        - ``"biotoolsID"`` : bio.tools ID

    Returns
    -------
    dict[str, str] | None
        A mapping with the issue title as key and the issue body as value,
        or ``None`` if no issue is to be created.
    """
    if bt_params is None:
        logger.unchanged("No bio.tools params found, nothing to map.")
        return None

    bt_name = bt_params.get("name")
    bt_id = bt_params.get("biotoolsID")

    gh_norm = normalize_text(gh_name)
    bt_name_norm = normalize_text(bt_name)
    bt_id_norm = normalize_text(bt_id)

    def make_issue(name: str) -> dict[str, str]:
        return {
            "Update repository name from bio.tools metadata": (
                f"The GitHub repository name '{gh_name}' does not match the bio.tools "
                f"name '{bt_name}' or ID '{bt_id}'.\n\n"
                f"Proposed new name: '{bt_id}'.\n\n"
                "Please consider updating the repository name."
            ),
        }

    return await reconcile_bt_over_gh(
        bt_norm=bt_id_norm,
        gh_norm=gh_norm,
        make_output=make_issue,
        log_label="name/id",
        equality_fn=lambda gh, bt: str_contain_each_other(gh, bt) or str_contain_each_other(gh, bt_name_norm),
    )
