"""
Typed chat message model and an LLMProvider protocol.
"""

from typing import Literal, Protocol

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """
    A message in a chat conversation.

    Attributes
    ----------
    role : Literal["system", "user", "assistant"]
        The role of the message sender. One of:
        - "system": Instructions or global context for the LLM assistant.
        - "user": A message from the user.
        - "assistant": A message from the LLM assistant.
    content : str
        The content of the message.
    """

    role: Literal["system", "user", "assistant"]
    content: str


class LLMProvider(Protocol):
    """Protocol for LLM providers that generate chat-based responses."""

    async def generate(self, messages: list[ChatMessage]) -> ChatMessage:
        """Generate a chat-based response from the model."""
        ...
