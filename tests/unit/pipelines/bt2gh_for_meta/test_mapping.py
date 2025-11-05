"""
Unit tests for the mapping.
"""

from bridge.pipelines.bt2gh_for_pr.map import MapBioTools2GitHub
from bridge.pipelines.gh2bt_for_meta.map import MapGitHub2BioTools
from bridge.pipelines.mapping.bt2gh_map import MapItem
from bridge.pipelines.protocols import Method


class DummyTopic:
    """
    Dummy topic class
    """

    def __init__(self, term: str):
        self.term = term


class DummyUrlElem:
    """
    Dummy url element
    """

    def __init__(self, url: str):
        self.url = url


class DummyLinkContainer:
    """
    Dummy Links
    """

    def __init__(self, urls: list[str]):
        self.url = [DummyUrlElem(u) for u in urls]


class DummyLicense:
    """
    Dummy Lcence
    """

    def __init__(self, spdx_id: str):
        self.spdx_id = spdx_id


class DummyLatestRelease:
    """
    Dummy Latest release
    """

    def __init__(self, tag_name: str):
        self.tag_name = tag_name


class DummyGHRepo:
    """
    Dummy GitHub repository class
    """

    def __init__(self):
        self.name = "tool-name"
        self.homepage = "https://example.org"
        self.topics = ["topic1", "topic2"]
        self.languages = ["Python", "C++"]
        self.latest_release = DummyLatestRelease(tag_name="v0.9.0")
        self.html_url = "https://github.com/example/repo"
        self.licence = "MIT"


class DummyBTMetadata:
    """
    Dummy bio.tools class.
    """

    def __init__(self):
        self.name = "tool-name-on-gh"
        self.homepage = "https://gh.example"
        self.version = "0.1.2"
        self.topic = [DummyTopic(term="genomics")]
        self.language = ["Python", "C++"]
        self.link = DummyLinkContainer(["https://example.com/a", "https://example.com/b"])
        self.license = DummyLicense(spdx_id="MIT")


def test_mapbiotools2github_map_returns_expected_map():
    """
    Test for the biotools 2 github mapping function
    """
    gh_repo = DummyGHRepo()
    bt_metadata = DummyBTMetadata()
    mapper = MapBioTools2GitHub(repo=bt_metadata, metadata=gh_repo)

    result = mapper.map()

    name_item = result["name"]
    assert isinstance(name_item, MapItem)
    assert name_item.schema_entry == bt_metadata.name
    assert name_item.repo_entry == gh_repo.name
    assert name_item.method == Method.EXACT

    homepage_item = result["homepage"]
    assert isinstance(homepage_item, MapItem)
    assert homepage_item.schema_entry == bt_metadata.homepage
    assert homepage_item.repo_entry == gh_repo.homepage
    assert homepage_item.method == Method.EXACT

    topic_item = result["topic"]
    assert isinstance(topic_item, MapItem)
    assert topic_item.schema_entry == [ti.term for ti in bt_metadata.topic]
    assert topic_item.repo_entry == gh_repo.topics
    assert topic_item.method == Method.SUBSET


def test_mapgithub2biotools_map_returns_expected_map():
    """
    Test for the github 2 biotools mapping function
    """
    repo = DummyBTMetadata()
    metadata = DummyGHRepo()
    mapper = MapGitHub2BioTools(repo=repo, metadata=metadata)

    result = mapper.map()

    assert set(result.keys()) == {"name", "language", "version", "link", "licence"}

    name_item = result["name"]
    assert isinstance(name_item, MapItem)
    assert name_item.schema_entry == repo.name
    assert name_item.repo_entry == metadata.name
    assert name_item.method == Method.EXACT

    language_item = result["language"]
    assert isinstance(language_item, MapItem)
    assert language_item.schema_entry == repo.language
    assert language_item.repo_entry == metadata.languages
    assert language_item.method == Method.EXACT

    version_item = result["version"]
    assert isinstance(version_item, MapItem)
    assert version_item.schema_entry == repo.version
    assert version_item.repo_entry == metadata.latest_release.tag_name
    assert version_item.method == Method.EXACT

    link_item = result["link"]
    assert isinstance(link_item, MapItem)
    assert link_item.schema_entry == ["https://example.com/a", "https://example.com/b"]
    assert link_item.repo_entry == metadata.html_url
    assert link_item.method == Method.EXACT

    licence_item = result["licence"]
    assert isinstance(licence_item, MapItem)
    assert licence_item.schema_entry == repo.license.spdx_id
    assert licence_item.repo_entry == metadata.licence
    assert licence_item.method == Method.EXACT
