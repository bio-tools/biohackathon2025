"""
Mapping classes for GitHub to bio.tools.
"""

from pathlib import Path

from bridge.pipelines.protocols import MapItem, Method, ModelsMap
from bridge.pipelines.utils import load_dict_from_yaml_file

from .map_funcs import (
    map_biotools_id,
    map_description,
    map_documentation,
    map_functions,
    map_homepage,
    map_language,
    map_license,
    map_maturity,
    map_name,
    map_publication,
    map_topics,
    map_version,
)


class MapGitHub2BioTools(ModelsMap):
    """
    Map bio.tools metadata record to GitHub
    """

    def __init__(self, repo, metadata, repo_path: str):
        super().__init__(repo=repo, metadata=metadata)
        self.repo_path = Path(repo_path)

    @property
    def map(self) -> dict[str, MapItem]:
        """
        Map GitHub metadata property to corresponding bio.tools property.
        """
        return {
            "biotools_id": MapItem(
                schema_entry=self.metadata.biotoolsID,
                repo_entry=self.repo.repo.name,
                method=Method.FUZZY,
                fn=map_biotools_id,
            ),
            "name": MapItem(
                schema_entry=self.metadata.name, repo_entry=self.repo.repo.name, method=Method.EXACT, fn=map_name
            ),
            # Languages are both lists
            "language": MapItem(
                schema_entry=self.metadata.language,
                repo_entry=self.repo.languages,
                method=Method.EXACT,
                fn=map_language,
            ),
            # link in bio.tools is a list of objects with url property. We need to compare only
            # the list of urls.
            "link": MapItem(
                schema_entry=[link.url for link in self.metadata.link],
                repo_entry=self.repo.repo.html_url,
                method=Method.EXACT,
            ),
            "license": MapItem(
                schema_entry=self.metadata.license,
                repo_entry=self.repo.repo.license.spdx_id,
                method=Method.EXACT,
                fn=map_license,
            ),
            "homepage": MapItem(
                schema_entry=self.metadata.homepage,
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
            "maturity": MapItem(
                schema_entry=self.metadata.maturity,
                repo_entry={
                    "stargazers_count": self.repo.repo.stargazers_count,
                    "forks_count": self.repo.repo.forks_count,
                    "watchers_count": self.repo.repo.watchers_count,
                    "subscribers_count": self.repo.repo.subscribers_count,
                    "archived": self.repo.repo.archived,
                },
                method=Method.FUZZY,
                fn=map_maturity,
            ),
            "version": MapItem(
                schema_entry=self.metadata.version,
                repo_entry=self.repo.latest_release.tag_name,
                method=Method.EXACT,
                fn=map_version,
            ),
            "publication": MapItem(
                schema_entry=self.metadata.publication,
                repo_entry=load_dict_from_yaml_file(self.repo_path / "CITATION.cff"),
                method=Method.FUZZY,
                fn=map_publication,
            ),
            "functions": MapItem(
                schema_entry=self.metadata.function,
                repo_entry=self.repo.readme,
                method=Method.FUZZY,
                fn=map_functions,
            ),
            "topics": MapItem(
                schema_entry=self.metadata.topic,
                repo_entry=self.repo.repo.topics,
                method=Method.FUZZY,
                fn=map_topics,
            ),
        }
