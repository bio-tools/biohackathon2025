"""
Mapping classes for bio.tools to GitHub and vice versa.
"""

from typing import Any

from pydantic import BaseModel

from bridge.pipelines.protocols import Method, ModelsMap


class MapItem(BaseModel):
    """
    Map bio.tools metadata property to corresponding GitHub property and match method.
    """

    bt_entry: Any
    gh_entry: Any
    method: Method | None


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
                bt_entry=self.repo.version, gh_entry=self.metadata, method=Method.EXACT  # releases[].tag_name
            ),
            "topic": MapItem(
                bt_entry=self.repo.topic.term,  # TODO: topic is list of TopicItem
                gh_entry=self.metadata.topics,
                method=Method.EXACT,
            ),
        }
