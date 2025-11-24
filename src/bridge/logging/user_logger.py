"""
Custom logger for user-level logging in the bridge module.
"""

import logging

CONFLICT_LEVEL = logging.INFO + 1
EXACT_LEVEL = logging.INFO + 2
ADDED_LEVEL = logging.INFO + 3
NOTE_LEVEL = logging.INFO + 4

logging.addLevelName(CONFLICT_LEVEL, "CONFLICT")
logging.addLevelName(EXACT_LEVEL, "EXACT")
logging.addLevelName(ADDED_LEVEL, "ADDED")
logging.addLevelName(NOTE_LEVEL, "NOTE")


class BridgeLogger(logging.Logger):
    """
    Logger with extra convenience methods:
        .conflict(), .exact(), .added(), .note()

    Behaves like a normal logger (msg, *args, **kwargs).
    """

    def conflict(self, msg, *args, **kwargs):
        """
        Log a "conflict" event.

        Parameters
        ----------
        msg : str
            The log message.
        *args
            Positional arguments for the log message.
        **kwargs
            Keyword arguments for the log message.
        """
        if self.isEnabledFor(CONFLICT_LEVEL):
            extra = kwargs.setdefault("extra", {})
            extra.setdefault("event_type", "conflict")
            self._log(CONFLICT_LEVEL, msg, args, **kwargs)

    def exact(self, msg, *args, **kwargs):
        """
        Log an "exact match" event.

        Parameters
        ----------
        msg : str
            The log message.
        *args
            Positional arguments for the log message.
        **kwargs
            Keyword arguments for the log message.
        """
        if self.isEnabledFor(EXACT_LEVEL):
            extra = kwargs.setdefault("extra", {})
            extra.setdefault("event_type", "exact")
            self._log(EXACT_LEVEL, msg, args, **kwargs)

    def added(self, msg, *args, **kwargs):
        """
        Log an "added" event.

        Parameters
        ----------
        msg : str
            The log message.
        *args
            Positional arguments for the log message.
        **kwargs
            Keyword arguments for the log message.
        """
        if self.isEnabledFor(ADDED_LEVEL):
            extra = kwargs.setdefault("extra", {})
            extra.setdefault("event_type", "added")
            self._log(ADDED_LEVEL, msg, args, **kwargs)

    def note(self, msg, *args, **kwargs):
        """
        Log a "note" event.

        Parameters
        ----------
        msg : str
            The log message.
        *args
            Positional arguments for the log message.
        **kwargs
            Keyword arguments for the log message.
        """
        if self.isEnabledFor(NOTE_LEVEL):
            extra = kwargs.setdefault("extra", {})
            extra.setdefault("event_type", "note")
            self._log(NOTE_LEVEL, msg, args, **kwargs)


logging.setLoggerClass(BridgeLogger)
