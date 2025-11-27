"""
Mapping classes for bio.tools to GitHub.
"""

from pydantic import BaseModel

from bridge.pipelines.protocols import MapItem, Method, ModelsMap
from bridge.pipelines.utils import check_file_with_extension_exists

from .map_funcs import map_citation, map_description, map_edam2topics, map_homepage, map_readme


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

    issue: list[str] = ["description", "homepage", "topics"]
    pr: list[str] = ["citation", "readme"]


class MapBioTools2GitHub(ModelsMap):
    """
    Map bio.tools metadata record to GitHub
    """

    def __init__(self, repo, metadata, repo_path: str):
        super().__init__(repo=repo, metadata=metadata)
        self.repo_path = repo_path

    @property
    def map(self) -> dict[str, MapItem]:
        """
        Map bio.tools metadata property to corresponding GitHub property.
        """
        return {
            "name": MapItem(schema_entry=self.metadata.name, repo_entry=self.repo.repo.name, method=Method.EXACT),
            "version": MapItem(
                schema_entry=self.metadata.latest_release.tag_name,
                repo_entry=self.repo.version,
                method=Method.EXACT,
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
                repo_entry=check_file_with_extension_exists(
                    in_folder_path=self.repo_path,
                    file_extension=".cff",
                ),
                method=Method.FUZZY,
                fn=map_citation,
            ),
            "topics": MapItem(
                schema_entry={"topics": self.metadata.topic, "functions": self.metadata.function},
                repo_entry=self.repo.repo.topics,
                method=Method.FUZZY,
                fn=map_edam2topics,
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
                },
                repo_entry=self.repo.readme,
                method=Method.FUZZY,
                fn=map_readme,
            ),
        }
