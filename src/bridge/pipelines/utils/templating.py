"""
Utilities for handling templating in pipelines.
"""

import re


def remove_first_snippet_from_text(text: str | None, snippet: str | None) -> str:
    """
    Remove the first occurrence of `snippet` from `text`.
    If snippet is None or not found, return text unchanged.

    Parameters
    ----------
    text : str | None
        The original text.
    snippet : str | None
        The snippet to remove.
    """
    if not text:
        return ""

    if not snippet:
        return text

    idx = text.find(snippet)
    if idx == -1:
        return text

    return text[:idx] + text[idx + len(snippet) :]


def fill_template(template: str, placeholders: dict[str, str]) -> str:
    """
    Fill in a template string with provided placeholder values.

    Parameters
    ----------
    template : str
        The template string containing placeholders.
    placeholders : dict[str, str]
        A dictionary mapping placeholder keys to their replacement values.

    Returns
    -------
    str
        The template string with placeholders replaced by their corresponding values.
    """
    result = template
    for key, value in placeholders.items():
        pattern = re.compile(r"{{\s*" + re.escape(key) + r"\s*}}")
        result = pattern.sub(value, result)
    return result
