"""
CLI command to create a GitHub pull request from a bio.tools record.
"""

import asyncio
import logging

import typer

from bridge.handlers import create_pr_issues_from_meta

logger = logging.getLogger(__name__)

app = typer.Typer(help="bio.tools -> GitHub bridge")


@app.command("pr")
def pr(
    biotools_id: str = typer.Argument(..., help="The ID of the source bio.tools entry."),
    owner: str = typer.Argument(..., help="The owner of the GitHub repository to create the PR in."),
    repo: str = typer.Argument(..., help="The name of the GitHub repository to create the PR in."),
    allow_issues: bool | None = typer.Option(None, help="Whether to create issues in the repository."),
):
    """
    Create a GitHub PR from bio.tools metadata.

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
    logger.info(f"Creating PR for {owner}/{repo} from bio.tools:{biotools_id}")

    async def _run():
        result = await create_pr_issues_from_meta(
            schema="biotools",
            repo_type="github",
            identifier=biotools_id,
            owner=owner,
            repo=repo,
            allow_issues=allow_issues,
        )
        typer.echo(result)

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error(f"Failed to create PR from bio.tools metadata: {e}")
        typer.echo(f"Failed to create PR from bio.tools metadata: {e}", err=True)
