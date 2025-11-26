"""
Utilities for handling asset files in pipelines.
"""

import base64


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
    if not svg_path.exists():
        raise FileNotFoundError(f"SVG file not found: {svg_path}")

    with open(svg_path, "rb") as svg_file:
        svg_content = svg_file.read_bytes()
    encoded_svg = base64.b64encode(svg_content).decode("ascii")
    return encoded_svg
