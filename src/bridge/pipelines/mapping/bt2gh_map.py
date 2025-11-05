"""
Mapping classes for bio.tools to GitHub and vice versa.
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
            "name": MapItem(schema_entry=self.repo.name, repo_entry=self.metadata.name, method=Method.EXACT),
            "homepage": MapItem(
                schema_entry=self.repo.homepage, repo_entry=self.metadata.homepage, method=Method.EXACT
            ),
            "version": MapItem(
                schema_entry=self.repo.version,
                repo_entry=self.metadata,
                method=Method.EXACT,  # TODO: releases[].tag_name
            ),
            "topic": MapItem(
                schema_entry=[ti.term for ti in self.repo.topic],
                repo_entry=self.metadata.topics,
                method=Method.SUBSET,
            ),
        }
