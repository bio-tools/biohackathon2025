"""
Protocol and base classes for pipeline argument models consumed by pipeline run functions.
"""

from .map import MapItem, Method, ModelsMap
from .pipeline_args import PipelineArgs

__all__ = [
    "ModelsMap",
    "Method",
    "PipelineArgs",
    "MapItem",
]
