"""
Mapping classes for bio.tools to GitHub.
"""

from bridge.pipelines.protocols import MapItem, Method, ModelsMap


class MapBioTools2GitHub(ModelsMap):
    """
    Map bio.tools metadata record to GitHub
    """

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
                schema_entry=self.metadata.description, repo_entry=self.repo.repo.description, method=Method.EXACT
            ),
        }
