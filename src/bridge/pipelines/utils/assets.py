"""
Utilities for handling asset files in pipelines.
"""

import base64
from pathlib import Path


def svg_to_base64(svg_path: str) -> str:
    """
    Convert an SVG file to a base64-encoded string.

    Parameters
    ----------
    svg_path : str
        Path to the SVG file.

    Returns
    -------
    str
        Base64-encoded string of the SVG content.

    Raises
    ------
    FileNotFoundError
        If the SVG file does not exist.
    """
    svg_path = Path(svg_path)
    if not svg_path.exists():
        raise FileNotFoundError(f"SVG file not found: {svg_path}")

    svg_content = svg_path.read_bytes()
    encoded_svg = base64.b64encode(svg_content).decode("ascii").replace("\n", "")
    return encoded_svg
