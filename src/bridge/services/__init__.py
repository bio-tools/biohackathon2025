"""
Infrastructure layer that handles all interactions with external systems and services:
repository and registry clients, repository operations, and an LLM provider.
"""

from .biotools import BiotoolsIngestor
from .github import GitHubIngestor, GitHubRepoProvider
from .huggingface import HuggingFaceProvider
from .protocols import ChatMessage

__all__ = [
    "GitHubRepoProvider",
    "GitHubIngestor",
    "BiotoolsIngestor",
    "HuggingFaceProvider",
    "ChatMessage",
]
