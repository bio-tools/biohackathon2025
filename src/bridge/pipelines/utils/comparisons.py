"""
Utility functions for comparisons.
"""


def str_contain_each_other(str1: str, str2: str) -> bool:
    """
    Check if two strings contain each other (case-insensitive).

    Parameters
    ----------
    str1 : str
        First string.
    str2 : str
        Second string.

    Returns
    -------
    bool
        True if either string contains the other, False otherwise.
    """
    str1_lower = str1.lower()
    str2_lower = str2.lower()
    return str1_lower in str2_lower or str2_lower in str1_lower
