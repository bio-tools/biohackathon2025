"""
Unit tests for ModelsMap / MapItem / Method and (de)serialization of mapping functions.

Public behavior covered:
- ModelsMap exposes SafeAttr proxies for repo/metadata
- MapItem validates `fn` as None/callable/dotted-path, rejects bad inputs
- MapItem serializes `fn` to an importable dotted path
- MapItem.run() deep-unwraps inputs and supports sync + async fns via maybe_await
"""

from __future__ import annotations

import types
from functools import partial
from pydantic_core import PydanticSerializationError

import pytest

import bridge.pipelines.protocols.map as mod
from bridge.pipelines.protocols.map import MapItem, Method, ModelsMap
from bridge.pipelines.protocols.none_propagation import SafeAttr


# -----------------------------
# Helpers (top-level callables for dotted-path serialization)
# -----------------------------


def _sync_echo(repo, schema):
    return {"repo": repo, "schema": schema}


async def _async_echo(repo, schema):
    return {"repo": repo, "schema": schema}


def _sync_uses_values(repo, schema):
    # used to assert deep_unwrap happened (SafeAttr should be unwrapped)
    return (repo, schema)


def _sync_pair(x, y):
    return (x, y)


# -----------------------------
# ModelsMap
# -----------------------------


class _ConcreteMap(ModelsMap):
    @property
    def map(self):
        return {"x": 1}


@pytest.mark.parametrize(
    "repo, metadata",
    [
        ({"a": 1}, {"b": 2}),
        (types.SimpleNamespace(x=1), types.SimpleNamespace(y=2)),
        (None, None),
    ],
)
def test_modelsmap_exposes_safeattr_proxies(repo, metadata):
    m = _ConcreteMap(repo=repo, metadata=metadata)

    assert isinstance(m.repo, SafeAttr)
    assert isinstance(m.metadata, SafeAttr)

    # Missing attribute chains must not raise
    assert m.repo.foo.bar.baz.unwrap() is None
    assert m.metadata.missing.chain.unwrap() is None
    assert m.repo["nope"]["still_nope"].unwrap() is None


# -----------------------------
# _to_path / _import_from_path validation (via MapItem)
# -----------------------------


@pytest.mark.parametrize(
    "fn_value, expect_ok",
    [
        (None, True),
        (_sync_echo, True),
        (_async_echo, True),
        (f"{__name__}:_sync_echo", True),
        (f"{__name__}._sync_echo", True),
        ("not.a.real.module:fn", False),
        (f"{__name__}:does_not_exist", False),
        (123, False),
    ],
)
def test_mapitem_fn_validator_accepts_callable_or_importable_string(fn_value, expect_ok):
    if expect_ok:
        mi = MapItem(schema_entry=None, repo_entry=None, method=Method.EXACT, fn=fn_value)
        assert (mi.fn is None) if fn_value is None else callable(mi.fn)
    else:
        with pytest.raises(Exception):
            _ = MapItem(schema_entry=None, repo_entry=None, method=Method.EXACT, fn=fn_value)


@pytest.mark.parametrize(
    "bad_fn",
    [
        partial(_sync_pair, 1),
    ],
)
def test_mapitem_fn_serializer_rejects_partials(bad_fn):
    mi = MapItem(schema_entry=None, repo_entry=None, method=Method.EXACT, fn=bad_fn)

    with pytest.raises(PydanticSerializationError) as exc:
        _ = mi.model_dump()

    assert "serialize_fn" in str(exc.value)
    assert "partials aren’t serializable" in str(exc.value)


def test_mapitem_fn_serializer_roundtrips_for_top_level_callable():
    mi = MapItem(schema_entry=None, repo_entry=None, method=Method.EXACT, fn=_sync_echo)

    dumped = mi.model_dump()
    assert dumped["fn"] == f"{__name__}:_sync_echo"

    mi2 = MapItem(schema_entry=None, repo_entry=None, method=Method.EXACT, fn=dumped["fn"])
    assert mi2.fn is _sync_echo


# -----------------------------
# MapItem.run()
# -----------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fn, repo_entry, schema_entry, expected_repo, expected_schema",
    [
        (_sync_uses_values, SafeAttr({"x": 1}), SafeAttr({"y": 2}), {"x": 1}, {"y": 2}),
        (_sync_uses_values, {"x": SafeAttr(1)}, {"y": SafeAttr(2)}, {"x": 1}, {"y": 2}),
        (_sync_uses_values, SafeAttr(None), SafeAttr("s"), None, "s"),
    ],
)
async def test_mapitem_run_deep_unwraps_inputs(fn, repo_entry, schema_entry, expected_repo, expected_schema):
    mi = MapItem(schema_entry=schema_entry, repo_entry=repo_entry, method=Method.EXACT, fn=fn)
    out = await mi.run()
    assert out == (expected_repo, expected_schema)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fn",
    [
        _sync_echo,
        _async_echo,
    ],
)
async def test_mapitem_run_supports_sync_and_async_fns(fn):
    mi = MapItem(schema_entry={"a": 1}, repo_entry={"b": 2}, method=Method.EXACT, fn=fn)
    out = await mi.run()
    assert out == {"repo": {"b": 2}, "schema": {"a": 1}}


@pytest.mark.asyncio
async def test_mapitem_run_returns_none_when_fn_is_none():
    mi = MapItem(schema_entry={"a": 1}, repo_entry={"b": 2}, method=Method.EXACT, fn=None)
    assert await mi.run() is None
