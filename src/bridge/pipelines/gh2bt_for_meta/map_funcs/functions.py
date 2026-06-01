"""
Map function annotations from GitHub to bio.tools.

This modules reconciles the function annotations recorded in the GitHub README and
existing bio.tools metadata, and produces a reconciled list of `FunctionItem` instances
to be included in the bio.tools metadata. The reconciliation is performed using the
generic bio.tools-on-top-of-GitHub policy, which preserves existing bio.tools annotations
unless the GitHub README contains explicit function annotations that differ from bio.tools,
in which case the GitHub annotations are added on top of the existing bio.tools ones.
"""

import json
from typing import Any

import yaml

from bridge.core.biotools import FunctionItem
from bridge.logging import get_user_logger
from bridge.pipelines.policies.gh2bt import reconcile_gh_ontop_bt
from bridge.pipelines.shared.functions import find_match_yamls
from bridge.pipelines.utils import normalize_dict_strings, object_to_primitive

logger = get_user_logger()


def _stable_json(x: Any) -> str:
    """
    Convert a Python object to a JSON string with stable key ordering and compact formatting.
    This is useful for creating consistent string representations of
    complex objects (e.g., functions) for hashing or comparison.

    Parameters
    ----------
    x : Any
        The Python object to convert to a stable JSON string.

    Returns
    -------
    str
        The stable JSON string representation of the input object.
    """
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _sort_list_of_dicts(lst: list[Any]) -> list[Any]:
    """
    Sort a list of dictionaries by their stable JSON representation to ensure consistent ordering.
    This is used to canonicalize lists where order is not semantically meaningful.

    Parameters
    ----------
    lst : list[Any]
        The list of dictionaries to sort.

    Returns
    -------
    list[Any]
        A new list sorted by the stable JSON representation of its dictionary elements.
    """
    return sorted(lst, key=_stable_json)


def _canonicalize_function_payload(d: dict[str, Any]) -> dict[str, Any]:
    """
    Make semantically-equivalent FunctionItems produce identical packed keys.
    This involves sorting lists of dictionaries (e.g., operations, inputs, outputs)
    to ensure that different orderings of the same content yield the same representation.

    Parameters
    ----------
    d : dict[str, Any]
        The dictionary representation of a FunctionItem to canonicalize.

    Returns
    -------
    dict[str, Any]
        A new dictionary with sorted lists to ensure consistent representation of semantically equivalent FunctionItems.
    """
    d = dict(d)

    if isinstance(d.get("operation"), list):
        d["operation"] = _sort_list_of_dicts(d["operation"])

    for k in ("input", "output"):
        items = d.get(k)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("format"), list):
                    item["format"] = _sort_list_of_dicts(item["format"])
            d[k] = _sort_list_of_dicts(items)

    return d


def _pack_function_item(fi: FunctionItem, *, ignore_free_text: bool = False) -> str:
    """
    Return a hashable packed representation of a FunctionItem by
    converting it to a primitive dict, canonicalizing it, and then to a stable JSON string.

    Parameters
    ----------
    fi : FunctionItem
        The FunctionItem to pack.
    ignore_free_text : bool, optional
        Whether to ignore free-text fields like "note" and "cmd" in the packing process
        (default is ``False``).

    Returns
    -------
    str
        A stable JSON string representation of the FunctionItem that can be used for hashing or comparison.
    """
    prim = object_to_primitive(fi)
    prim = normalize_dict_strings(prim)

    if ignore_free_text:
        prim.pop("note", None)
        prim.pop("cmd", None)

    prim = _canonicalize_function_payload(prim)
    return _stable_json(prim)


def _unpack_function_item(packed: str) -> FunctionItem:
    """
    Unpack a FunctionItem from its packed JSON string representation.

    Parameters
    ----------
    packed : str
        The packed JSON string representation of a FunctionItem.

    Returns
    -------
    FunctionItem
        The unpacked FunctionItem reconstructed from the JSON string.
    """
    return FunctionItem(**json.loads(packed))


def _extract_functions_from_readme(gh_readme: str | None) -> set[str] | None:
    """
    Extract function annotations from the GitHub README by finding all YAML blocks
    that match the function annotation pattern, parsing them into FunctionItems,
    and returning a set of their packed representations for comparison.

    Parameters
    ----------
    gh_readme : str | None
        The content of the GitHub README to extract function annotations from.

    Returns
    -------
    set[str] | None
        A set of packed FunctionItem representations extracted from the README, or ``None`` if no
        function annotations are found.
    """
    yamls = find_match_yamls(gh_readme)

    function_keys = set()
    for yaml_str in yamls:
        try:
            data = yaml.safe_load(yaml_str)
            if not isinstance(data, dict):
                logger.warning("YAML block is not a dictionary, skipping: %s", yaml_str)
                continue

            function_item = FunctionItem(**data)
            key = _pack_function_item(function_item, ignore_free_text=False)
            function_keys.add(key)

        except yaml.YAMLError as e:
            logger.warning("Failed to parse YAML block, skipping: %s\nError: %s", yaml_str, e)

    return function_keys or None


async def map_functions(gh_readme: str | None, bt_functions: list[FunctionItem] | None) -> list[FunctionItem] | None:
    """
    Map and reconcile GitHub and bio.tools function annotations using the generic
    bio.tools-on-top-of-GitHub policy with canonicalization.

    Function comparison is performed on the packed representations of FunctionItems,
    which are designed to yield identical keys for semantically equivalent functions
    regardless of ordering or free-text differences.

    Parameters
    ----------
    gh_readme : str | None
        The current README content from GitHub, or ``None`` if the file does not exist yet.
    bt_functions : list[FunctionItem] | None
        The list of `FunctionItem` instances from bio.tools metadata, or ``None`` if no functions are defined.

    Returns
    -------
    list[FunctionItem] | None
        The reconciled list of `FunctionItem` instances to be used in bio.tools metadata,
        or ``None`` if no functions should be included.
    """
    bt_norm = (
        {_pack_function_item(fi, ignore_free_text=False) for fi in bt_functions} if bt_functions is not None else None
    )

    async def build_bt_from_norm(fi_keys):
        return [_unpack_function_item(fi) for fi in fi_keys] if fi_keys is not None else None

    return await reconcile_gh_ontop_bt(
        gh_norm=gh_readme,
        bt_norm=bt_norm,
        bt_value=bt_functions,
        build_bt_from_gh=_extract_functions_from_readme,
        build_bt_from_norm=build_bt_from_norm,
        log_label="functions",
    )
