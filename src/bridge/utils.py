"""
Cross-cutting utilities.
"""

import inspect
from collections.abc import Callable
from typing import Any


async def maybe_await(func: Callable[..., Any] | Any, *args, **kwargs) -> Any:
    """
    Wrap a function/method as an awaitable that may be async or sync,
    or to return a plain value.

    Parameters
    ----------
    func : Callable[..., Any] | Any
        A function/method to call, or a plain value.
    *args
        Positional arguments to pass to the function if `func` is callable.
    **kwargs
        Keyword arguments to pass to the function if `func` is callable.

    Returns
    -------
    Any
        The result of calling the function, or the plain value.
    """
    # Case 1: caller passed an already-awaitable object
    #   e.g. maybe_await(some_async_func()), maybe_await(coro)
    if inspect.isawaitable(func):
        return await func

    # Case 2: caller passed a function / method
    if callable(func):
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    # Case 3: plain value (not callable, not awaitable)
    if args or kwargs:
        raise TypeError(
            f"maybe_await: got non-callable {func!r} but also args/kwargs; did you mean maybe_await(some_func, ...)?"
        )
    return func


def require_args(*required):
    """
    Ensure that certain keyword arguments are provided to an async function.
    Decorator function.

    Parameters
    ----------
    required : str
        Names of required keyword arguments. Can be multiple.
    """

    def decorator(fn):
        async def wrapper(**kwargs):
            missing = [r for r in required if r not in kwargs]
            if missing:
                raise ValueError(f"Missing required args: {', '.join(missing)}")
            return await fn(**kwargs)

        return wrapper

    return decorator
