"""
Minimal module tracking whether global wiring has been performed to prevent duplicate initialization.
"""

_initialized = False


def is_initialized() -> bool:
    """
    Check if the registry has been initialized.

    Returns
    -------
    bool
        True if initialized, False otherwise.
    """
    return _initialized


def mark_initialized():
    """
    Mark the registry as initialized.
    """
    global _initialized
    _initialized = True
