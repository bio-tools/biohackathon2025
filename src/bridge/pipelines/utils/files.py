"""
Utility functions for files.
"""

from pathlib import Path


def check_file_with_extension_exists(in_folder_path: str, file_extension: str) -> bool:
    """
    Check if there is at least one file with the given extension in the specified folder.

    Parameters
    ----------
    in_folder_path : str
        The path to the folder to check.
    file_extension : str
        The file extension to look for (e.g., '.md', '.json').

    Returns
    -------
    bool
        True if at least one file with the specified extension exists in the folder, False otherwise.
    """
    import os

    for _, _, files in os.walk(in_folder_path):
        for file in files:
            if file.endswith(file_extension):
                return True
    return False


def get_file_content(file_path: str) -> str | None:
    """
    Read and return the content of a file.

    Parameters
    ----------
    file_path : str
        The path to the file.

    Returns
    -------
    str | None
        The content of the file. None if the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        return None

    return path.read_text(encoding="utf-8")
