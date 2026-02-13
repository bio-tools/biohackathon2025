"""
Unit tests for bio.tools → GitHub mapping (MapBioTools2GitHub).
"""

import bridge.pipelines.bt2gh_for_pr_issues.map as bt2gh_map_mod
from bridge.pipelines.bt2gh_for_pr_issues.map import MapBioTools2GitHub
from bridge.pipelines.protocols import Method
from bridge.pipelines.protocols.map import MapItem
from bridge.pipelines.protocols.none_propagation import deep_unwrap

from ..dummy.dummy_biotools import DummyBioToolsTool
from ..dummy.dummy_github import DummyGitHubRepoModel


def test_mapbiotools2github_map_returns_expected_keys(monkeypatch, tmp_path):
    """
    Basic smoke test: map contains the expected keys.
    Also monkeypatch CITATION.cff loading to avoid filesystem dependency.
    """
    monkeypatch.setattr(bt2gh_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()

    mapper = MapBioTools2GitHub(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))
    result = mapper.map

    assert set(result.keys()) == {
        "name",
        "version",
        "description",
        "citation",
        "topics",
        "homepage",
        "readme",
        "license",
        "functions",
    }


def test_mapbiotools2github_name_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(bt2gh_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapBioTools2GitHub(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["name"]
    assert isinstance(item, MapItem)

    assert deep_unwrap(item.schema_entry) == {"name": bt_tool.name, "biotoolsID": bt_tool.biotoolsID.root}
    assert deep_unwrap(item.repo_entry) == gh_repo.repo.name
    assert item.method == Method.EXACT
    assert item.fn is not None  # map_name


def test_mapbiotools2github_version_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(bt2gh_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapBioTools2GitHub(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["version"]
    assert isinstance(item, MapItem)

    # mapper uses schema_entry=self.metadata.version (bio.tools: Optional[List[VersionType]])
    assert deep_unwrap(item.schema_entry) == bt_tool.version
    assert deep_unwrap(item.repo_entry) == gh_repo.latest_release.tag_name
    assert item.method == Method.EXACT
    assert item.fn is not None  # map_version


def test_mapbiotools2github_description_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(bt2gh_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapBioTools2GitHub(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["description"]
    assert isinstance(item, MapItem)

    assert deep_unwrap(item.schema_entry) == bt_tool.description
    assert deep_unwrap(item.repo_entry) == gh_repo.repo.description
    assert item.method == Method.EXACT
    assert item.fn is not None  # map_description


def test_mapbiotools2github_topics_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(bt2gh_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapBioTools2GitHub(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["topics"]
    assert isinstance(item, MapItem)

    # mapper uses schema_entry={"topics": self.metadata.topic, "functions": self.metadata.function}
    assert deep_unwrap(item.schema_entry) == {"topics": bt_tool.topic, "functions": bt_tool.function}
    assert deep_unwrap(item.repo_entry) == gh_repo.repo.topics
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_topics


def test_mapbiotools2github_homepage_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(bt2gh_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapBioTools2GitHub(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["homepage"]
    assert isinstance(item, MapItem)

    # schema_entry is UrlftpType RootModel in real schema
    assert deep_unwrap(item.schema_entry) == bt_tool.homepage
    assert deep_unwrap(item.repo_entry) == {"homepage": gh_repo.repo.homepage, "html_url": gh_repo.repo.html_url}
    assert item.method == Method.EXACT
    assert item.fn is not None  # map_homepage


def test_mapbiotools2github_readme_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(bt2gh_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapBioTools2GitHub(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["readme"]
    assert isinstance(item, MapItem)

    assert deep_unwrap(item.schema_entry) == {
        "name": bt_tool.name,
        "biotoolsID": bt_tool.biotoolsID.root,
        "toolType": bt_tool.toolType,
        "functions": bt_tool.function,
    }
    assert deep_unwrap(item.repo_entry) == gh_repo.readme
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_readme


def test_mapbiotools2github_license_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(bt2gh_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapBioTools2GitHub(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["license"]
    assert isinstance(item, MapItem)

    # schema_entry is a License enum member (not a list) in the real schema
    assert deep_unwrap(item.schema_entry) == bt_tool.license
    assert deep_unwrap(item.repo_entry) == gh_repo.repo.license
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_license


def test_mapbiotools2github_functions_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(bt2gh_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapBioTools2GitHub(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["functions"]
    assert isinstance(item, MapItem)

    # schema_entry is a list of FunctionItem in the real schema
    assert deep_unwrap(item.schema_entry) == bt_tool.function
    assert deep_unwrap(item.repo_entry) == gh_repo.readme
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_functions


def test_mapbiotools2github_citation_mapping_loads_from_yaml(monkeypatch, tmp_path):
    """
    Ensure citation.repo_entry comes from load_dict_from_yaml_file(repo_path / CITATION.cff)
    without actually reading the filesystem.
    """
    sentinel_citation = {"message": "from yaml"}
    monkeypatch.setattr(bt2gh_map_mod, "load_dict_from_yaml_file", lambda _path: sentinel_citation)

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapBioTools2GitHub(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["citation"]
    assert isinstance(item, MapItem)

    assert deep_unwrap(item.repo_entry) == sentinel_citation
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_citation

    schema = deep_unwrap(item.schema_entry)
    assert schema["name"] == bt_tool.name
    assert schema["biotoolsID"] == bt_tool.biotoolsID  # NOTE: mapper uses the object, not .root
    assert schema["homepage"] == bt_tool.homepage
    assert schema["license"] == bt_tool.license
    assert schema["topic"] == bt_tool.topic
    assert schema["description"] == bt_tool.description
