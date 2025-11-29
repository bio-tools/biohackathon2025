"""
Mapping functions for description metadata.

This module reconciles textual tool descriptions between GitHub and
bio.tools. GitHub descriptions are treated as authoritative when present.
If GitHub provides no description and bio.tools is empty, a short description
is generated from the README using an LLM.
"""

from bridge.logging import get_user_logger
from bridge.pipelines.utils import normalize_text
from bridge.services import ChatMessage, HuggingFaceProvider

logger = get_user_logger()

MAX_README_CHARS = 10000


async def map_description(gh_params: dict | None, bt_description: str | None) -> str | None:
    """
    Map and reconcile GitHub description metadata and bio.tools description metadata.

    Policy:
    1. If GitHub provides no metadata, the existing bio.tools description
       is preserved.
    2. If GitHub provides a description:
       - If it is effectively identical to the bio.tools description
         (ignoring trailing punctuation and whitespace), no change is made.
       - Otherwise, the GitHub description overwrites the bio.tools value.
    3. If GitHub provides no description and bio.tools is empty:
       - If a README is available, a short description is generated from
         the README using an LLM and normalized before storage.
       - If no README is available, no description is set.
    4. LLM failures never overwrite existing bio.tools descriptions.

    Parameters
    ----------
    gh_params : dict | None
        GitHub metadata dictionary.
        Expected keys include:
        - ``"description"`` : Repository description string (optional)
        - ``"readme"``      : README contents used for LLM-based description generation
    bt_description : str | None
        Existing bio.tools description, or ``None`` if unset.

    Returns
    -------
    str | None
        The reconciled bio.tools description, or ``None`` if no description
        could be determined.
    """
    if gh_params is None:
        logger.unchanged("No GitHub description found, nothing to map.")
        return bt_description

    gh_description = normalize_text(gh_params.get("description"))

    if gh_description is None:
        # if there is no GitHub description, run LLM call on readme, overwrite only when no bt_description'
        if bt_description is None:
            readme = gh_params.get("readme")
            if readme is None:
                logger.unchanged("No GitHub description and no readme found, nothing to map.")
                return None

            hf_provider = HuggingFaceProvider()
            prompt = (
                f"Based on the following README content, generate a description for a bioinformatics tool. "
                f"Limit your response to 1–2 sentences. "
                f"Do not include any extra commentary or explanation. "
                f"Only output the description itself.\n\n{readme.strip()[:MAX_README_CHARS]}",
            )
            message_sys = ChatMessage(
                role="system",
                content=(
                    "You are an expert in bioinformatics tool documentation. "
                    "Your task is to generate a concise, clear, and short description for a software tool. "
                    "Limit your response to 1–2 sentences. "
                    "Do not include any explanation, reasoning, or commentary. "
                    "Only output the description itself."
                    "/nothink"
                ),
            )
            message_user = ChatMessage(
                role="user",
                content=prompt,
            )
            try:
                response = await hf_provider.generate([message_sys, message_user])
                logger.added(
                    "No GitHub description and no existing bio.tools description; using "
                    "readme to generate description."
                )
                return normalize_text(response.content).strip()[0:999]
            except Exception as e:
                logger.note(f"HuggingFaceProvider call failed: {e}. Returning empty description.")
                return None
        return bt_description
    else:
        # if there is a GitHub description, overwrite the bt_description if it is different
        # check if they are different (ignoring trailing periods and whitespace)
        if (
            bt_description is not None
            and gh_description.rstrip(". ").strip() == normalize_text(bt_description).rstrip(". ").strip()
        ):
            logger.exact_match("GitHub description matches existing bio.tools description.")
            return bt_description
        elif bt_description is not None:
            logger.conflict("Using GitHub description to overwrite existing bio.tools description.")
        else:
            logger.added("Using GitHub description as no existing bio.tools description.")
        return gh_description
