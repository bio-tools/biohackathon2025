"""
Cross-cutting utilities.
"""

import inspect


async def maybe_await(func, *args, **kwargs):
    """
    Call a function that may be async or sync, and await it if necessary.

    Parameters
    ----------
    func : Callable
        The function to call.
    *args
        Positional arguments to pass to the function.
    **kwargs
        Keyword arguments to pass to the function.

    Returns
    -------
    Any
        The result of the function call, awaited if it was async.
    """
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


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
