"""
End-to-end pipelines that implement the bridge’s directional workflows.
Exposes run functions for the pipelines and argument models.
"""

from .bt2gh_for_pr_issues import BiotoolsToGitHubForPRPipelineArgs, run as run_bt2gh_pipeline_for_pr_issues
from .gh2bt_for_meta import GitHubToBiotoolsForMetaPipelineArgs, run as run_gh2bt_pipeline_for_meta
from .goals import PipelineGoal

__all__ = [
    "PipelineGoal",
    "run_bt2gh_pipeline_for_pr_issues",
    "BiotoolsToGitHubForPRPipelineArgs",
    "run_gh2bt_pipeline_for_meta",
    "GitHubToBiotoolsForMetaPipelineArgs",
]
