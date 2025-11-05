"""
Mapping classes for GitHub to bio.tools.
"""

from bridge.pipelines.protocols import MapItem, Method, ModelsMap


class MapGitHub2BioTools(ModelsMap):
    """
    Map bio.tools metadata record to GitHub
    """

    def map(self) -> dict[str, MapItem]:
        """
        Map GitHub metadata property to corresponding bio.tools property.
        """
        return {
            "name": MapItem(bt_entry=self.repo.name, gh_entry=self.metadata.name, method=Method.EXACT),
            # Languages are both lists
            "language": MapItem(bt_entry=self.repo.language, gh_entry=self.metadata.languages, method=Method.EXACT),
            "version": MapItem(
                bt_entry=self.repo.version, gh_entry=self.metadata.latest_release.tag_name, method=Method.EXACT
            ),
            # link in bio.tools is a list of objects with url property. We need to compare only
            # the list of urls.
            "link": MapItem(
                bt_entry=[link.url for link in self.repo.link.url],
                gh_entry=self.metadata.html_url,
                method=Method.EXACT,
            ),
            "licence": MapItem(
                bt_entry=self.repo.license.spdx_id,
                gh_entry=self.metadata.licence,
                method=Method.EXACT,
            ),
        }
