"""
Functions for mapping bio.tools function and topic EDAM annotation terms (topic, operation, input, output) to GitHub
"""

from bridge.core.biotools import FunctionItem, TopicItem
from bridge.logging import get_user_logger

logger = get_user_logger()


def _flatten_function(function: list[FunctionItem] | None) -> list[str]:
    """
    Flatten bio.tools topic annototions and function annotations for operation, input, and output.

    Terms may contain spaces. Those spaces are replaced by hyphens.
    This will allow copy/pasting the terms into GitHub and ensure that
    multi-word terms are not recognized as separate topics but as one.

    Relevant terms:
    - topic[].term
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
    if not function:
        return []

    function_flat = []
    # extract all EDAM terms
    for fnc_item in function:

        for op_item in fnc_item.operation or []:
            if op_item.term:
                function_flat.append(op_item.term)

        io_items = (fnc_item.input or []) + (fnc_item.output or [])
        for io_item in io_items:

            if io_item.data and io_item.data.term:
                function_flat.append(io_item.data.term)

            for form_item in io_item.format or []:
                if form_item.term:
                    function_flat.append(form_item.term)

    # replace all spaces with hyphens
    function_flat = [term.replace(" ", "-").lower() for term in function_flat]

    return function_flat


def map_edam2topics(gh_topics: list[str] | None, bt_edam: dict[str, any] | None) -> dict[str, str] | None:
    """
    Map bio.tools edam items to GitHub topics.

    Returns
    -------
    dict[str, str] | None
        A dictionary with issue title as key and issue body as value, or None if no issue is needed.
    """
    if bt_edam is None:
        logger.unchanged("No bio.tools EDAM annotations found, nothing to map.")
        return None

    topic_terms: list[TopicItem] = bt_edam.get("topics") or []
    # get only each term for topic items
    topic_terms = [ti.term.replace(" ", "-").lower() for ti in topic_terms if ti.term]
    function_terms = _flatten_function(bt_edam.get("functions") or [])
    edam_terms = topic_terms + function_terms

    if not edam_terms:
        # no function annotations in bio.tools
        return None

    if gh_topics is None:
        gh_topics = []
    terms_missing = set(edam_terms).difference(set(gh_topics))
    if not terms_missing:
        # no bio.tools function annotations missing in GitHub topics
        return None

    num_missing = len(terms_missing)
    terms = " ".join(sorted(terms_missing))

    # adjust message based on singular/plural
    noun, verb, pronoun = ("term", "is", "it") if num_missing == 1 else ("terms", "are", "them")

    logger.added(f"{num_missing} EDAM {noun} to GitHub topics: {terms}")

    return {
        "Add edam annotations from bio.tools metadata": (
            f"The bio.tools edam annotations contain {num_missing} EDAM {noun} "
            f"that {verb} not included in the GitHub topics: \n\n{terms}\n\n"
            f"Please consider adding {pronoun} to the GitHub repository."
        )
    }


# TODO: add function for mapping to GitHub content (README) resulting in pull request. Compare citation.py
# def map_function2readme():
