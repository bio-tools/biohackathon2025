"""
Root Typer application for the CLI.
Registers directional subcommands for interactive runs and sets up logging.
"""

import logging

import typer

from bridge.logging import setup_logging

from .commands import biotools_to_github, github_to_biotools

logger = logging.getLogger(__name__)

app = typer.Typer(help="GitHub ⇄ bio.tools bridge CLI")

# register subcommands
app.add_typer(biotools_to_github.app, name="biotools-to-github")
app.add_typer(github_to_biotools.app, name="github-to-biotools")


@app.callback()
def main():
    """Set up logging for the CLI application."""
    setup_logging("cli")
    logger.info("Starting CLI application")
