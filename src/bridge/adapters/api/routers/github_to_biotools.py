"""
Endpoint to extract bio.tools metadata from a GitHub repository.
"""

import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bridge.handlers import extract_meta_from_repo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["GitHub -> bio.tools bridge"])


class GitHubToBioToolsPayload(BaseModel):
    """
    Payload for extracting bio.tools metadata from a GitHub repository.

    Parameters
    ----------
    owner : str
        The owner of the source GitHub repository.
    repo : str
        The name of the source GitHub repository.
    biotools_id : Optional[str]
        Existing bio.tools ID to update, if available.
    """

    owner: str
    repo: str
    biotools_id: str | None = None


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Extract bio.tools metadata from a GitHub repository",
    description="Extract bio.tools metadata from a GitHub repository",
)
async def github_to_biotools(payload: GitHubToBioToolsPayload):
    """
    Extract bio.tools metadata from a GitHub repository.

    Parameters
    ----------
    payload : GitHubToBioToolsPayload
        The payload containing GitHub repo details and optional existing bio.tools ID.
    """
    logger.info(
        f"Received metadata extraction request for {payload.owner}/{payload.repo} to bio.tools:{payload.biotools_id}"
    )
    try:
        metadata = await extract_meta_from_repo(
            schema="biotools",
            repo_type="github",
            owner=payload.owner,
            repo=payload.repo,
            identifier=payload.biotools_id,
        )
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=metadata)
    except Exception as e:
        logger.error(f"Failed to extract metadata from GitHub repository: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract metadata from GitHub repository: {e}") from e
