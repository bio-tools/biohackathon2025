"""
Utilities for handling string templating.
"""

import re


def remove_first_snippet_from_text(text: str | None, snippet: str | None) -> str:
    """
    Remove the first occurrence of a snippet from a string.

    This helper searches for the first occurrence of `snippet` in `text` and
    returns a new string with that occurrence removed. All content before and
    after the snippet is preserved. If the snippet is not found, the original
    string is returned unchanged.

    Behaviour:
    - If `text` is ``None`` or an empty string, an empty string is returned.
    - If `snippet` is ``None`` or an empty string, `text` is returned unchanged.
    - Only the first match is removed; subsequent occurrences of `snippet`
      remain untouched.

    Parameters
    ----------
    text : str | None
        The original text from which the snippet should be removed. May be
        ``None``, in which case an empty string is returned.
    snippet : str | None
        The snippet to remove from the text. If ``None`` or empty, no removal
        is performed.

    Returns
    -------
    str
        A new string with the first occurrence of `snippet` removed, or the
        original text (or an empty string) if no removal is performed.
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
    Render a simple string template by substituting named placeholders.

    This function performs lightweight templating by replacing occurrences of
    ``{{ key }}`` in the template with corresponding values from the
    `placeholders` dictionary. Whitespace immediately inside the curly braces
    is ignored, so all of the following forms are supported and treated
    equivalently:

    - ``{{key}}``
    - ``{{ key }}``
    - ``{{    key   }}``

    Substitution is performed for each key in `placeholders` using a regular
    expression that matches the placeholder pattern. Placeholders without a
    corresponding key in the `placeholders` dictionary are left unchanged.

    Parameters
    ----------
    template : str
        The template string containing one or more placeholders of the form
        ``{{ key }}``.
    placeholders : dict[str, str]
        A mapping from placeholder names (without braces) to replacement
        strings. Each key is treated literally (escaped in the underlying
        regular expression).

    Returns
    -------
    str
        The rendered template with all matching placeholders replaced by their
        corresponding values.
    """
    result = template
    for key, value in placeholders.items():
        pattern = re.compile(r"{{\s*" + re.escape(key) + r"\s*}}")
        result = pattern.sub(value, result)
    return result
