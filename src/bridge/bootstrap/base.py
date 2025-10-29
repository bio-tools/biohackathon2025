"""
Core in-memory registries and helpers for registration and lookup of schemas, repo providers, and pipeline bindings.
This is the dependency map the handlers and pipelines rely on.
"""

from bridge.pipelines import PipelineGoal
from bridge.pipelines.protocols import PipelineArgs
from bridge.services.protocols import RepoProvider

# -------------------------------
# Data structures
# -------------------------------


class SchemaRegistration:
    """
    Holds the composer function for a given schema.

    Parameters
    ----------
    composer : callable
        Function that composes metadata models for the schema.
    """

    def __init__(self, composer: callable):
        self.composer = composer


class RepoRegistration:
    """
    Holds the composer function and type[RepoProvider] class for a given repo type.

    Parameters
    ----------
    composer : callable
        Function that composes repo models.
    provider_cls : type[RepoProvider]
        The type[RepoProvider] class for providing repository interactions.
    """

    def __init__(self, composer: callable, provider_cls: type[RepoProvider]):
        self.composer = composer
        self.provider_cls = provider_cls


class BridgeRegistration:
    """
    Holds the mapping between PipelineGoals and their
    corresponding pipeline functions and argument models.

    Parameters
    ----------
    pipelines : dict[PipelineGoal, tuple[callable, type[PipelineArgs]]]
        Each entry maps a PipelineGoal to (pipeline_function, args_model_class).
    """

    def __init__(self, pipelines: dict[PipelineGoal, tuple[callable, type[PipelineArgs]]]):
        self.pipelines = pipelines


# -------------------------------
# Global registries
# -------------------------------

_schema_registry: dict[str, SchemaRegistration] = {}
_repo_registry: dict[str, RepoRegistration] = {}
_bridge_registry: dict[tuple[str, str], BridgeRegistration] = {}
_handler_registry: dict[PipelineGoal, callable] = {}


# -------------------------------
# Registration functions
# -------------------------------


def register_schema(schema: str, *, composer: callable):
    """
    Register a schema with its composer function.

    Parameters
    ----------
    schema : str
        The name of the schema to register (e.g., "biotools").
    composer : callable
        Function that composes metadata models for the schema.
    """
    _schema_registry[schema] = SchemaRegistration(composer)


def register_repo(repo_type: str, *, composer: callable, provider_cls: type[RepoProvider]):
    """
    Register a repository type with its composer function and type[RepoProvider] class.

    Parameters
    ----------
    repo_type : str
        The type of the repository to register (e.g., "github").
    composer : callable
        Function that composes repo models.
    provider_cls : type[RepoProvider]
        The type[RepoProvider] class for providing repository interactions.
    """
    _repo_registry[repo_type] = RepoRegistration(composer, provider_cls)


def register_bridge(
    schema: str,
    repo_type: str,
    *,
    pipelines: dict[PipelineGoal, tuple[callable, type[PipelineArgs]]],
):
    """
    Register the mapping between a schema and repo type to their pipelines.

    Parameters
    ----------
    schema : str
        The name of the schema (e.g., "biotools").
    repo_type : str
        The type of the repository (e.g., "github").
    pipelines : dict[PipelineGoal, tuple[callable, type[PipelineArgs]]]
        Each entry maps a PipelineGoal to (pipeline_function, args_model_class).
    """
    _bridge_registry[(schema, repo_type)] = BridgeRegistration(pipelines)


def get_schema_composer(schema: str) -> callable:
    """
    Retrieve the composer function for a given schema.

    Parameters
    ----------
    schema : str
        The name of the schema (e.g., "biotools").

    Returns
    -------
    callable
        The composer function for the schema.
    """
    try:
        return _schema_registry[schema].composer
    except KeyError as e:
        raise NotImplementedError(f"No composer registered for schema: {schema}") from e


def get_repo_components(repo_type: str) -> tuple[callable, type[RepoProvider]]:
    """
    Retrieve the (composer_function, RepoProviderClass) tuple for a given repo type.

    Parameters
    ----------
    repo_type : str
        The type of the repository (e.g., "github").

    Returns
    -------
    tuple[callable, type[RepoProvider]]
        The (composer_function, RepoProviderClass) for the repo type.
    """
    try:
        reg = _repo_registry[repo_type]
        return reg.composer, reg.provider_cls
    except KeyError as e:
        raise NotImplementedError(f"No repo registered for type: {repo_type}") from e


def get_pipeline(schema: str, repo_type: str, goal: PipelineGoal) -> tuple[callable, type[PipelineArgs]]:
    """
    Retrieve the pipeline function and argument model for a given schema, repo_type, and goal.

    Parameters
    ----------
    schema : str
        The name of the schema (e.g., "biotools").
    repo_type : str
        The type of the repository (e.g., "github").
    goal : PipelineGoal
        The pipeline goal.

    Returns
    -------
    tuple[callable, type[PipelineArgs]]
        The (pipeline_function, args_model_class) for the specified combination.
    """
    try:
        reg = _bridge_registry[(schema, repo_type)]
        pipeline_entry = reg.pipelines[goal]
        return pipeline_entry
    except KeyError as e:
        raise NotImplementedError(f"No pipeline registered for ({schema}, {repo_type}, {goal})") from e


def get_handler(goal: PipelineGoal) -> callable:
    """
    Retrieve the handler function for a specific pipeline goal.

    Parameters
    ----------
    goal : PipelineGoal
        The pipeline goal.

    Returns
    -------
    callable
        The handler function for the specified goal.
    """
    try:
        return _handler_registry[goal]
    except KeyError as e:
        raise NotImplementedError(f"No handler registered for goal: {goal}") from e
