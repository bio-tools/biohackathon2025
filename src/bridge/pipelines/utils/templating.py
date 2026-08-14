"""
Utilities for handling string templating.
"""

import re


def separate_snippet_from_text(text: str | None, snippet: str | None) -> tuple[str, str]:
    """
    Separate the first occurrence of a snippet from a string.

    This helper searches for the first occurrence of `snippet` in `text` and
    returns a tuple containing the content before and after that occurrence.
    If the snippet is not found, the original text is returned as the "before"
    part and the "after" part is an empty string.

    Parameters
    ----------
    text : str | None
        The original text from which the snippet should be separated. May be
        ``None``, in which case both returned parts will be empty strings.
    snippet : str | None
        The snippet to separate from the text. If ``None`` or empty, no separation
        is performed and the entire text is returned as the "before" part.

    Returns
    -------
    tuple[str, str]
        A tuple containing the "before" and "after" parts of the text relative to
        the first occurrence of the snippet. If the snippet is not found, the first
        element is the original text (or an empty string if `text` is ``None``) and
        the second element is an empty string.
    """
    if not text:
        return "", ""

    if not snippet:
        return text, ""

    idx = text.find(snippet)
    if idx == -1:
        return text, ""

    before = text[:idx]
    after = text[idx + len(snippet) :]
    return before, after


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
    before, after = separate_snippet_from_text(text, snippet)

    return before + after


def separate_snippets_from_text(text: str | None, snippets: list[str]) -> tuple[str, str]:
    """
    Separate the first occurrence of a list of snippets from a string.
    Then remove the remaining snippets from the "after" part.

    This helper searches for the first occurrence of any snippet in `snippets`
    within `text` and separates the text into "before" and "after" parts based
    on that first match. It then removes all subsequent occurrences of any of the
    snippets from the "after" part. If no snippets are found, the original text is
    returned as the "before" part and the "after" part is an empty string.

    Parameters
    ----------
    text : str | None
        The original text from which the snippets should be separated. May be
        ``None``, in which case both returned parts will be empty strings.
    snippets : list[str]
        A list of snippets to search for and separate from the text. If the list is
        empty, no separation is performed and the entire text is returned as the "before" part.

    Returns
    -------
    tuple[str, str]
        A tuple containing the "before" and "after" parts of the text relative to
        the first occurrence of any snippet. The "after" part has all subsequent
        occurrences of any snippets removed. If no snippets are found, the first
        element is the original text (or an empty string if `text` is ``None``)
        and the second element is an empty string.
    """
    first_snippet = snippets[0] if snippets else None
    before, after = separate_snippet_from_text(text, first_snippet)

    if len(snippets) <= 1:
        return before, after

    remaining_snippets = snippets[1:]
    for snippet in remaining_snippets:
        after = remove_first_snippet_from_text(after, snippet)

    return before, after


def fill_template(template: str, placeholders: dict[str, str]) -> str:
    r"""
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

    Replacement values are inserted literally: backslash sequences such as
    ``\\1``, ``\\g<0>`` or ``\\masses.txt`` are *not* interpreted as regular
    expression replacement escapes.

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
        result = pattern.sub(lambda _match, value=value: value, result)
    return result
