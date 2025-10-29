"""
Decorator for registering a handler for a PipelineGoal.
Ensures wiring is initialized before execution, then routes calls into the configured pipeline graph.
"""

import functools
import logging

from bridge.pipelines import PipelineGoal

from .base import _handler_registry
from .state import is_initialized
from .wiring import wiring

logger = logging.getLogger(__name__)


def register_handler(goal: PipelineGoal, *, auto_wire: bool = True, force_wire: bool = False):
    """
    Register a handler function for a specific pipeline goal.
    Automatically ensures the registry wiring is initialized before the handler runs.
    Decorator function.

    Parameters
    ----------
    goal : PipelineGoal
        The pipeline goal to register the handler for.
    auto_wire : bool, optional
        If True, automatically wire the registry before running the handler (default: True).
    force_wire : bool, optional
        If True, re-initialize wiring even if already initialized (default: False).

    Raises
    ------
    ValueError
        If a handler is already registered for the specified goal.
    """

    def decorator(func: callable):
        if goal in _handler_registry:
            existing = _handler_registry[goal]
            raise ValueError(
                f"Handler for goal '{goal.name}' already registered " f"({existing.__module__}.{existing.__name__})."
            )

        @functools.wraps(func)
        def wrapped_handler(*args, **kwargs):
            if auto_wire and (not is_initialized() or force_wire):
                logger.debug("Auto-wiring registry before executing handler for %s", goal.name)
                wiring(force=force_wire)
            return func(*args, **kwargs)

        _handler_registry[goal] = wrapped_handler
        return wrapped_handler

    return decorator
