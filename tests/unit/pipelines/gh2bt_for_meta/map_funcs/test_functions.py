"""
Unit tests for mapping GitHub function annotations to bio.tools functions (gh2bt map_functions).

These tests focus on behavior, not logging. We patch:
- find_match_yamls: deterministic extraction from README
- yaml.safe_load: real (safe) parsing of YAML strings
- object_to_primitive / normalize_dict_strings: simplified + deterministic (so packing is stable)
- reconcile_gh_ontop_bt: real (we test integration-ish behavior), but we also
  include one test that patches it to assert the normalized inputs if you want.

We use minimal FunctionItem-like stubs via monkeypatching the module's FunctionItem
constructor to avoid depending on Pydantic validation details in unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

import bridge.pipelines.gh2bt_for_meta.map_funcs.functions as mod


# -----------------------------
# Minimal FunctionItem stub
# -----------------------------


@dataclass(frozen=True)
class _FuncItem:
    """
    A minimal stand-in for bridge.core.biotools.FunctionItem.

    We store the raw dict payload and expose it in a way the mapping code expects:
    - It must be constructible as FunctionItem(**data)
    - object_to_primitive(FunctionItem) must produce a dict
    """

    payload: dict[str, Any]


# -----------------------------
# Helpers
# -----------------------------


def _fi(**payload: Any) -> _FuncItem:
    return _FuncItem(payload=payload)


def _yaml_for(payload: dict[str, Any]) -> str:
    """
    Produce a simple YAML string. We keep it small and explicit.
    """
    # Minimal YAML: key: value, and lists as "-".
    # For these tests, safe_load handles it.
    import yaml as _yaml  # local import to avoid confusion with mod.yaml

    return _yaml.safe_dump(payload, sort_keys=False)


# -----------------------------
# Fixtures: patch internals for determinism
# -----------------------------


@pytest.fixture(autouse=True)
def _patch_functionitem_and_primitives(monkeypatch):
    # Patch FunctionItem in the module under test to our stub constructor.
    monkeypatch.setattr(mod, "FunctionItem", lambda **data: _FuncItem(payload=dict(data)))

    # object_to_primitive: unwrap our stub; pass dicts through
    def fake_object_to_primitive(x):
        if isinstance(x, _FuncItem):
            return dict(x.payload)
        if isinstance(x, dict):
            return dict(x)
        return x

    # normalize_dict_strings: no-op except ensure strings are stripped
    def fake_normalize_dict_strings(d):
        def norm(v):
            if isinstance(v, str):
                return v.strip()
            if isinstance(v, list):
                return [norm(i) for i in v]
            if isinstance(v, dict):
                return {k: norm(val) for k, val in v.items()}
            return v

        return norm(dict(d))

    monkeypatch.setattr(mod, "object_to_primitive", fake_object_to_primitive)
    monkeypatch.setattr(mod, "normalize_dict_strings", fake_normalize_dict_strings)


@pytest.fixture
def _patch_find_match_yamls(monkeypatch):
    monkeypatch.setattr(mod, "find_match_yamls", lambda _readme: [])


# =========================================================
# Unit tests for helpers: packing/canonicalization
# =========================================================


def test_pack_ignores_note_and_cmd_when_requested():
    fi = _fi(
        operation=[{"term": "X"}],
        note="hello",
        cmd="--flag",
    )
    a = mod._pack_function_item(fi, ignore_free_text=False)
    b = mod._pack_function_item(fi, ignore_free_text=True)
    assert a != b
    # removing note/cmd should remove those substrings from packed JSON
    assert "note" in a
    assert "cmd" in a
    assert "note" not in b
    assert "cmd" not in b


def test_pack_canonicalizes_operation_list_order():
    fi1 = _fi(operation=[{"term": "A"}, {"term": "B"}])
    fi2 = _fi(operation=[{"term": "B"}, {"term": "A"}])
    assert mod._pack_function_item(fi1) == mod._pack_function_item(fi2)


def test_pack_canonicalizes_input_format_order_and_input_list_order():
    fi1 = _fi(
        operation=[{"term": "X"}],
        input=[
            {"data": {"term": "Seq"}, "format": [{"term": "FASTA"}, {"term": "TXT"}]},
            {"data": {"term": "Align"}, "format": [{"term": "SAM"}]},
        ],
    )
    fi2 = _fi(
        operation=[{"term": "X"}],
        input=[
            {"data": {"term": "Align"}, "format": [{"term": "SAM"}]},
            {"data": {"term": "Seq"}, "format": [{"term": "TXT"}, {"term": "FASTA"}]},  # swapped
        ],
    )
    assert mod._pack_function_item(fi1) == mod._pack_function_item(fi2)


def test_unpack_roundtrip_matches_packed_semantics():
    fi = _fi(operation=[{"term": "X"}], output=[{"data": {"term": "Y"}}])
    packed = mod._pack_function_item(fi)
    unpacked = mod._unpack_function_item(packed)
    assert isinstance(unpacked, _FuncItem)
    assert mod._pack_function_item(unpacked) == packed


# =========================================================
# _extract_functions_from_readme behavior
# =========================================================


@pytest.mark.parametrize(
    "case, yamls, expected_count",
    [
        ("no yamls => None", [], 0),
        ("one valid yaml => one function", [_yaml_for({"operation": [{"term": "X"}]})], 1),
        (
            "two valid yamls => two functions",
            [
                _yaml_for({"operation": [{"term": "X"}]}),
                _yaml_for({"operation": [{"term": "Y"}]}),
            ],
            2,
        ),
    ],
)
def test_extract_functions_from_readme_counts_valid_blocks(case, yamls, expected_count, monkeypatch):
    monkeypatch.setattr(mod, "find_match_yamls", lambda _readme: list(yamls))

    keys = mod._extract_functions_from_readme("README")
    if expected_count == 0:
        assert keys is None, case
    else:
        assert isinstance(keys, set)
        assert len(keys) == expected_count


def test_extract_functions_from_readme_skips_non_dict_yaml(monkeypatch):
    # YAML that loads to a list => skipped => None
    monkeypatch.setattr(mod, "find_match_yamls", lambda _readme: ["- a\n- b\n"])
    keys = mod._extract_functions_from_readme("README")
    assert keys is None


def test_extract_functions_from_readme_skips_yaml_parse_errors(monkeypatch):
    # invalid YAML => safe_load raises YAMLError => skipped => None
    monkeypatch.setattr(mod, "find_match_yamls", lambda _readme: [": bad ::: yaml"])
    keys = mod._extract_functions_from_readme("README")
    assert keys is None


def test_extract_functions_from_readme_dedupes_semantically_equivalent_blocks(monkeypatch):
    # same function but with operation list in different order => same packed key => set size 1
    y1 = _yaml_for({"operation": [{"term": "A"}, {"term": "B"}]})
    y2 = _yaml_for({"operation": [{"term": "B"}, {"term": "A"}]})
    monkeypatch.setattr(mod, "find_match_yamls", lambda _readme: [y1, y2])

    keys = mod._extract_functions_from_readme("README")
    assert keys is not None
    assert len(keys) == 1


# =========================================================
# map_functions reconciliation behavior (via reconcile_gh_ontop_bt)
# =========================================================


def test_map_functions_github_silent_preserves_bt(monkeypatch, _patch_find_match_yamls):
    # gh_readme is None => reconcile_gh_ontop_bt returns bt_value unchanged
    bt = [_fi(operation=[{"term": "BT"}])]
    out = mod.map_functions(gh_readme=None, bt_functions=bt)
    assert out == bt


def test_map_functions_when_bt_missing_builds_from_github(monkeypatch):
    # GitHub has functions => bt_norm None => returns built list
    y = _yaml_for({"operation": [{"term": "GH"}]})
    monkeypatch.setattr(mod, "find_match_yamls", lambda _readme: [y])

    out = mod.map_functions(gh_readme="README", bt_functions=None)
    assert out is not None
    assert isinstance(out, list)
    assert len(out) == 1
    assert out[0].payload["operation"][0]["term"] == "GH"


def test_map_functions_exact_match_preserves_original_bt_object(monkeypatch):
    # Same function present in bt and GitHub => union adds nothing => returns bt_value (same list object)
    payload = {"operation": [{"term": "Same"}]}
    y = _yaml_for(payload)
    monkeypatch.setattr(mod, "find_match_yamls", lambda _readme: [y])

    bt = [_fi(**payload)]
    out = mod.map_functions(gh_readme="README", bt_functions=bt)
    assert out is bt  # preserved (exact)


def test_map_functions_conflict_adds_github_on_top_of_bt(monkeypatch):
    # bt has A, GH has B => result has A and B (order not guaranteed)
    y = _yaml_for({"operation": [{"term": "B"}]})
    monkeypatch.setattr(mod, "find_match_yamls", lambda _readme: [y])

    bt = [_fi(operation=[{"term": "A"}])]
    out = mod.map_functions(gh_readme="README", bt_functions=bt)

    assert out is not None
    terms = {item.payload["operation"][0]["term"] for item in out}
    assert terms == {"A", "B"}


def test_map_functions_github_functions_all_invalid_preserves_bt(monkeypatch):
    # GitHub YAML is non-dict => _extract_functions_from_readme returns None => treated as "cannot build" => preserve bt
    monkeypatch.setattr(mod, "find_match_yamls", lambda _readme: ["- not-a-dict\n- still-not\n"])

    bt = [_fi(operation=[{"term": "A"}])]
    out = mod.map_functions(gh_readme="README", bt_functions=bt)
    assert out == bt


def test_map_functions_strips_strings_before_packing_so_equivalent_whitespace_matches(monkeypatch):
    # bt has "X", GH has " X " => normalize_dict_strings strips => packed keys match => preserve bt
    y = _yaml_for({"operation": [{"term": "  X  "}]})
    monkeypatch.setattr(mod, "find_match_yamls", lambda _readme: [y])

    bt = [_fi(operation=[{"term": "X"}])]
    out = mod.map_functions(gh_readme="README", bt_functions=bt)

    assert out is bt
