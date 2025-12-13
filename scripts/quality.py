"""
Quality-related scripts: linting and formatting.
"""

import subprocess
import sys
from pathlib import Path


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


def coverage_report() -> None:
    """Run tests with coverage reporting."""
    rc = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=bridge",
            "--cov-branch",
            "--cov-report=html",
        ]
    )

    if rc == 0:
        report_uri = Path("htmlcov/index.html").resolve().as_uri()
        _run([sys.executable, "-m", "webbrowser", report_uri])

    raise SystemExit(rc)
