"""
Docstring for bridge.pipelines.gh2bt_for_meta.map_funcs.functions
"""

import yaml

from bridge.core.biotools import FunctionItem
from bridge.logging import get_user_logger
from bridge.pipelines.policies.gh2bt import reconcile_gh_ontop_bt
from bridge.pipelines.shared.functions import find_match_yamls

logger = get_user_logger()


def _extract_functions_from_readme(gh_readme: str | None) -> set[FunctionItem] | None:
    yamls = find_match_yamls(gh_readme)
    # Parse YAMLs into FunctionItems
    functions = set()
    for yaml_str in yamls:
        try:
            data = yaml.safe_load(yaml_str)
            if isinstance(data, dict):
                function_item = FunctionItem.from_dict(data)
                functions.add(function_item)
            else:
                logger.warning("YAML block is not a dictionary, skipping: %s", yaml_str)
        except yaml.YAMLError as e:
            logger.warning("Failed to parse YAML block, skipping: %s\nError: %s", yaml_str, e)
    return functions if functions else None


def map_functions(gh_readme: str | None, bt_functions: list[FunctionItem] | None) -> list[FunctionItem] | None:
    """
    Docstring for map_functions
    """
    return reconcile_gh_ontop_bt(
        gh_norm=gh_readme,
        bt_norm=set(bt_functions) if bt_functions is not None else None,
        bt_value=bt_functions,
        build_bt_from_gh=_extract_functions_from_readme,
        build_bt_from_norm=lambda bt_norm: set(bt_norm) if bt_norm is not None else None,
        log_label="functions",
    )
