"""
Utilities for pipelines.
"""

from .assets import svg_to_base64
from .decorators import prepare_match_items
from .file_checks import check_file_with_extension_exists
from .templating import fill_template, remove_first_snippet_from_text
from .urls import canonicalize_shields_url, canonicalize_url

__all__ = [
    "prepare_match_items",
    "check_file_with_extension_exists",
    "svg_to_base64",
    "fill_template",
    "remove_first_snippet_from_text",
    "canonicalize_url",
    "canonicalize_shields_url",
]
