"""
Default wiring for the bridge: registers the bio.tools schema, the GitHub repo provider, and both directional pipelines.
Idempotent and guarded by bootstrap.state.
"""

import logging

from bridge.builders import compose_biotools_metadata, compose_github_repo
from bridge.pipelines import (
    BiotoolsToGitHubForPRPipelineArgs,
    GitHubToBiotoolsForMetaPipelineArgs,
    PipelineGoal,
    run_bt2gh_pipeline_for_pr,
    run_gh2bt_pipeline_for_meta,
)
from bridge.services import GitHubRepoProvider

from .base import register_bridge, register_repo, register_schema
from .state import is_initialized, mark_initialized

logger = logging.getLogger(__name__)


def wiring(force: bool = False):
    """
    Initialize the registry with schemas, repositories, and bridges.

    Parameters
    ----------
    force : bool, optional
        If True, forces re-initialization even if already initialized. Defaults to False.
    """
    if is_initialized() and not force:
        logger.info("Registry already initialized; skipping.")
        return

    register_schema("biotools", composer=compose_biotools_metadata)
    register_repo("github", composer=compose_github_repo, provider_cls=GitHubRepoProvider)
    register_bridge(
        "biotools",
        "github",
        pipelines={
            PipelineGoal.CREATE_PR: (run_bt2gh_pipeline_for_pr, BiotoolsToGitHubForPRPipelineArgs),
            PipelineGoal.EXTRACT_METADATA: (run_gh2bt_pipeline_for_meta, GitHubToBiotoolsForMetaPipelineArgs),
        },
    )
    logger.info("Registry initialization completed.")
    mark_initialized()
