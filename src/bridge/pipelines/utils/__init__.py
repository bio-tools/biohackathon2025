"""
Utilities for pipelines.
"""

from .badges import Badge, compose_badge
from .cleaning import (
    canonicalize_shields_url,
    canonicalize_url,
    escape_shields_part,
    normalize_color,
    normalize_dict_strings,
    normalize_pydantic_model_strings,
    normalize_text,
)
from .conversions import object_to_primitive, svg_to_base64
from .decorators import prepare_match_items
from .files import check_file_with_extension_exists, get_file_content, load_dict_from_yaml_file
from .templating import fill_template, remove_first_snippet_from_text

__all__ = [
    "prepare_match_items",
    "check_file_with_extension_exists",
    "get_file_content",
    "load_dict_from_yaml_file",
    "Badge",
    "compose_badge",
    "canonicalize_shields_url",
    "canonicalize_url",
    "escape_shields_part",
    "normalize_color",
    "normalize_text",
    "normalize_dict_strings",
    "normalize_pydantic_model_strings",
    "fill_template",
    "remove_first_snippet_from_text",
    "svg_to_base64",
    "object_to_primitive",
]
