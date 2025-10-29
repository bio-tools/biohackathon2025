"""
Generate Sphinx API documentation.
This script is a part of CI documentation generation.

Run via:
    poetry run generate-docs
"""

import shutil
import subprocess
import sys
from pathlib import Path

DOCS_DIR = Path("docs")
SOURCE_DIR = DOCS_DIR / "source"
BUILD_DIR = DOCS_DIR / "build"
GENERATED_DIRS = [SOURCE_DIR / "_generated", SOURCE_DIR / "api_reference" / "_apidoc_generated"]


def clean_docs():
    """Remove previous build and generated files."""
    targets = [BUILD_DIR] + GENERATED_DIRS

    for path in targets:
        if path.exists():
            print(f"Removing {path}...")
            shutil.rmtree(path, ignore_errors=True)


def build_docs():
    """Build final HTML docs."""
    build_cmd = [
        "sphinx-build",
        "-b",
        "html",
        str(SOURCE_DIR),
        str(DOCS_DIR / "build"),
        "-q",
    ]
    print(f"Building HTML: {' '.join(build_cmd)}")
    subprocess.run(build_cmd, check=True, stderr=subprocess.DEVNULL)
    print("Docs built successfully.")


def main():
    """Generate docs."""
    if not SOURCE_DIR.is_dir():
        sys.exit(f"Docs source directory not found: {SOURCE_DIR}")

    clean_docs()
    build_docs()


if __name__ == "__main__":
    main()
