"""
Cross-cutting utilities.
"""


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
