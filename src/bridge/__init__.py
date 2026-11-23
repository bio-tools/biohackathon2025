"""
The main bridge package: a bidirectional modular framework for integration between
(GitHub) repositories and (bio.tools) metadata.
"""

from importlib.metadata import PackageNotFoundError, version

from bridge.logging import setup_logging

from .handlers import create_pr_issues_from_meta, extract_meta_from_repo

try:
    __version__ = version("metadata-bridge")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0"

setup_logging("package")

__all__ = [
    "__version__",
    "extract_meta_from_repo",
    "create_pr_issues_from_meta",
]
