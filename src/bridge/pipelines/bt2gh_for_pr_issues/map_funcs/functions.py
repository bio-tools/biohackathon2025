"""
Docstring for bridge.pipelines.bt2gh_for_pr_issues.map_funcs.functions
"""

import yaml

from bridge.core.biotools import FunctionItem
from bridge.logging import get_user_logger
from bridge.pipelines.utils import fill_template

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
    Docstring for map_functions
    """
    functions_in_readme = False
    # TODO: check if the functions are actually mentioned in the README
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
    return {"Add function annotations from bio.tools metadata": issue_body}
