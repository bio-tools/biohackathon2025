"""
Decorators for pipeline functions.
"""

import functools
from typing import Any


def prepare_match_items(func: callable):
    """
    Check and normalize inputs for match methods.

    Validation rule:
    - None: returns 0 without further matching

    Normalization rules:
    - list/set/tuple: converted to set
    # TODO: handle dicts?
    """

    @functools.wraps(func)
    def wrapper(self, item1: Any, item2: Any) -> float:
        # Missing inout value
        if item1 is None or item2 is None:
            return 0.0

        def normalize(item):
            if isinstance(item, (list, set, tuple)):
                return set(item)
            else:
                return item

        item1_norm, item2_norm = normalize(item1), normalize(item2)
        return func(self, item1_norm, item2_norm)

    return wrapper
