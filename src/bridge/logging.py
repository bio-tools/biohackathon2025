"""
Project-wide logging setup.
Provides plaintext logs for CLI, JSON lines for API, and conservative defaults for library use;
also dials down noisy third-party loggers.
"""

import logging
import sys
from logging.config import dictConfig
from typing import Literal

from bridge.config import settings

USER_LOGGER_NAME = "bridge.user"

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


def setup_logging(mode: Literal["cli", "api", "package"] = "package"):
    """
    Configure global logging for the bridge project.

    Parameters
    ----------
    mode : Literal["cli", "api", "package"]
        One of: "cli", "api", or "package".
        - "cli" - plain text logs (for command-line tools)
        - "api" - json-line logs (for API services)
        - "package" - minimal setup for library use
    """
    log_level = getattr(settings, "log_level", "INFO").upper()

    if mode == "api":
        # json-like logs
        dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "json": {
                        "format": (
                            '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}'
                        ),
                        "datefmt": "%Y-%m-%dT%H:%M:%S",
                    },
                    "user_json": {
                        "format": ('{"time":"%(asctime)s","event_type":"%(event_type)s","message":"%(message)s"}'),
                        "datefmt": "%Y-%m-%dT%H:%M:%S",
                    },
                },
                "handlers": {
                    "default": {
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                        "formatter": "json",
                    },
                    "user": {
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                        "formatter": "user_json",
                    },
                },
                "root": {
                    "level": log_level,
                    "handlers": ["default"],
                },
                "loggers": {
                    f"{USER_LOGGER_NAME}": {
                        "level": log_level,
                        "handlers": ["user"],
                        "propagate": False,
                    },
                },
            }
        )

    elif mode == "cli":
        # plain text logs
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
            stream=sys.stdout,
            force=True,
        )

        # user-facing logger formatting for CLI
        user_logger = logging.getLogger(USER_LOGGER_NAME)
        user_logger.setLevel(log_level)
        user_logger.propagate = False
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [USER] %(levelname)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        user_logger.handlers = [handler]

    elif mode == "package":
        # respect existing loggers
        root = logging.getLogger()
        logging.basicConfig(
            level=log_level if root.level == logging.NOTSET else root.level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
            stream=sys.stderr,
        )

        # user-facing logger formatting for library use
        user_logger = logging.getLogger(USER_LOGGER_NAME)
        user_logger.setLevel(log_level)
        user_logger.propagate = False
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [USER] %(levelname)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        user_logger.handlers = [handler]

    else:
        raise ValueError(f"Unknown logging mode: {mode}")

    # Common noise suppression
    logging.getLogger("httpcore").setLevel("WARNING")
    logging.getLogger("httpx").setLevel("INFO")
    logging.getLogger("uvicorn").setLevel("INFO")
    logging.getLogger("asyncio").setLevel("WARNING")

    logger = logging.getLogger(__name__)
    logger.propagate = True
    logger.debug(f"Logging initialized for mode={mode}, level={log_level}")


def get_user_logger() -> logging.Logger:
    """
    Get the user-facing logger.

    Returns
    -------
    logging.Logger
        The user-facing logger.
    """
    return logging.getLogger(USER_LOGGER_NAME)
