"""
Utilities for pipelines.
"""

from .assets import svg_to_base64
from .decorators import prepare_match_items
from .file_checks import check_file_with_extension_exists
from .templating import fill_template

__all__ = [
    "prepare_match_items",
    "check_file_with_extension_exists",
    "svg_to_base64",
    "fill_template",
]
