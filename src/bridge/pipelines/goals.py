"""
Enumeration of supported pipeline goals used to bind handlers to pipeline implementations.
"""

from enum import Enum


class PipelineGoal(str, Enum):
    """
    Enumeration of possible pipeline goals.

    Attributes
    ----------
    CREATE_PR_ISSUES : str
        Goal to create a pull request and issues in a repository based on source metadata.
    EXTRACT_METADATA : str
        Goal to extract metadata from a repository.
    """

    CREATE_PR_ISSUES = "create_pr_issues"
    EXTRACT_METADATA = "extract_metadata"
