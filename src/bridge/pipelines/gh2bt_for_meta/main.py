"""
Implements the GitHub→bio.tools metadata pipeline:
derives a BiotoolsToolModel from a GitHubRepoModel.
"""

import base64
import logging
import urllib

from bridge.core import BiotoolsToolModel, GitHubRepoModel
from bridge.pipelines.protocols import PipelineArgs

from .map import MapGitHub2BioTools

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

    # hf_provider = HuggingFaceProvider()
    # message_sys = ChatMessage(
    #     role="system",
    #     content=(
    #         "You are a Star Trek expert. Respond only to the current user message. "
    #         "Keep your response to a single, self-contained, metaphorical sentence. "
    #         "Do not ask questions. Do not continue the conversation. Do not add extra explanation."
    #     ),
    # )
    # message = ChatMessage(
    #     role="user",
    #     content="Explain quantum entanglement in one sentence using metaphors a Klingon warrior would understand.",
    # )
    # response = await hf_provider.generate([message_sys, message])

    mapper = MapGitHub2BioTools(
        repo=github_repo,
        metadata=args.existing_metadata,
    )

    biotools_metadata = BiotoolsToolModel(
        name=github_repo.repo.name,
        description=await mapper.map["description"].run(),
        homepage=mapper.map["homepage"].run(),
        maturity=mapper.map["maturity"].run(),
    )

    biotools_url = "https://bio-tools-dev.sdu.dk"

    logger.info(f"Extracted bio.tools metadata for repo {github_repo.repo.name}")
    logger.info(
        f"\n\n*** 🛠  Want to create a bio.tools entry for this repo? ***\n"
        f"🚀 (1) Log in to {biotools_url}\n"
        f"✨ (2) click the following link:\n\n{biotools_url}/register"
        f"?json={urllib.parse.quote(base64.b64encode(biotools_metadata.model_dump_json().encode('ascii')))} \n"
    )
    return biotools_metadata
