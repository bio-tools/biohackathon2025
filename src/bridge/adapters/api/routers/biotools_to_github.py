"""
Endpoint to create a GitHub pull request from a bio.tools record.
"""

import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bridge.handlers import create_pr_issues_from_meta

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bio.tools -> GitHub bridge"])


class BioToolsToGitHubPayload(BaseModel):
    """
    Payload for creating a GitHub PR from bio.tools metadata.

    Parameters
    ----------
    biotools_id : str
        The ID of the source bio.tools entry.
    owner : str
        The owner of the GitHub repository to create the PR in.
    repo : str
        The name of the GitHub repository to create the PR in.
    allow_issues : bool | None
        Whether to create issues in the repository based on bio.tools issues. Default is None.
    """

    biotools_id: str
    owner: str
    repo: str
    allow_issues: bool | None = None


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a GitHub PR from bio.tools metadata",
    description="Create a GitHub PR from bio.tools metadata",
)
async def biotools_to_github_pr_issues(payload: BioToolsToGitHubPayload):
    """
    Create a GitHub PR from bio.tools metadata.

    Parameters
    ----------
    payload : BioToolsToGitHubPayload
        The payload containing bio.tools ID and GitHub repo details.

    Returns
    -------
    JSONResponse
        The response containing PR details.
    """
    logger.info(f"Received PR creation request for {payload.owner}/{payload.repo} from bio.tools:{payload.biotools_id}")
    try:
        pr = await create_pr_issues_from_meta(
            schema="biotools",
            repo_type="github",
            identifier=payload.biotools_id,
            owner=payload.owner,
            repo=payload.repo,
            allow_issues=payload.allow_issues,
        )
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=pr)
    except Exception as e:
        logger.exception(f"Failed to create PR from bio.tools metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create PR from bio.tools metadata: {e}") from e
