"""
The main bridge package: a bidirectional modular framework for integration between
(GitHub) repositories and (bio.tools) metadata.
"""

from bridge.logging import setup_logging

from .handlers import create_pr_issues_from_meta, extract_meta_from_repo

setup_logging("package")

__all__ = [
    "extract_meta_from_repo",
    "create_pr_issues_from_meta",
]
