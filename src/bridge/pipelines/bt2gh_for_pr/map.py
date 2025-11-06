"""
Mapping classes for bio.tools to GitHub.
"""

from pydantic import BaseModel

from bridge.pipelines.protocols import MapItem, Method, ModelsMap

from .map_funcs import map_citation, map_description


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

    issue: list[str] = ["description"]
    pr: list[str] = ["citation"]


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
            "homepage": MapItem(
                schema_entry=self.metadata.homepage, repo_entry=self.repo.homepage, method=Method.EXACT
            ),
            "version": MapItem(
                schema_entry=self.metadata.version,
                repo_entry=self.repo.latest_release.tag_name,
                method=Method.EXACT,
            ),
            "topic": MapItem(
                schema_entry=self.metadata.topic,
                repo_entry=[ti.term for ti in self.repo.repo.topics],
                method=Method.SUBSET,
            ),
            "description": MapItem(
                schema_entry=self.metadata.description,
                repo_entry=self.repo.repo.description,
                method=Method.EXACT,
                fn=map_description,
            ),
            "citation": MapItem(
                schema_entry={},
                repo_entry=self.repo.citation,
                method=Method.FUZZY,
                fn=map_citation,
            ),
        }
