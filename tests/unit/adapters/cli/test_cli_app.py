"""
Unit tests for the CLI app entrypoint.
"""

from typer.testing import CliRunner

from bridge.__main__ import main_app as root_cli
from bridge.adapters.cli import app as inner_cli

runner = CliRunner()


def test_root_cli_help():
    """
    Test that the root CLI app shows help correctly.

    Raises
    ------
    AssertionError
        If the help output does not match expected values.
    """
    result = runner.invoke(root_cli, ["--help"])
    assert result.exit_code == 0
    # this is the text you defined on main_app
    assert "GitHub ⇄ bio.tools bridge entrypoint" in result.stdout
    # inner CLI should be wired as subcommand
    assert "cli" in result.stdout


def test_inner_cli_help():
    """
    Test that the inner CLI app shows help correctly.

    Raises
    ------
    AssertionError
        If the help output does not match expected values.
    """
    result = runner.invoke(inner_cli, ["--help"])
    assert result.exit_code == 0
    # don't assert the banner here; it's a different app
    assert "Usage:" in result.stdout
