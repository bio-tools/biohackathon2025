"""
Implements the GitHub→bio.tools metadata pipeline:
derives a BiotoolsToolModel from a GitHubRepoModel.
"""

import logging

from bridge.core import BiotoolsToolModel, GitHubRepoModel
from bridge.pipelines.protocols import PipelineArgs
from bridge.services import ChatMessage, HuggingFaceProvider

logger = logging.getLogger(__name__)


class GitHubToBiotoolsForMetaPipelineArgs(PipelineArgs):
    """
    Pipeline argument model for the GitHub to bio.tools for metadata pipeline.

    Parameters
    ----------
    repo_model : GitHubRepoModel
        The source GitHub repository model.
    existing_metadata : BiotoolsToolModel | None
        Existing bio.tools metadata model, if available. Default is None.
    """

    repo_model: GitHubRepoModel
    existing_metadata: BiotoolsToolModel | None = None


async def run(args: GitHubToBiotoolsForMetaPipelineArgs) -> BiotoolsToolModel:
    """
    Run the pipeline to extract bio.tools metadata from a GitHub repository.

    Parameters
    ----------
    args : GitHubToBiotoolsForMetaPipelineArgs
        The pipeline arguments containing the GitHub repository model and existing bio.tools metadata.

    Returns
    -------
    BiotoolsToolModel
        The extracted or updated bio.tools metadata model.
    """
    logger.info(f"Running GitHub → bio.tools metadata pipeline for repo {args.repo_model.repo.name}")

    github_repo = args.repo_model

    # TODO: Implement actual logic to extract (or update) bio.tools metadata from github_repo

    hf_provider = HuggingFaceProvider()
    message_sys = ChatMessage(
        role="system",
        content=(
            "You are a bioinformatics expert with a precise and to the point writing style."
        ),
    )
    message = ChatMessage(
        role="user",
        content=". Extract a 1-sentence description from this README." +
            github_repo.readme,
    )
    response = await hf_provider.generate([message_sys, message])
    logger.info(f"Generated description from README for repo {github_repo.repo.name}")

    biotools_metadata = BiotoolsToolModel(
        name=github_repo.repo.name,
        description=github_repo.repo.description,
        homepage="pewpew.com",
    )

    logger.info(f"Extracted bio.tools metadata for repo {github_repo.repo.name}")
    return biotools_metadata
