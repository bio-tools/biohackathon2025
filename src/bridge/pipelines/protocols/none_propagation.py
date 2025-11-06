"""
SafeAttr proxy class for safe attribute/item access and deep unwrapping utility.
"""

from collections.abc import Mapping, Sequence, Set


class SafeAttr:
    """
    A proxy class that safely accesses attributes and items of an underlying object.
    If an attribute or item does not exist, it returns a SafeAttr wrapping None instead of raising an exception.
    """

    __slots__ = ("_v",)

    def __init__(self, v):
        object.__setattr__(self, "_v", v)

    def __getattr__(self, name):
        try:
            return SafeAttr(getattr(self._v, name))
        except Exception:
            return SafeAttr(None)

    def __getitem__(self, key):
        try:
            return SafeAttr(self._v[key])
        except Exception:
            return SafeAttr(None)

    def __call__(self, *args, **kwargs):
        """
        Call the underlying object if it is callable, returning a SafeAttr wrapping the result.
        """
        if callable(self._v):
            try:
                return SafeAttr(self._v(*args, **kwargs))
            except Exception:
                return SafeAttr(None)
        return SafeAttr(None)

    def __iter__(self):
        v = self._v
        if v is None or isinstance(v, (str, bytes, bytearray)) or isinstance(v, Mapping):
            return iter(())  # don’t fake iteration
        try:
            it = iter(v)
        except TypeError:
            return iter(())
        return (SafeAttr(x) for x in it)

    def __len__(self):
        try:
            return len(self._v)
        except Exception:
            return 0

    def __bool__(self):
        return bool(self._v)

    def unwrap(self, default=None):
        """
        Unwrap the underlying value, or return default if None.

        Parameters
        ----------
        default : Any
            The default value to return if the underlying value is None.

        Returns
        -------
        Any
            The deeply unwrapped value.
        """
        return self._v if self._v is not None else default

    def __repr__(self):
        return f"SafeAttr({self._v!r})"


def deep_unwrap(v, *, _seen=None):
    """
    Recursively unwrap SafeAttr instances within common container types.

    Parameters
    ----------
    v : Any
        The value to unwrap.
    _seen : set | None
        Internal set to track seen object IDs for cycle detection.

    Returns
    -------
    Any
        The deeply unwrapped value.
    """
    # Only unwrap SafeAttr and common container *interfaces*.
    if isinstance(v, SafeAttr):
        return deep_unwrap(v.unwrap(), _seen=_seen)

    # Primitives / scalars just pass through.
    if isinstance(v, (str, bytes, bytearray)) or v is None:
        return v

    # Cycle guard
    if _seen is None:
        _seen = set()
    try:
        oid = id(v)
        if oid in _seen:
            return v
        _seen.add(oid)
    except Exception:
        # Unhashable / odd cases — just return as-is.
        return v

    if isinstance(v, Mapping):
        return {deep_unwrap(k, _seen=_seen): deep_unwrap(val, _seen=_seen) for k, val in v.items()}

    if isinstance(v, Set):
        return {deep_unwrap(x, _seen=_seen) for x in v}

    if isinstance(v, Sequence) and not isinstance(v, (str, bytes, bytearray)):
        return [deep_unwrap(x, _seen=_seen) for x in v]

    # Any other (your “hundreds of custom types”) — leave intact.
    return v
