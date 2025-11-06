"""
Mapping classes for GitHub to bio.tools.
"""

from bridge.pipelines.protocols import MapItem, Method, ModelsMap

from .map_funcs import map_description, map_documentation, map_homepage, map_license


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
            "name": MapItem(schema_entry=self.repo.repo.name, repo_entry=self.metadata.name, method=Method.EXACT),
            # Languages are both lists
            "language": MapItem(
                schema_entry=self.metadata.language, repo_entry=self.repo.repo.language, method=Method.EXACT
            ),
            "version": MapItem(
                schema_entry=self.metadata.version, repo_entry=self.repo.latest_release.tag_name, method=Method.EXACT
            ),
            # link in bio.tools is a list of objects with url property. We need to compare only
            # the list of urls.
            "link": MapItem(
                schema_entry=[link.url for link in self.metadata.link],
                repo_entry=self.repo.html_url,
                method=Method.EXACT,
            ),
            "license": MapItem(
                schema_entry=self.metadata.repo.license.spdx_id,
                repo_entry=self.repo.license,
                method=Method.EXACT,
                fn=map_license,
            ),
            "homepage": MapItem(
                schema_entry=self.metadata.repo.homepage,
                repo_entry={"homepage": self.repo.repo.homepage, "html_url": self.repo.repo.html_url},
                method=Method.FUZZY,
                fn=map_homepage,
            ),
            "documentation": MapItem(
                schema_entry=self.metadata.documentation,
                repo_entry={
                    "html_url": self.repo.repo.html_url,
                    "has_wiki": self.repo.repo.has_wiki,
                    "code_of_conduct": self.repo.repo.code_of_conduct,
                    "github_pages": self.repo.github_pages,
                },
                method=Method.FUZZY,
                fn=map_documentation,
            ),
            "description": MapItem(
                schema_entry=self.metadata.description,
                repo_entry={"description": self.repo.repo.description, "readme": self.repo.readme},
                method=Method.FUZZY,
                fn=map_description,
            ),
        }
