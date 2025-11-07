"""
LLM provider wrapping huggingface_hub’s InferenceClient for chat-style text generation used by pipelines.
"""

import asyncio
import logging
from typing import Literal

from huggingface_hub import InferenceClient

from bridge.config import settings
from bridge.services.protocols import ChatMessage, LLMProvider

logger = logging.getLogger(__name__)

# Type for Hugging Face inference providers.
type HF_Provider = Literal[
    "black-forest-labs",
    "cerebras",
    "clarifai",
    "cohere",
    "fal-ai",
    "featherless-ai",
    "fireworks-ai",
    "groq",
    "hf-inference",
    "hyperbolic",
    "nebius",
    "novita",
    "nscale",
    "openai",
    "publicai",
    "replicate",
    "sambanova",
    "scaleway",
    "together",
    "zai-org",
    "auto",
] | None


class HuggingFaceProvider(LLMProvider):
    """
    Hugging Face provider for chat-capable models using InferenceClient.
    Supports models compatible with the chat.completions API.

    Parameters
    ----------
    model : str
        The Hugging Face model identifier to use for chat generation.
        Default is "Qwen/Qwen3-8B" (https://huggingface.co/Qwen/Qwen2.5-7B).
    provider : HF_Provider
        The inference provider to use. Default is "featherless-ai".
    """

    def __init__(self, model: str = "Qwen/Qwen3-8B", provider: HF_Provider = "featherless-ai"):
        settings.require_huggingface_token()

        self.model = model
        self._client = InferenceClient(provider=provider, model=model, token=settings.huggingface_token)

    async def generate(self, messages: list[ChatMessage], **kwargs) -> ChatMessage:
        """
        Generate a chat-based response from the model.

        Parameters
        ----------
        messages : list[ChatMessage]
            A list of chat messages forming the conversation history.
        **kwargs
            Additional generation parameters such as `max_new_tokens` and `temperature`.

        Returns
        -------
        ChatMessage
            The generated chat message (response) from the model.

        Raises
        ------
        ValueError
            If `messages` is empty.
        RuntimeError
            If the model response is missing required fields.
        Exception
            For any other errors during generation.
        """
        if not messages:
            raise ValueError("`messages` cannot be empty — provide a chat-style message list.")

        try:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self.model,
                messages=[m.model_dump() for m in messages],
                max_tokens=kwargs.get("max_new_tokens", 500),
                temperature=kwargs.get("temperature", 0.7),
            )

            message = response.choices[0].message
            role = getattr(message, "role", None)
            content = getattr(message, "content", None)
            if not role:
                raise RuntimeError("Response from model missing 'role' field.")
            if not content:
                raise RuntimeError("Empty response received from model.")

            return ChatMessage(role=role, content=content)

        except Exception as e:
            logger.error(f"Chat generation failed for model '{self.model}': {e}")
            raise
