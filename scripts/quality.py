"""
Quality-related scripts: linting and formatting.
"""

import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from subprocess import DEVNULL, Popen, run

BASE_DIR = Path(__file__).resolve().parent.parent
BLACK_CONFIG = str(BASE_DIR / "black.toml")


def _run(cmd: list[str]) -> int:
    """Run a subprocess command and return its return code."""
    return subprocess.run(cmd, check=False).returncode


def lint() -> None:
    """CI-style checks: Ruff lint + Black check."""
    rc = 0
    rc |= _run([sys.executable, "-m", "ruff", "check", "."])
    rc |= _run([sys.executable, "-m", "black", "--check", ".", "--config", BLACK_CONFIG])
    raise SystemExit(rc)


def fmt() -> None:
    """Fix imports/lints via Ruff, then format via Black."""
    rc = 0
    rc |= _run([sys.executable, "-m", "ruff", "check", ".", "--fix", "--unsafe-fixes"])
    # Black: apply formatting using your config
    rc |= _run([sys.executable, "-m", "black", ".", "--config", BLACK_CONFIG])
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


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

_TOTAL_RE = re.compile(r"Total\s+jobs:\s*(\d+)", re.IGNORECASE)
_COMPLETE_RE = re.compile(r"Complete:\s*(\d+)\s*\(([\d.]+)%\)", re.IGNORECASE)
_SURV_RE = re.compile(r"Surviving\s+mutants:\s*(\d+)\s*\(([\d.]+)%\)", re.IGNORECASE)


def _clean_report_text(s: str) -> str:
    s = s or ""
    s = _ANSI_RE.sub("", s)
    return s


def cosmic_ray_report(
    env: str | None = None,  # "local" | "ci" | None(auto)
    config_path: str | None = None,  # override if you want
    session_path: str | None = None,  # override if you want
    html_report_path: str | None = None,  # override if you want
    progress_every_s: int | None = None,  # override if you want
    open_browser: bool | None = None,  # override if you want
) -> None:
    """
    Run Cosmic Ray mutation testing with live progress reporting and HTML report generation.

    Supports:
      - local: uses cosmic-ray.local.toml, prints progress, opens browser (default)
      - ci:    uses cosmic-ray.ci.toml, prints minimal progress, does NOT open browser (default)

    Env auto-detection:
      - if env is None and CI is set -> "ci"
      - else -> "local"
    """
    if env is None:
        env = "ci" if os.getenv("CI") else "local"
        print(f"Auto-detected Cosmic Ray env as: {env}")
    env = env.lower().strip()
    if env not in {"local", "ci"}:
        raise ValueError(f"env must be 'local' or 'ci', got: {env!r}")

    # Defaults per environment (can be overridden via args)
    suffix = "ci" if env == "ci" else "local"
    config_path = config_path or f"cosmic-ray.{suffix}.toml"
    session_path = session_path or f"cosmic-ray.{suffix}.sqlite"
    html_report_path = html_report_path or f"cosmic-ray-report-{suffix}.html"

    # CI should be quiet + not open GUI stuff
    if progress_every_s is None:
        progress_every_s = 10 if env == "ci" else 5
    if open_browser is None:
        open_browser = env == "local"

    config = Path(config_path)
    session = Path(session_path)
    report = Path(html_report_path)

    # 1) init
    rc = run(["cosmic-ray", "init", "--force", str(config), str(session)]).returncode
    if rc != 0:
        raise SystemExit(rc)

    # 2) exec
    proc = Popen(["cosmic-ray", "exec", str(config), str(session)])

    stop = threading.Event()

    def _progress_watcher() -> None:
        last_line = ""
        while not stop.is_set():
            time.sleep(progress_every_s)
            if proc.poll() is not None:
                return

            r = run(["cr-report", str(session)], capture_output=True, text=True)
            out = _clean_report_text((r.stdout or "") + "\n" + (r.stderr or ""))

            total_m = _TOTAL_RE.search(out)
            comp_m = _COMPLETE_RE.search(out)
            surv_m = _SURV_RE.search(out)

            if not (total_m and comp_m):
                # Don't spam if parsing fails
                continue

            total = int(total_m.group(1))
            complete = int(comp_m.group(1))
            pct = float(comp_m.group(2))

            surviving = int(surv_m.group(1)) if surv_m else None

            # Keep CI output minimal: still a single updating line.
            line = f"Cosmic Ray [{env}]: {complete}/{total} ({pct:.2f}%)"
            if surviving is not None:
                line += f" | surviving: {surviving}"

            if line != last_line:
                print("\r" + line.ljust(120), end="", flush=True)
                last_line = line

    t = threading.Thread(target=_progress_watcher, daemon=True)
    t.start()

    rc = proc.wait()
    stop.set()

    # tidy progress line
    print()
    print("\r" + (" " * 120) + "\r", end="", flush=True)

    if rc != 0:
        raise SystemExit(rc)

    # 3) html report
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", encoding="utf-8") as f:
        html_rc = run(["cr-html", str(session)], stdout=f, stderr=DEVNULL).returncode
    if html_rc != 0:
        run(["cr-report", str(session)])
        raise SystemExit(html_rc)

    # 4) open browser only when local (unless overridden)
    if open_browser:
        report_uri = report.resolve().as_uri()
        run([sys.executable, "-m", "webbrowser", report_uri])

    raise SystemExit(0)
