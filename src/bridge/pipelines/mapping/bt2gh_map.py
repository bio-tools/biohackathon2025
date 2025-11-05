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
            "name": MapItem(bt_entry=self.repo.name, gh_entry=self.metadata.name, method=Method.EXACT),
            "homepage": MapItem(bt_entry=self.repo.homepage, gh_entry=self.metadata.homepage, method=Method.EXACT),
            "version": MapItem(
                bt_entry=self.repo.version, gh_entry=self.metadata, method=Method.EXACT  # TODO: releases[].tag_name
            ),
            "topic": MapItem(
                bt_entry=[ti.term for ti in self.repo.topic],
                gh_entry=self.metadata.topics,
                method=Method.SUBSET,
            ),
        }
