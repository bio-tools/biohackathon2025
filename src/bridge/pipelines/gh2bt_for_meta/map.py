"""
Mapping classes for GitHub to bio.tools.
"""

from bridge.pipelines.protocols import MapItem, Method, ModelsMap

from .map_funcs import map_homepage


class MapGitHub2BioTools(ModelsMap):
    """
    Map bio.tools metadata record to GitHub
    """

    @property
    def map(self) -> dict[str, MapItem]:
        """
        Map GitHub metadata property to corresponding bio.tools property.
        """
        return {
            "name": MapItem(schema_entry=self.metadata.repo.name, repo_entry=self.repo.name, method=Method.EXACT),
            # Languages are both lists
            "language": MapItem(
                schema_entry=self.metadata.repo.language, repo_entry=self.repo.language, method=Method.EXACT
            ),
            "version": MapItem(
                schema_entry=self.metadata.latest_release.tag_name, repo_entry=self.repo.version, method=Method.EXACT
            ),
            # link in bio.tools is a list of objects with url property. We need to compare only
            # the list of urls.
            "link": MapItem(
                schema_entry=self.metadata.repo.html_url,
                repo_entry=[link.url for link in self.repo.link],
                method=Method.EXACT,
            ),
            "license": MapItem(
                schema_entry=self.metadata.repo.license.spdx_id,
                repo_entry=self.repo.license,
                method=Method.EXACT,
            ),
            "homepage": MapItem(
                schema_entry=self.metadata.repo.homepage,
                repo_entry=self.repo.homepage,
                method=Method.FUZZY,
                fn=map_homepage,
            ),
        }
