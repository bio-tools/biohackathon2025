"""
Bootstrap utilities that register schemas, repositories, pipelines, and handlers into process-local registries,
plus lookup helpers used by handlers at runtime.
"""

from .base import get_handler, get_pipeline, get_repo_components, get_schema_composer
from .register_handler import register_handler

__all__ = [
    "get_schema_composer",
    "get_repo_components",
    "get_pipeline",
    "get_handler",
    "register_handler",
]
