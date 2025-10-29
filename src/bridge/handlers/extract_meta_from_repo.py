"""
Handler for 'extract metadata from repository'.
Builds a repo model (and optional existing metadata) and returns the extracted metadata.
"""

import logging

from bridge.bootstrap import (
    get_pipeline,
    get_repo_components,
    get_schema_composer,
    register_handler,
)
from bridge.pipelines import PipelineGoal
from bridge.utils import require_args

logger = logging.getLogger(__name__)


@require_args("owner", "repo")
@register_handler(PipelineGoal.EXTRACT_METADATA)
async def extract_meta_from_repo(schema: str, repo_type: str, **kwargs) -> str:
    """
    Extract metadata from a repository.

    Parameters
    ----------
    schema : str
        The metadata schema to extract (e.g., "biotools").
    repo_type : str
        The type of repository (e.g., "github").
    **kwargs
        Additional keyword arguments required by the composers and pipeline.

        For schema="biotools", repo_type="github":
        - owner: str - The owner of the source repository.
        - repo: str - The name of the source repository.
        - identifier: str | None - Optional identifier for existing metadata in bio.tools.

    Returns
    -------
    str
        The extracted metadata in JSON format.
    """
    logger.info(
        f"Extracting {schema} metadata from {repo_type} repo {kwargs.get('owner')}/{kwargs.get('repo')} "
        f"with identifier {kwargs.get('identifier')}"
    )

    metadata_composer = get_schema_composer(schema)
    repo_composer, _ = get_repo_components(repo_type)
    pipeline, args_model = get_pipeline(schema, repo_type, PipelineGoal.EXTRACT_METADATA)

    repo_model = await repo_composer(**kwargs)
    identifier = kwargs.get("identifier")
    metadata = await metadata_composer(**kwargs) if identifier else None

    pipeline_kwargs = {
        "repo_model": repo_model,
        "existing_metadata": metadata,
    }
    merged_kwargs = {**pipeline_kwargs, **kwargs}
    pipeline_args = args_model(**merged_kwargs)
    result = await pipeline(pipeline_args)

    result_json = result.model_dump_json(exclude_none=True, indent=2)
    logger.info(
        f"Extracted {schema} metadata from {repo_type} repo {kwargs.get('owner')}/{kwargs.get('repo')} successfully"
    )
    return result_json
