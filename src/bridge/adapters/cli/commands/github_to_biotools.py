"""
CLI command to extract bio.tools metadata from a GitHub repository.
"""

import asyncio
import logging

import typer

from bridge.handlers import extract_meta_from_repo

logger = logging.getLogger(__name__)

app = typer.Typer(help="GitHub -> bio.tools bridge.")


@app.command("extract")
def extract(
    owner: str = typer.Argument(..., help="The owner of the source GitHub repository."),
    repo: str = typer.Argument(..., help="The name of the source GitHub repository."),
    biotools_id: str | None = typer.Option(None, help="Existing bio.tools ID to update (optional)."),
):
    """
    Extract bio.tools metadata from a GitHub repository.

    Parameters
    ----------
    owner : str
        The owner of the source GitHub repository.
    repo : str
        The name of the source GitHub repository.
    biotools_id : Optional[str]
        Existing bio.tools ID to update, if available.
    """
    logger.info(f"Extracting metadata for {owner}/{repo} to bio.tools:{biotools_id}")

    async def _run():
        result = await extract_meta_from_repo(
            schema="biotools",
            repo_type="github",
            owner=owner,
            repo=repo,
            identifier=biotools_id,
        )
        typer.echo(result)

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error(f"Failed to extract metadata from GitHub repository: {e}")
        typer.echo(f"Failed to extract metadata from GitHub repository: {e}", err=True)
