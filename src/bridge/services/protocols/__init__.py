"""
Protocols and base classes for services.
"""

from .ingestor import Ingestor
from .llm_provider import ChatMessage, LLMProvider
from .repo_provider import ForkInfo, RepoProvider

__all__ = [
    "Ingestor",
    "RepoProvider",
    "ForkInfo",
    "LLMProvider",
    "ChatMessage",
]
