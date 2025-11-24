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
                            '{"time":"%(asctime)s",'
                            '"level":"%(levelname)s",'
                            '"name":"%(name)s",'
                            '"message":"%(message)s"}'
                        ),
                        "datefmt": "%Y-%m-%dT%H:%M:%S",
                    },
                },
                "handlers": {
                    "default": {
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                        "formatter": "json",
                    },
                },
                "root": {
                    "level": log_level,
                    "handlers": ["default"],
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

    elif mode == "package":
        # respect existing loggers
        root = logging.getLogger()
        logging.basicConfig(
            level=log_level if root.level == logging.NOTSET else root.level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
            stream=sys.stderr,
        )

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
