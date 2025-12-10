"""
Handler for 'create pull request from metadata'.
Opens a PR in a repository based on metadata from a specified schema.
"""

import logging
import time
import uuid

from bridge.bootstrap import (
    get_pipeline,
    get_repo_components,
    get_schema_composer,
    register_handler,
)
from bridge.pipelines import PipelineGoal
from bridge.utils import require_args

logger = logging.getLogger(__name__)


def _unique_branch_name(prefix: str = "update") -> str:
    """
    Generate a unique branch name using the given prefix.

    Parameters
    ----------
    prefix : str
        The prefix for the branch name.

    Returns
    -------
    str
        A unique branch name.
    """
    timestamp = int(time.time())
    rnd = uuid.uuid4().hex[:6]
    return f"{prefix}/{timestamp}-{rnd}"


@require_args("owner", "repo", "identifier")
@register_handler(PipelineGoal.CREATE_PR)
async def create_pr_issues_from_meta(schema: str, repo_type: str, **kwargs):
    """
    Create a pull request and issues in the repository based on the metadata.

    Parameters
    ----------
    schema : str
        The metadata schema to use (e.g., "biotools").
    repo_type : str
        The type of repository (e.g., "github").
    **kwargs
        Additional keyword arguments required by the composers, provider, and pipeline.

        For schema="biotools", repo_type="github":
        - owner: str - The owner of the repository where the PR will be created.
        - repo: str - The name of the repository where the PR will be created.
        - identifier: str - Identifier for the source metadata in bio.tools.
    """
    logger.info(
        f"Creating PR and issues in {repo_type} repo {kwargs.get('owner')}/{kwargs.get('repo')} "
        f"from {schema} metadata ID {kwargs.get('identifier')}"
    )

    owner = kwargs["owner"]
    repo = kwargs["repo"]
    identifier = kwargs["identifier"]

    metadata_composer = get_schema_composer(schema)
    repo_composer, repo_provider = get_repo_components(repo_type)
    pipeline, args_model = get_pipeline(schema, repo_type, PipelineGoal.CREATE_PR)

    if not repo_provider:
        raise ValueError(f"No provider found for repo type: {repo_type}")

    metadata = await metadata_composer(**kwargs)
    repo_model = await repo_composer(**kwargs)
    repo_provider = repo_provider()

    fork = await repo_provider.fork(kwargs["owner"], kwargs["repo"])

    with repo_provider.clone_context(fork.full_name) as cloned_repo:
        pipeline_kwargs = {
            "existing_repo_model": repo_model,
            "repo_path": cloned_repo,
            "metadata_model": metadata,
        }
        merged_kwargs = {**pipeline_kwargs, **kwargs}
        pipeline_args = args_model(**merged_kwargs)
        file_changes, issues = await pipeline(pipeline_args)

        output = {"pr": None, "issues": None}

        pr = {}
        if file_changes:
            branch = _unique_branch_name()
            repo_provider.apply_changes_and_push(cloned_repo, branch, file_changes)
            pr = await repo_provider.create_pull_request(
                owner=owner,
                repo=repo,
                title=f"Update from {schema}",
                body=f"Auto-generated PR from {schema} ID {identifier}.",
                head_branch=f"{fork.owner}:{branch}",
                base_branch=repo_model.repo.default_branch,
            )
            output["pr"] = pr
            logger.info(f"Created PR for {owner}/{repo}: {pr.get('html_url')}")

        allow_issues = kwargs.get("allow_issues", None)

        if allow_issues and issues:
            created_issues = []
            for title, body in issues.items():
                created_issue = await repo_provider.create_issue(
                    owner=owner,
                    repo=repo,
                    title=title,
                    body=body,
                )
                created_issues.append(created_issue)
                logger.info(f"Created issue for {owner}/{repo}: {created_issue.get('html_url')}")
            output["issues"] = created_issues

        return output
