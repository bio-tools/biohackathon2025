"""
Implements the bio.tools→GitHub PR pipeline:
given a checkout path and a BiotoolsToolModel,
produce file changes to propose in a pull request.
"""

import logging

from bridge.core import BiotoolsToolModel
from bridge.pipelines.protocols import PipelineArgs
from bridge.services import ChatMessage, HuggingFaceProvider

logger = logging.getLogger(__name__)


class BiotoolsToGitHubForPRPipelineArgs(PipelineArgs):
    """
    Pipeline argument model for the bio.tools to GitHub for PR pipeline.

    Parameters
    ----------
    repo_path : str
        Path to the cloned GitHub repository to make changes in.
    metadata_model : BiotoolsToolModel
        The source bio.tools metadata model.
    """

    repo_path: str
    metadata_model: BiotoolsToolModel


async def run(args: BiotoolsToGitHubForPRPipelineArgs) -> tuple[dict, dict]:
    """
    Run the pipeline to generate repository file changes based on bio.tools metadata.

    Parameters
    ----------
    args: BiotoolsToGitHubForPRPipelineArgs
        The pipeline arguments containing a path to the cloned GitHub repository and metadata model.

    Returns
    -------
    tuple[dict, dict]
        A dictionary mapping file paths to their new content, and
        a dictionary mapping issue titles to their bodies.
    """
    logger.info(f"Running bio.tools → GitHub PR pipeline for {args.metadata_model.name}")

    repo_path = args.repo_path
    biotools_model = args.metadata_model

    # TODO: Implement actual logic to generate file changes based on biotools_model

    hf_provider = HuggingFaceProvider()
    message_sys = ChatMessage(
        role="system",
        content=(
            "You are a Star Trek expert. Respond only to the current user message. "
            "Keep your response to a single, self-contained, metaphorical sentence. "
            "Do not ask questions. Do not continue the conversation. Do not add extra explanation."
        ),
    )
    message = ChatMessage(
        role="user",
        content="Explain quantum entanglement in one sentence using metaphors a Klingon warrior would understand.",
    )
    response = await hf_provider.generate([message_sys, message])

    file_changes = {"README.md": f"pew pew {biotools_model.name}\n{response.content}"}
    issues = {"issue pew pew": "Pew pew issue body"}

    logger.info(f"Generated file changes for repo at {repo_path}: {file_changes.keys()}")
    return file_changes, issues
