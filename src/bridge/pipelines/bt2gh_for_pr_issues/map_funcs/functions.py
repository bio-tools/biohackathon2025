"""
Map function annotations from bio.tools to GitHub.

This module compares the function annotations recorded in bio.tools with the
GitHub README and, when appropriate, proposes a GitHub issue suggesting that
the bio.tools function annotations be added to the README.
"""

import re

import yaml

from bridge.core.biotools import FunctionItem
from bridge.logging import get_user_logger
from bridge.pipelines.utils import fill_template, separate_snippets_from_text

logger = get_user_logger()

FUNCTION_TEMPLATE = """
<details>
<summary>{{ FUNCTION_NAME }}</summary>

```yaml
# biotools-function
{{ FUNCTION_YAML}}
```

</details>
"""
FUNCTION_PATTERN = re.compile(
    r"""
    <details>\s*
    <summary>(?P<name>.*?)</summary>\s*
    ```yaml\s*
    #\s*biotools-function\s*
    (?P<yaml>.*?)
    ```\s*
    </details>
    """,
    re.DOTALL | re.VERBOSE,
)


def _function_to_yaml(function: FunctionItem) -> str:
    """
    Convert a FunctionItem to a YAML string.

    Parameters
    ----------
    function : FunctionItem
        The FunctionItem to convert.

    Returns
    -------
    str
        The YAML string representation of the FunctionItem.
    """
    data = function.model_dump(exclude_none=True)
    return yaml.safe_dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )


def _build_function_name(function: FunctionItem) -> str:
    """
    Build a function name out of the function's operations.

    Parameters
    ----------
    function : FunctionItem
        The FunctionItem to build the name from.

    Returns
    -------
    str
        The built function name.
    """
    operations = function.operation  # min 1
    operations_str = ", ".join(op.term for op in operations)
    return operations_str


def _build_function(function: FunctionItem) -> str:
    """
    Build a function string by converting the FunctionItem to YAML and filling the FUNCTION_TEMPLATE.

    Parameters
    ----------
    function : FunctionItem
        The function item to build.

    Returns
    -------
    str
        The built function string.
    """
    function_yaml = _function_to_yaml(function)
    function_name = _build_function_name(function)
    filling = {
        "FUNCTION_NAME": function_name,
        "FUNCTION_YAML": function_yaml,
    }
    return fill_template(FUNCTION_TEMPLATE, filling)


def _build_functions(functions: list[FunctionItem]) -> str:
    """
    Build a string for all functions by concatenating the built function strings.

    Parameters
    ----------
    functions : list[FunctionItem]
        The list of FunctionItems to build.

    Returns
    -------
    str
        The concatenated function strings.
    """
    txt = "#Functions\n\n"
    return txt + "\n".join(_build_function(function) for function in functions)


def map_functions(gh_readme: str | None, bt_functions: list[FunctionItem] | None) -> dict[str, str] | None:
    """
    Propose a GitHub issue to add function annotations based on bio.tools metadata.

    Steps performed:
    1. Check if the README already mentions functions using the FUNCTION_PATTERN.
       If it does, no issue is needed.
    2. If no functions are found in bio.tools, no issue is needed.
    3. If functions are present in bio.tools but not mentioned in the README, build
         a function string for each function and propose an issue to add them to the README.

    Parameters
    ----------
    gh_readme : str | None
        The current README content from GitHub, or ``None`` if the file does
        not exist yet.
    bt_functions : list[FunctionItem] | None
        The list of FunctionItems from bio.tools metadata, or ``None`` if no functions are defined.

    Returns
    -------
    dict[str, str] | None
        A dictionary with the issue title as key and the issue body as value,
        or ``None`` if no issue is to be created.
    """
    matches = list(FUNCTION_PATTERN.finditer(gh_readme or ""))
    functions_in_readme = len(matches) > 0
    if functions_in_readme:
        logger.info("Functions are mentioned in the README, no issue needed.")
        return None

    if not bt_functions:
        logger.info("No functions found in biotools, no issue needed.")
        return None

    functions_txt = _build_functions(bt_functions)
    issue_body = (
        "The bio.tools metadata contains the following function annotations, "
        "but they are not mentioned in the GitHub README:\n"
        "Please consider adding these functions to the README to improve discoverability "
        "and provide users with more information about the tool's capabilities.\n\n"
        f"{functions_txt}"
    )
    logger.added("bio.tools function annotations added to issue.")
    return {"Add function annotations from bio.tools metadata": issue_body}


def map_functions_to_readme(gh_readme: str | None, bt_functions: list[FunctionItem] | None) -> str | None:
    """
    Propose an updated README content by adding function annotations from bio.tools metadata.

    Steps performed:
    1. Check if README exists; if not, no update is needed.
    2. Check if the README already mentions functions using the FUNCTION_PATTERN.
       If it does not, no update is needed.
    3. If no functions are found in bio.tools, no update is needed.
    4. If functions are present in bio.tools and the README mentions functions,
         remove all existing function blocks from the README.
    5. In their place, add new function blocks for each function from bio.tools.
        The new function blocks are built using the FUNCTION_TEMPLATE and the
        function data from bio.tools.

    Parameters
    ----------
    gh_readme : str | None
        The current README content from GitHub, or ``None`` if the file does
        not exist yet.
    bt_functions : list[FunctionItem] | None
        The list of FunctionItems from bio.tools metadata, or ``None`` if no functions are defined.

    Returns
    -------
    str | None
        The updated README content with function annotations added,
        or the original README content if no update is needed.
    """
    if gh_readme is None:
        logger.info("README does not exist, no need to map functions.")
        return gh_readme

    matches = list(FUNCTION_PATTERN.finditer(gh_readme or ""))
    functions_in_readme = len(matches) > 0
    if not functions_in_readme:
        logger.info("Functions are not mentioned in the README, no PR needed.")
        return gh_readme

    if not bt_functions:
        logger.info("No functions found in biotools, no need to include any in README.")
        return gh_readme

    matches_blocks = [m.group(0) for m in matches]
    before, after = separate_snippets_from_text(gh_readme, matches_blocks)
    functions_txt = _build_functions(bt_functions)
    new_readme = before + functions_txt + after
    logger.added("bio.tools function annotations added to README content.")
    return new_readme
