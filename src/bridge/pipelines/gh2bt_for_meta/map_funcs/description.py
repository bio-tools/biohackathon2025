"""
Mapping functions for description metadata.
"""

from bridge.logging import get_user_logger
from bridge.services import ChatMessage, HuggingFaceProvider

logger = get_user_logger()


async def map_description(gh_description: dict | None, bt_description: str | None) -> str | None:
    """
    Map GitHub description metadata to bio.tools description metadata.
    """
    if gh_description is None:
        logger.unchanged("No GitHub description found, nothing to map.")
        return bt_description

    if gh_description.get("description") is None:
        # if there is no GitHub description, run LLM call on readme, overwrite only when no bt_description'
        if bt_description is None:
            readme = gh_description.get("readme")
            hf_provider = HuggingFaceProvider()
            prompt = (
                f"Based on the following README content, generate a description for a bioinformatics tool. "
                f"Limit your response to 1–2 sentences. "
                f"Do not include any extra commentary or explanation. "
                f"Only output the description itself.\n\n{readme}"
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
                return response.content.strip()[0:999]
            except Exception as e:
                logger.note(f"HuggingFaceProvider call failed: {e}. Returning empty description.")
                return None
        return bt_description
    else:
        # if there is a GitHub description, overwrite the bt_description if it is different
        # check if they are different (ignoring trailing periods and whitespace)
        if (
            bt_description is not None
            and gh_description.get("description").rstrip(". ").strip() == bt_description.rstrip(". ").strip()
        ):
            logger.exact_match("GitHub description matches existing bio.tools description.")
            return bt_description
        elif bt_description is not None:
            logger.conflict("Using GitHub description to overwrite existing bio.tools description.")
        else:
            logger.added("Using GitHub description as no existing bio.tools description.")
        return gh_description.get("description")
