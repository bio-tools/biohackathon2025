"""
Quality-related scripts: linting and formatting.
"""

import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from subprocess import DEVNULL, Popen, run


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


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

_TOTAL_RE = re.compile(r"Total\s+jobs:\s*(\d+)", re.IGNORECASE)
_COMPLETE_RE = re.compile(r"Complete:\s*(\d+)\s*\(([\d.]+)%\)", re.IGNORECASE)
_SURV_RE = re.compile(r"Surviving\s+mutants:\s*(\d+)\s*\(([\d.]+)%\)", re.IGNORECASE)


def _clean_report_text(s: str) -> str:
    s = s or ""
    s = _ANSI_RE.sub("", s)
    return s


def cosmic_ray_report(
    config_path: str = "cosmic-ray.toml",
    session_path: str = "cosmic-ray.sqlite",
    html_report_path: str = "cosmic-ray-report.html",
    progress_every_s: int = 5,
) -> None:
    """
    Run Cosmic Ray mutation testing with live progress reporting and HTML report generation.
    """
    config = Path(config_path)
    session = Path(session_path)
    report = Path(html_report_path)

    rc = run(["cosmic-ray", "init", "--force", str(config), str(session)]).returncode
    if rc != 0:
        raise SystemExit(rc)

    proc = Popen(["cosmic-ray", "exec", str(config), str(session)])

    stop = threading.Event()

    def _progress_watcher() -> None:
        last_line = ""

        while not stop.is_set():
            time.sleep(progress_every_s)
            if proc.poll() is not None:
                return

            # Cosmic Ray explicitly supports querying progress during exec.
            r = run(["cr-report", str(session)], capture_output=True, text=True)
            out = _clean_report_text((r.stdout or "") + "\n" + (r.stderr or ""))

            total_m = _TOTAL_RE.search(out)
            comp_m = _COMPLETE_RE.search(out)
            surv_m = _SURV_RE.search(out)

            if not (total_m and comp_m):
                # Stay quiet by default (no spam).
                # Uncomment if you want one-time visibility:
                # if not warned_unparseable:
                #     print("\n[debug] Could not parse cr-report output. First 300 chars:\n" + out[:300])
                #     warned_unparseable = True
                continue

            total = int(total_m.group(1))
            complete = int(comp_m.group(1))
            pct = float(comp_m.group(2))

            surviving = None
            if surv_m:
                surviving = int(surv_m.group(1))

            status = "running..."
            line = f"Cosmic Ray: {complete}/{total} ({pct:.2f}%)"
            if surviving is not None:
                line += f" | surviving: {surviving}"
            line += f" | {status}"

            # print as a single updating line
            if line != last_line:
                print("\r" + line.ljust(120), end="", flush=True)
                last_line = line

    t = threading.Thread(target=_progress_watcher, daemon=True)
    t.start()

    rc = proc.wait()
    stop.set()
    print()  # newline after the \r progress line
    print("\r" + (" " * 120) + "\r", end="", flush=True)

    if rc != 0:
        raise SystemExit(rc)

    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", encoding="utf-8") as f:
        html_rc = run(["cr-html", str(session)], stdout=f, stderr=DEVNULL).returncode
    if html_rc != 0:
        run(["cr-report", str(session)])
        raise SystemExit(html_rc)

    report_uri = report.resolve().as_uri()
    run([sys.executable, "-m", "webbrowser", report_uri])

    raise SystemExit(0)
