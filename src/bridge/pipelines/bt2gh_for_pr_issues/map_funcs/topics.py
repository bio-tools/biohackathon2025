"""
Functions for mapping bio.tools EDAM annotations to GitHub topics.

This module inspects EDAM-based annotations from bio.tools (topics and
function-level operation/input/output terms) and compares them to the
existing set of GitHub topics for a repository. When one or more EDAM
terms are missing from the GitHub topics, it proposes a GitHub issue
suggesting that these terms be added as topics, using a generic
bio.tools-on-top-of-GitHub additive policy.
"""

import re

from bridge.core.biotools import FunctionItem, TopicItem
from bridge.logging import get_user_logger
from bridge.pipelines.policies.bt2gh import reconcile_bt_ontop_gh

logger = get_user_logger()


def _normalize_edam_term(term: str) -> str:
    """
    Normalize an EDAM term by replacing spaces with hyphens and converting to lowercase.

    This makes EDAM terms suitable for use as GitHub topics and ensures
    that multi-word terms are treated as a single topic. Non-alphanumeric
    characters (except hyphens) are stripped to comply with GitHub topic rules.

    Parameters
    ----------
    term : str
        The EDAM term to normalize.

    Returns
    -------
    str
        The normalized EDAM term.
    """
    # Replace spaces with hyphens and lowercase
    normalized = term.replace(" ", "-").lower()
    # Replace any non-alphanumeric/hyphen chars with hyphens
    normalized = re.sub(r"[^a-z0-9-]", "-", normalized)
    # Collapse multiple consecutive hyphens and strip leading/trailing hyphens
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized


def _normalize_gh_topic(gh_topic: str) -> str:
    """
    Normalize a GitHub topic by converting to lowercase.

    Parameters
    ----------
    gh_topic : str
        The GitHub topic to normalize.

    Returns
    -------
    str
        The normalized GitHub topic.
    """
    return gh_topic.lower()


def _flatten_function(function: list[FunctionItem]) -> list[str]:
    """
    Flatten bio.tools function annotations for operation, input, and output.

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
        List of bio.tools function annotations using EDAM ontology.

    Returns
    -------
    list[str]
        Flattened list of EDAM terms strings.
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

    return function_flat


def map_topics(gh_topics: list[str] | None, bt_edam: dict[str, any] | None) -> dict[str, str] | None:
    """
    Propose a GitHub issue to add missing EDAM-based topics from bio.tools.

    This function inspects EDAM annotations from bio.tools (both high-level
    topics and function-level operation/input/output terms), normalizes them
    to GitHub-topic-style slugs, and compares them against the normalized
    set of existing GitHub topics. It then applies the generic
    bio.tools-on-top-of-GitHub additive policy to decide whether an issue
    should be proposed and which EDAM terms to include.

    Parameters
    ----------
    gh_topics : list[str] | None
        Current list of GitHub topics for the repository, or ``None`` if
        no topics are set.
    bt_edam : dict[str, Any] | None
        EDAM-related metadata from bio.tools.
        Expected keys include:
        - "topics"    : list[TopicItem]
        - "functions" : list[FunctionItem]

    Returns
    -------
    dict[str, str] | None
        A mapping with the issue title as key and the issue body as value,
        or ``None`` if no issue is needed under the policy.
    """
    if bt_edam is None:
        logger.unchanged("No bio.tools EDAM annotations found, nothing to map")
        return None

    topic_items: list[TopicItem] = bt_edam.get("topics") or []
    function_items: list[FunctionItem] = bt_edam.get("functions") or []

    topic_terms = [_normalize_edam_term(ti.term) for ti in topic_items if ti.term]
    function_terms = [_normalize_edam_term(term) for term in _flatten_function(function_items)]

    bt_terms = set(topic_terms + function_terms)
    gh_terms = {_normalize_gh_topic(t) for t in gh_topics or []}

    def make_issue(missing: set[str]) -> dict[str, str]:
        num_missing = len(missing)
        terms = "\n".join(sorted(missing))

        # adjust message based on singular/plural
        noun, verb, pronoun = ("term", "is", "it") if num_missing == 1 else ("terms", "are", "them")

        # Construct the JSON payload for the API
        names_json = ",".join(f'"{term}"' for term in sorted(missing))

        return {
            "Add EDAM annotations from bio.tools metadata": (
                f"The bio.tools EDAM annotations contain {num_missing} EDAM {noun} "
                f"that {verb} not included in the GitHub topics:\n\n{terms}\n\n"
                f"Please consider adding {pronoun} to the GitHub repository.\n\n"
                f"We recommend one of the following methods:\n\n"
                f"1. _Use the GitHub CLI (one --add-topic flag per term):_\n"
                f"```\n"
                f"gh repo edit <OWNER/REPO> " + " ".join(f"--add-topic {term}" for term in sorted(missing)) + "\n"
                f"```\n\n"
                f"2. _Use the GitHub API via curl (requires token):_\n"
                f"```\n"
                f"curl -L -X PUT \\\n"
                f"  -H 'Accept: application/vnd.github+json' \\\n"
                f"  -H 'Authorization: Bearer <YOUR-TOKEN>' \\\n"
                f"  -H 'X-GitHub-Api-Version: 2022-11-28' \\\n"
                f"  https://api.github.com/repos/OWNER/REPO/topics \\\n"
                f"  -d '{{\"names\": [{names_json}]}}'\n"
                f"```\n\n"
                f"3. _Visit the GitHub web UI:_\n"
                f"You can also add topics manually via the repository settings:\n"
                f"https://github.com/OWNER/REPO/settings\n\n"
                f"Please replace `<OWNER/REPO>` and `<YOUR-TOKEN>` with the appropriate values."
            )
        }

    return reconcile_bt_ontop_gh(
        gh_norm=gh_terms,
        bt_norm=bt_terms,
        make_output=make_issue,
        log_label="EDAM terms",
    )


# TODO: add function for mapping to GitHub content (README) resulting in pull request. Compare citation.py
# def map_function2readme():
