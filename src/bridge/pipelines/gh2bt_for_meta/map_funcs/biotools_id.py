"""
Map GitHub repository name to bio.tools ID.

This module reconciles the GitHub repository name with the bio.tools ID.
It applies a policy that prefers the GitHub name while ensuring uniqueness
within bio.tools, generating alternative IDs if necessary.
"""

import httpx

from bridge.builders import compose_biotools_metadata
from bridge.logging import get_user_logger
from bridge.pipelines.utils import normalize_text, str_contain_each_other

logger = get_user_logger()


async def _matching_biotools_id_exists(biotools_id: str) -> bool:
    """
    Check if a bio.tools entry with the given ID already exists.

    The check is performed by attempting to fetch bio.tools metadata
    for the given ID. If a 404 Not Found error is returned, the ID
    does not exist. Any other error is treated as an indication that
    the ID may exist, to avoid false negatives.

    Parameters
    ----------
    biotools_id : str
        Candidate bio.tools ID to check.

    Returns
    -------
    bool
        True if a matching bio.tools entry exists, False otherwise.
    """
    try:
        matching_bt_metadata = await compose_biotools_metadata(identifier=biotools_id)
    except Exception as e:
        if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
            return False
        else:
            logger.added(f"Failed to check existing bio.tools ID '{biotools_id}': {e}. Assuming it exists.")
            return True

    return matching_bt_metadata is not None


async def map_biotools_id(gh_name: str | None, bt_id: str | None) -> str | None:
    """
    Map and reconcile GitHub repository name to bio.tools ID.

    Policy:
    1. If no GitHub repo name is available, preserve existing bio.tools ID (even if None).
    2. If the existing bio.tools ID and GitHub repo name contain each other
       (case-insensitive), preserve the existing bio.tools ID.
    3. If they do not contain each other, log a conflict but continue.
    4. If the GitHub repo name is not already used as a bio.tools ID,
       use it as the new bio.tools ID.
    5. If the GitHub repo name is already used as a bio.tools ID,
       attempt to generate a unique ID by appending suffixes ``-1``, ``-2``, ...
       up to ``-99``. If a unique ID is found, use it.
    6. If no unique ID can be generated, log a note and return ``None``,
       requiring manual intervention.

    Parameters
    ----------
    gh_name : str | None
        GitHub repository name.
    bt_id : str | None
        Existing bio.tools ID.

    Returns
    -------
    str | None
        Mapped bio.tools ID, or ``None`` if mapping failed.
    """
    if gh_name is None:
        logger.unchanged("No GitHub repo name found, nothing to map.")
        return bt_id

    gh_norm = normalize_text(gh_name)
    bt_norm = normalize_text(bt_id or "")

    if bt_id is not None and str_contain_each_other(gh_norm, bt_norm):
        logger.exact(f"bio.tools ID '{bt_id}' and GitHub repo name '{gh_name}' contain each other")
        return bt_id

    if bt_id is not None and not str_contain_each_other(gh_norm, bt_norm):
        logger.conflict(f"bio.tools ID '{bt_id}' and GitHub repo name '{gh_name}' do not contain each other")

    if not await _matching_biotools_id_exists(gh_norm):
        logger.added(f"Using GitHub repo name '{gh_name}' as bio.tools ID")
        return gh_norm

    logger.conflict(
        f"GitHub repo name '{gh_name}' cannot be used as bio.tools ID because it matches an existing entry. "
        "Trying to generate a unique bio.tools ID."
    )

    for suffix in range(1, 100):
        candidate_id = f"{gh_norm}-{suffix}"
        if not await _matching_biotools_id_exists(candidate_id):
            logger.added(f"Using generated bio.tools ID '{candidate_id}'")
            return candidate_id

    logger.note(
        f"Failed to generate unique bio.tools ID based on GitHub repo name '{gh_name}'. "
        "Please set bio.tools ID manually."
    )
    return None
