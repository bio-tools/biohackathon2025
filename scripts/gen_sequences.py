"""
Generate SVG sequence diagrams from Mermaid `.mmd` files.
Diagrams code location: docs/source/api_reference/sequence/*.mmd
Output SVGs next to the .mmd files (same basename, .svg extension).

Run via:
    poetry run gen-sequence-diagrams
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SEQ_DOCS_DIR = BASE_DIR / "docs" / "source" / "api_reference" / "sequence"


def find_mermaid_files(root: Path) -> list[Path]:
    """Return all .mmd files under `root`."""
    return sorted(root.rglob("*.mmd"))


def render_mermaid_to_svg(mmd_file: Path, mmdc_exe: str) -> None:
    """Render a single .mmd file to .svg using mermaid-cli."""
    svg_file = mmd_file.with_suffix(".svg")

    svg_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"[mermaid] {mmd_file.relative_to(BASE_DIR)} -> {svg_file.relative_to(BASE_DIR)}")

    try:
        subprocess.run(
            [
                mmdc_exe,
                "-i",
                str(mmd_file),
                "-o",
                str(svg_file),
                # Optional tweaks:
                # "--backgroundColor", "transparent",
                # "--scale", "1.0",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Rendered {svg_file}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to render {mmd_file}")
        if e.stderr.strip():
            print("stderr:", e.stderr.strip())
        elif e.stdout.strip():
            print("stdout:", e.stdout.strip())
        else:
            print("(no output)")
        return


def main() -> None:
    """
    Generate SVG sequence diagrams from Mermaid `.mmd` files.
    """
    SEQ_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    mmdc_exe = shutil.which("mmdc")
    if not mmdc_exe:
        print("mmdc (mermaid-cli) not found.")
        print(" • Install: npm install -g @mermaid-js/mermaid-cli")
        return

    files = find_mermaid_files(SEQ_DOCS_DIR)
    if not files:
        print(f"No .mmd files found under {SEQ_DOCS_DIR}")
        return

    for mmd_file in files:
        render_mermaid_to_svg(mmd_file, mmdc_exe)


if __name__ == "__main__":
    main()
