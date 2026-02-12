"""
Docstring for bridge.pipelines.gh2bt_for_meta.map_funcs.functions
"""

from bridge.core.biotools import FunctionItem
from bridge.pipelines.policies.gh2bt import reconcile_gh_ontop_bt


def _extract_functions_from_readme(gh_readme: str) -> set[FunctionItem] | None:
    return None


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
