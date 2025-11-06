"""
Functions for mapping bio.tools function items (operation, input, output) to GitHub
"""

from bridge.core.biotools import FunctionItem


def _flatten_function(function: list[FunctionItem]) -> list[str]:
    """
    Flatten bio.tools function annotations for operation, input, and output.

    Terms may contain spaces. Those spaces are replaced by hyphens.
    This will allow copy/pasting the terms into GitHub and ensure that
    multi-word terms are not recognized as separate topics but as one.

    Relevant terms:
    - function[].operation[].term
    - function[].input[].data.term
    - function[].input[].format[].term
    - function[].output[].data.term
    - function[].output[].format[].term

    Parameters
    ----------
    function : list[FunctionItem]
        List of bio.tools function annotations using EDAM ontology

    Returns
    -------
    list
        Flattened list of EDAM terms
    """
    function_flat = []
    # extract all EDAM terms
    for fnc_item in function:
        for op_item in fnc_item.operation:
            function_flat += [op_item.term]
        for io_item in fnc_item.input + fnc_item.output:
            function_flat += [io_item.data.term]
            for form_item in io_item.format:
                function_flat += [form_item.term]

    # replace all spaces with hyphens
    function_flat = [term.replace(" ", "-").lower() for term in function_flat]

    return function_flat


def map_function2topics(gh_topics: list[str] | None, bt_function: list[FunctionItem] | None) -> dict[str, str] | None:
    """
    Map bio.tools function items to GitHub topics.

    Returns
    -------
    dict[str, str] | None
        A dictionary with issue title as key and issue body as value, or None if no issue is needed.
    """
    if bt_function is None:
        # no function annotations in bio.tools
        return None

    edam_terms = _flatten_function(bt_function)
    terms_missing = set(edam_terms).difference(set(gh_topics))
    if not terms_missing:
        # no bio.tools function annotations missing in GitHub topics
        return None

    num_missing = len(terms_missing)
    terms = " ".join(sorted(terms_missing))

    # adjust message based on singular/plural
    noun, verb, pronoun = ("term", "is", "it") if num_missing == 1 else ("terms", "are", "them")

    return {
        "Add function annotations from bio.tools metadata": (
            f"The bio.tools function annotations contain {num_missing} EDAM {noun} "
            f"that {verb} not included in the GitHub topics: \n\n{terms}\n\n"
            f"Please consider adding {pronoun} to the GitHub repository."
        )
    }


# TODO: add function for mapping to GitHub content (README) resulting in pull request. Compare citation.py
# def map_function2readme():
