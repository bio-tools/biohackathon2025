"""
Utilities for handling templating in pipelines.
"""


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
        temp_key = "{{" + key + "}}"
        result = result.replace(temp_key, value)
    return result
