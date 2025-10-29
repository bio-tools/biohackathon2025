"""
Quality-related scripts: linting and formatting.
"""

import subprocess
import sys


def _run(cmd: list[str]) -> int:
    """Run a subprocess command and return its return code."""
    return subprocess.run(cmd, check=False).returncode


def lint() -> None:
    """CI-style checks: Ruff lint + Black check."""
    rc = 0
    rc |= _run([sys.executable, "-m", "ruff", "check", "."])
    rc |= _run([sys.executable, "-m", "black", "--check", "."])
    raise SystemExit(rc)


def fmt() -> None:
    """Fix imports/lints via Ruff, then format via Black."""
    rc = 0
    rc |= _run([sys.executable, "-m", "ruff", "check", ".", "--fix", "--unsafe-fixes"])
    rc |= _run([sys.executable, "-m", "black", "."])
    raise SystemExit(rc)
