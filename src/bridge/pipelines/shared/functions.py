"""
Shared functions utilities for pipelines.
"""

import re

FUNCTION_PATTERN = re.compile(
    r"""
    <details>\s*
    <summary>(?P<name>[^\r\n<]*)</summary>\s*
    ```yaml[ \t]*\r?\n
    #[ \t]*biotools-function[ \t]*\r?\n
    (?P<yaml>.*?)
    ^[ \t]*```[ \t]*\r?\n
    \s*</details>
    """,
    re.DOTALL | re.VERBOSE | re.MULTILINE,
)


def find_matches(text: str | None) -> list[str]:
    """
    Find all function annotations in the given text.

    Parameters
    ----------
    text : str
        The text to search for function annotations.

    Returns
    -------
    list[FunctionItem]
        A list of FunctionItems found in the text.
    """
    matches = list(FUNCTION_PATTERN.finditer(text or ""))
    return matches


def find_match_yamls(text: str | None) -> list[str]:
    """
    Find all function annotation YAML blocks in the given text.

    Parameters
    ----------
    text : str
        The text to search for function annotations.

    Returns
    -------
    list[str]
        A list of YAML strings found in the function annotations in the text.
    """
    matches = find_matches(text)
    yamls = [m.group("yaml") for m in matches]
    return yamls
