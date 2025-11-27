"""
Utilities for pipelines.
"""

from .badges import Badge, compose_badge
from .decorators import prepare_match_items
from .file_checks import check_file_with_extension_exists
from .templating import fill_template, remove_first_snippet_from_text

__all__ = [
    "prepare_match_items",
    "check_file_with_extension_exists",
    "Badge",
    "compose_badge",
    "fill_template",
    "remove_first_snippet_from_text",
]
