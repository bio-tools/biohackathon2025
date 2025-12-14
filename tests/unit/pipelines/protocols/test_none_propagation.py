"""
Unit tests for SafeAttr and deep_unwrap (parametrized).

Covers *public* behavior:
- safe attribute/item access (missing -> SafeAttr(None))
- safe calling (non-callable -> SafeAttr(None), exceptions -> SafeAttr(None))
- iteration rules (no fake iteration for None/strings/mappings; iterables yield SafeAttr)
- len/bool/unwrap semantics
- deep_unwrap recursion over common containers + cycle guard
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from bridge.pipelines.protocols.none_propagation import SafeAttr, deep_unwrap  # adjust if needed


# -----------------------------
# Fixtures / dummies
# -----------------------------


class _Child:
    y = "hello"


class _Obj:
    def __init__(self):
        self.x = 123
        self.child = _Child()


@dataclass
class _Box:
    """Simple custom object to verify deep_unwrap leaves non-container custom types intact."""

    v: object


# -----------------------------
# SafeAttr: getattr
# -----------------------------


@pytest.mark.parametrize(
    "base, path, expected",
    [
        (_Obj(), "x", 123),
        (_Obj(), "child.y", "hello"),
        (_Obj(), "nope", None),
        (_Obj(), "nope.anything.more", None),
        (None, "x", None),
        (123, "x", None),
    ],
)
def test_safeattr_getattr_chain(base, path, expected):
    s = SafeAttr(base)
    cur = s
    for part in path.split("."):
        cur = getattr(cur, part)
        assert isinstance(cur, SafeAttr)
    assert cur.unwrap() == expected


@pytest.mark.parametrize(
    "base, path, default, expected",
    [
        (_Obj(), "nope", "D", "D"),
        (_Obj(), "nope.anything.more", 0, 0),
        (None, "x", "fallback", "fallback"),
    ],
)
def test_safeattr_unwrap_default_on_none(base, path, default, expected):
    s = SafeAttr(base)
    cur = s
    for part in path.split("."):
        cur = getattr(cur, part)
    assert cur.unwrap(default=default) == expected


# -----------------------------
# SafeAttr: getitem
# -----------------------------


@pytest.mark.parametrize(
    "base, key, expected",
    [
        ({"a": 1}, "a", 1),
        ({"a": 1}, "missing", None),
        ([], 0, None),  # list index error => SafeAttr(None)
        (123, "x", None),  # non-subscriptable => SafeAttr(None)
        (None, "x", None),
    ],
)
def test_safeattr_getitem(base, key, expected):
    s = SafeAttr(base)[key]
    assert isinstance(s, SafeAttr)
    assert s.unwrap() == expected


# -----------------------------
# SafeAttr: call
# -----------------------------


def _adder(a, b):
    return a + b


def _boom(*_a, **_k):
    raise RuntimeError("nope")


@pytest.mark.parametrize(
    "base, args, kwargs, expected",
    [
        (_adder, (2, 3), {}, 5),
        (10, (), {}, None),  # non-callable
        (_boom, (), {}, None),  # callable but raises
        (None, (), {}, None),
    ],
)
def test_safeattr_call(base, args, kwargs, expected):
    out = SafeAttr(base)(*args, **kwargs)
    assert isinstance(out, SafeAttr)
    assert out.unwrap() == expected


# -----------------------------
# SafeAttr: len / bool / repr
# -----------------------------


@pytest.mark.parametrize(
    "base, expected_len",
    [
        ([1, 2, 3], 3),
        ("abc", 3),  # SafeAttr.__len__ delegates to underlying
        ({"a": 1}, 1),
        (None, 0),
        (object(), 0),
    ],
)
def test_safeattr_len(base, expected_len):
    assert len(SafeAttr(base)) == expected_len


@pytest.mark.parametrize(
    "base, expected_bool",
    [
        ("x", True),
        ("", False),
        ([1], True),
        ([], False),
        (None, False),
        (0, False),
        (1, True),
    ],
)
def test_safeattr_bool(base, expected_bool):
    assert bool(SafeAttr(base)) is expected_bool


@pytest.mark.parametrize(
    "base, must_contain",
    [
        ({"a": 1}, "SafeAttr("),
        (None, "SafeAttr("),
        ("x", "SafeAttr("),
    ],
)
def test_safeattr_repr(base, must_contain):
    r = repr(SafeAttr(base))
    assert r.startswith(must_contain)


# -----------------------------
# SafeAttr: iteration
# -----------------------------


@pytest.mark.parametrize(
    "base",
    [
        None,
        "abc",
        b"abc",
        bytearray(b"abc"),
        {"a": 1},  # mappings explicitly return empty iterator
        123,  # non-iterable
        object(),  # non-iterable
    ],
)
def test_safeattr_iter_returns_empty_for_non_iterables_and_excluded_types(base):
    assert list(SafeAttr(base)) == []


@pytest.mark.parametrize(
    "base, expected",
    [
        ([1, 2, 3], [1, 2, 3]),
        ((4, 5), [4, 5]),
        ((i for i in [6, 7]), [6, 7]),
    ],
)
def test_safeattr_iter_wraps_items(base, expected):
    out = list(SafeAttr(base))
    assert all(isinstance(x, SafeAttr) for x in out)
    assert [x.unwrap() for x in out] == expected


# -----------------------------
# deep_unwrap: primitives and SafeAttr leaf
# -----------------------------


@pytest.mark.parametrize(
    "v, expected",
    [
        (SafeAttr(1), 1),
        (SafeAttr(None), None),
        ("x", "x"),
        (b"x", b"x"),
        (bytearray(b"x"), bytearray(b"x")),
        (None, None),
    ],
)
def test_deep_unwrap_leaf_and_primitives(v, expected):
    assert deep_unwrap(v) == expected


# -----------------------------
# deep_unwrap: containers
# -----------------------------


@pytest.mark.parametrize(
    "v, expected",
    [
        (
            {"a": SafeAttr(1), "b": SafeAttr("x")},
            {"a": 1, "b": "x"},
        ),
        (
            {"k": {"inner": [SafeAttr(2), 3]}},
            {"k": {"inner": [2, 3]}},
        ),
        (
            {SafeAttr("k"): SafeAttr(9)},
            {"k": 9},
        ),
        (
            {"s": {SafeAttr("x"), SafeAttr("y")}},
            {"s": {"x", "y"}},
        ),
        (
            {"seq": (SafeAttr(1), SafeAttr(2))},  # Sequence -> list by implementation
            {"seq": [1, 2]},
        ),
    ],
)
def test_deep_unwrap_containers(v, expected):
    assert deep_unwrap(v) == expected


def test_deep_unwrap_leaves_custom_objects_intact():
    obj = _Box(v=SafeAttr(5))
    out = deep_unwrap({"x": obj, "y": SafeAttr(1)})
    assert out["x"] is obj
    assert out["y"] == 1


def test_deep_unwrap_cycle_guard():
    a = []
    a.append(a)  # cycle
    a.append(SafeAttr(1))

    out = deep_unwrap(a)

    # cycle element returned as-is; second element unwrapped
    assert isinstance(out, list)
    assert out[0] is a
    assert out[1] == 1
