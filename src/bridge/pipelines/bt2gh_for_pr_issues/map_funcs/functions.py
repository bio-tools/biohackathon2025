"""
Docstring for bridge.pipelines.bt2gh_for_pr_issues.map_funcs.functions
"""

from bridge.core.biotools import FunctionItem
from bridge.logging import get_user_logger

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


def map_functions(gh_readme: str | None, bt_functions: list[FunctionItem] | None) -> dict[str, str] | None:
    """
    Docstring for map_functions
    """
    functions_in_readme = False
    # TODO: check if the functions are actually mentioned in the README
    if functions_in_readme:
        logger.info("Functions are mentioned in the README, no issue needed.")
        return None

    return None
