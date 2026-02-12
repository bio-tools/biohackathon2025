"""
Mapping classes for bio.tools to GitHub.
"""

from pathlib import Path

from pydantic import BaseModel

from bridge.pipelines.protocols import MapItem, Method, ModelsMap
from bridge.pipelines.utils import load_dict_from_yaml_file

from .map_funcs import (
    map_citation,
    map_description,
    map_functions,
    map_homepage,
    map_license,
    map_name,
    map_readme,
    map_topics,
    map_version,
)


class MapDestination(BaseModel):
    """
    Set destination (issue or PR) for each mapped property.

    Parameters
    ----------
    issue : list[str]
        List of properties to be mapped to issues.
    pr : list[str]
        List of properties to be mapped to pull requests.
    """

    issue: list[str] = ["name", "description", "homepage", "topics", "version", "functions"]
    pr: list[str] = ["citation", "readme", "license"]


class MapBioTools2GitHub(ModelsMap):
    """
    Map bio.tools metadata record to GitHub
    """

    def __init__(self, repo, metadata, repo_path: str):
        super().__init__(repo=repo, metadata=metadata)
        self.repo_path = Path(repo_path)

    @property
    def map(self) -> dict[str, MapItem]:
        """
        Map bio.tools metadata property to corresponding GitHub property.
        """
        return {
            "name": MapItem(
                schema_entry={
                    "name": self.metadata.name,
                    "biotoolsID": self.metadata.biotoolsID.root,
                },
                repo_entry=self.repo.repo.name,
                method=Method.EXACT,
                fn=map_name,
            ),
            "version": MapItem(
                schema_entry=self.metadata.version,
                repo_entry=self.repo.latest_release.tag_name,
                method=Method.EXACT,
                fn=map_version,
            ),
            "description": MapItem(
                schema_entry=self.metadata.description,
                repo_entry=self.repo.repo.description,
                method=Method.EXACT,
                fn=map_description,
            ),
            "citation": MapItem(
                schema_entry={
                    "publication": self.metadata.publication,
                    "name": self.metadata.name,
                    "biotoolsID": self.metadata.biotoolsID,
                    "homepage": self.metadata.homepage,
                    "license": self.metadata.license,
                    "topic": self.metadata.topic,
                    "description": self.metadata.description,
                },
                repo_entry=load_dict_from_yaml_file(self.repo_path / "CITATION.cff"),
                method=Method.FUZZY,
                fn=map_citation,
            ),
            "topics": MapItem(
                schema_entry={"topics": self.metadata.topic, "functions": self.metadata.function},
                repo_entry=self.repo.repo.topics,
                method=Method.FUZZY,
                fn=map_topics,
            ),
            # TODO: function2readme
            "homepage": MapItem(
                schema_entry=self.metadata.homepage,
                repo_entry={"homepage": self.repo.repo.homepage, "html_url": self.repo.repo.html_url},
                method=Method.EXACT,
                fn=map_homepage,
            ),
            "readme": MapItem(
                schema_entry={
                    "name": self.metadata.name,
                    "biotoolsID": self.metadata.biotoolsID.root,
                    "toolType": self.metadata.toolType,
                    "function": self.metadata.function,
                },
                repo_entry=self.repo.readme,
                method=Method.FUZZY,
                fn=map_readme,
            ),
            "license": MapItem(
                schema_entry=self.metadata.license,
                repo_entry=self.repo.repo.license,
                method=Method.FUZZY,
                fn=map_license,
            ),
            "functions": MapItem(
                schema_entry=self.metadata.function,
                repo_entry=self.repo.readme,
                method=Method.FUZZY,
                fn=map_functions,
            ),
        }
