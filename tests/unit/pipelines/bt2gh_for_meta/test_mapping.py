"""
Unit tests for the mapping.
"""

from bridge.pipelines.bt2gh_for_pr.map import MapBioTools2GitHub
from bridge.pipelines.gh2bt_for_meta.map import MapGitHub2BioTools
from bridge.pipelines.protocols import Method
from bridge.pipelines.protocols.map import MapItem
from bridge.pipelines.protocols.none_propagation import deep_unwrap


class DummyGitHubRepoModel:
    """
    Minimal dummy for `GitHubRepoModel`:
    """

    class Release:
        """
        Minimal dummy for a GitHub Release
        """

        def __init__(self, tag_name: str):
            self.tag_name = tag_name

    class LinkElem:
        """
        Minimal dummy for a link element
        """

        def __init__(self, url: str):
            self.url = url

    class LinkContainer:
        """
        Minimal dummy for a link container
        """

        def __init__(self, urls: list[str]):
            # production code may iterate `repo.link.url` where .url is a list
            self.url = [DummyGitHubRepoModel.LinkElem(u) for u in urls]

    class License:
        """
        Minimal dummy for a license element
        """

        def __init__(self, spdx_id: str):
            self.spdx_id = spdx_id

    class FullRepo:
        """
        Minimal dummy for a full GitHub repo object
        """

        def __init__(self):
            self.name = "repo-name"
            self.language = "Python"
            self.link = DummyGitHubRepoModel.LinkContainer([])
            self.license = DummyGitHubRepoModel.License("MIT")
            self.html_url = "https://github.com/example/"
            self.homepage = "homepage"
            self.topics = ["genomics"]

    def __init__(self):
        self.repo = DummyGitHubRepoModel.FullRepo()
        self.latest_release = DummyGitHubRepoModel.Release("1.2.3")


class DummyBioToolsTool:
    """
    Minimal dummy for a bio.tools `ToolModel`-like object:
    """

    class Topic:
        """
        Minimal dummy for a bio.tools Topic object
        """

        def __init__(self, term: str):
            self.term = term

    def __init__(self):
        self.name = "tool-name"
        # bio.tools model uses `homepage`
        self.homepage = "https://example.org"
        # many mappers expect `topics` as list of objects with .term
        self.topic = [DummyBioToolsTool.Topic("genomics")]
        # some mappers check `.language` or `.languages`
        self.language = ["Python"]
        self.license = license or "MIT"
        # ToolModel uses `version` as list in the real schema; provide both shapes
        self.version = "1.2.3"
        self.link = [
            DummyGitHubRepoModel.LinkElem("https://example.com/a"),
            DummyGitHubRepoModel.LinkElem("https://example.com/b"),
        ]
        self.license = ["MIT"]


def test_mapbiotools2github_map_returns_expected_map():
    """
    Test for the biotools 2 github mapping function
    """
    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapBioTools2GitHub(repo=bt_tool, metadata=gh_repo)

    result = mapper.map()

    name_item = result["name"]
    assert isinstance(name_item, MapItem)
    assert deep_unwrap(name_item.schema_entry) == gh_repo.repo.name
    assert deep_unwrap(name_item.repo_entry) == bt_tool.name
    assert name_item.method == Method.EXACT

    homepage_item = result["homepage"]
    assert isinstance(homepage_item, MapItem)
    assert deep_unwrap(homepage_item.schema_entry) == gh_repo.repo.homepage
    assert deep_unwrap(homepage_item.repo_entry) == bt_tool.homepage
    assert homepage_item.method == Method.EXACT

    topic_item = result["topic"]
    assert isinstance(topic_item, MapItem)
    assert deep_unwrap(topic_item.schema_entry) == gh_repo.repo.topics
    assert deep_unwrap(topic_item.repo_entry) == [ti.term for ti in bt_tool.topic]
    assert topic_item.method == Method.SUBSET


def test_mapgithub2biotools_map_returns_expected_map():
    """
    Test for the github 2 biotools mapping function
    """
    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=bt_tool, metadata=gh_repo)

    result = mapper.map

    assert set(result) == {"name", "language", "version", "link", "license", "homepage"}

    name_item = result["name"]
    assert isinstance(name_item, MapItem)
    assert deep_unwrap(name_item.schema_entry) == gh_repo.repo.name
    assert deep_unwrap(name_item.repo_entry) == bt_tool.name
    assert name_item.method == Method.EXACT

    language_item = result["language"]
    assert isinstance(language_item, MapItem)
    assert deep_unwrap(language_item.schema_entry) == gh_repo.repo.language
    assert deep_unwrap(language_item.repo_entry) == bt_tool.language
    assert language_item.method == Method.EXACT

    version_item = result["version"]
    assert isinstance(version_item, MapItem)
    assert deep_unwrap(version_item.schema_entry) == gh_repo.latest_release.tag_name
    assert deep_unwrap(version_item.repo_entry) == bt_tool.version
    assert version_item.method == Method.EXACT

    link_item = result["link"]
    assert isinstance(link_item, MapItem)
    assert deep_unwrap(link_item.schema_entry) == gh_repo.repo.html_url
    assert deep_unwrap(link_item.repo_entry) == ["https://example.com/a", "https://example.com/b"]
    assert link_item.method == Method.EXACT

    license_item = result["license"]
    assert isinstance(license_item, MapItem)
    assert deep_unwrap(license_item.schema_entry) == gh_repo.repo.license.spdx_id
    assert deep_unwrap(license_item.repo_entry) == bt_tool.license
    assert license_item.method == Method.EXACT
