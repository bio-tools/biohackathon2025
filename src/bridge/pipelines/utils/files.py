"""
Utility functions for basic file handling.
"""

from pathlib import Path
from typing import Any

import yaml


def check_file_with_extension_exists(in_folder_path: str, file_extension: str) -> bool:
    """
    Check whether a folder contains at least one file with a given extension.

    Parameters
    ----------
    in_folder_path : str
        Path to the folder that should be searched.
    file_extension : str
        File extension to look for, including the leading dot
        (e.g. ``".md"``, ``".json"``).

    Returns
    -------
    bool
        ``True`` if at least one file with the specified extension is found
        anywhere under ``in_folder_path``; ``False`` otherwise.
    """
    import os

    for _, _, files in os.walk(in_folder_path):
        for file in files:
            if file.endswith(file_extension):
                return True
    return False


def get_file_content(file_path: str | Path) -> str | None:
    """
    Read the contents of a text file as UTF-8.

    Parameters
    ----------
    file_path : str | Path
        Path to the file whose contents should be read.

    Returns
    -------
    str | None
        The file contents as a string if the file exists, otherwise ``None``.
    """
    path = Path(file_path)
    if not path.exists():
        return None

    return path.read_text(encoding="utf-8")


def load_dict_from_yaml_file(file_path: str | Path) -> dict[str, Any]:
    """
    Load a YAML file and return its content as a dictionary.

    Parameters
    ----------
    file_path : str | Path
        Path to the YAML file to load.

    Returns
    -------
    dict[str, Any]
        The parsed YAML content as a dictionary, or an empty dictionary
        if the file is missing, empty, invalid, or cannot be parsed.
    """
    content = get_file_content(file_path)
    if content is None:
        return {}

    try:
        data = yaml.safe_load(content)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        # parsing error
        return {}
