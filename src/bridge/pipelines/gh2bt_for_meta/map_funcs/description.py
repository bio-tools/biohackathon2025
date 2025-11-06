"""
Mapping functions for description metadata.
"""
import logging
from bridge.services import HuggingFaceProvider, ChatMessage

logger = logging.getLogger(__name__)


async def map_description(gh_description: dict | None, bt_description: str | None) -> str | None:
    """
    Map GitHub description metadata to bio.tools description metadata.
    """
    if gh_description.get("description") is None:
        # if there is no GitHub description, run LLM call on readme, overwrite only when no bt_description'
        if bt_description is None:
            hf_provider = HuggingFaceProvider()
            prompt = f"Generate a concise 1-2 sentence description for a bioinformatics tool based on the following README content:\n\n{gh_description.get('readme')}\n\nDescription:"
            message_sys = ChatMessage(
                role="system",
                content="You are an expert in bioinformatics tool documentation. Generate concise, clear descriptions for tools based on their README content."
            )
            message_user = ChatMessage(
                role="user",
                content=prompt,
            )
            try:
                response = await hf_provider.generate([message_sys, message_user])
                logging.info("ADDED: No GitHub description and no existing bio.tools description; using readme to generate description.")
                return response.content.strip()[1:100]
            except Exception as e:
                logging.warning(f"HuggingFaceProvider call failed: {e}. Returning empty description.")
                return None
        return bt_description
    else:
        # if there is a GitHub description, overwrite the bt_description if it is different
        # check if they are different (ignoring trailing periods and whitespace)
        if bt_description is not None and gh_description.get("description").rstrip(". ").strip() == bt_description.rstrip(". ").strip():
            logging.info("EXACT MATCH: GitHub description matches existing bio.tools description.")
            return bt_description
        else:
            logging.info("CONFLICT: Using GitHub description to overwrite existing bio.tools description.")
            return gh_description.get("description")
