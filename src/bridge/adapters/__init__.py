"""
User-facing adapters for the bridge: a FastAPI app and a Typer CLI.
"""

from .api import app as api_app
from .cli import app as cli_app

__all__ = ["api_app", "cli_app"]
