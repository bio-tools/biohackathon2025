"""
Unit tests for GitHub → bio.tools mapping (MapGitHub2BioTools).
"""

import bridge.pipelines.gh2bt_for_meta.map as gh2bt_map_mod
from bridge.pipelines.gh2bt_for_meta.map import MapGitHub2BioTools
from bridge.pipelines.protocols import Method
from bridge.pipelines.protocols.map import MapItem
from bridge.pipelines.protocols.none_propagation import deep_unwrap

from ..dummy.dummy_biotools import DummyBioToolsTool
from ..dummy.dummy_github import DummyGitHubRepoModel


def test_mapgithub2biotools_map_returns_expected_keys(monkeypatch, tmp_path):
    """
    Smoke test: map contains the expected keys.
    Patch CITATION.cff loading to avoid filesystem dependency.
    """
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()

    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))
    result = mapper.map

    assert set(result) == {
        "biotools_id",
        "name",
        "language",
        "link",
        "license",
        "homepage",
        "documentation",
        "description",
        "maturity",
        "version",
        "publication",
        "functions",
        "topics",
    }


def test_mapgithub2biotools_biotools_id_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["biotools_id"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.schema_entry) == bt_tool.biotoolsID
    assert deep_unwrap(item.repo_entry) == gh_repo.repo.name
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_biotools_id


def test_mapgithub2biotools_name_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["name"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.repo_entry) == gh_repo.repo.name
    assert deep_unwrap(item.schema_entry) == bt_tool.name
    assert item.method == Method.EXACT
    assert item.fn is not None  # map_name


def test_mapgithub2biotools_language_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["language"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.repo_entry) == gh_repo.languages
    assert deep_unwrap(item.schema_entry) == bt_tool.language
    assert item.method == Method.EXACT
    assert item.fn is not None  # map_language


def test_mapgithub2biotools_link_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["link"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.repo_entry) == gh_repo.repo.html_url
    assert deep_unwrap(item.schema_entry) == [l.url for l in bt_tool.link]
    assert item.method == Method.EXACT
    assert item.fn is None  # no fn wired for link in your mapper


def test_mapgithub2biotools_license_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["license"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.repo_entry) == gh_repo.repo.license.spdx_id
    assert deep_unwrap(item.schema_entry) == bt_tool.license
    assert item.method == Method.EXACT
    assert item.fn is not None  # map_license


def test_mapgithub2biotools_homepage_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["homepage"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.repo_entry) == {"homepage": gh_repo.repo.homepage, "html_url": gh_repo.repo.html_url}
    assert deep_unwrap(item.schema_entry) == bt_tool.homepage
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_homepage


def test_mapgithub2biotools_documentation_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["documentation"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.schema_entry) == bt_tool.documentation
    assert deep_unwrap(item.repo_entry) == {
        "html_url": gh_repo.repo.html_url,
        "has_wiki": gh_repo.repo.has_wiki,
        "code_of_conduct": gh_repo.repo.code_of_conduct,
        "github_pages": gh_repo.github_pages,
    }
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_documentation


def test_mapgithub2biotools_description_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["description"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.schema_entry) == bt_tool.description
    assert deep_unwrap(item.repo_entry) == {"description": gh_repo.repo.description, "readme": gh_repo.readme}
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_description


def test_mapgithub2biotools_maturity_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["maturity"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.schema_entry) == bt_tool.maturity
    assert deep_unwrap(item.repo_entry) == {
        "stargazers_count": gh_repo.repo.stargazers_count,
        "forks_count": gh_repo.repo.forks_count,
        "watchers_count": gh_repo.repo.watchers_count,
        "subscribers_count": gh_repo.repo.subscribers_count,
        "archived": gh_repo.repo.archived,
    }
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_maturity


def test_mapgithub2biotools_version_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["version"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.schema_entry) == bt_tool.version
    assert deep_unwrap(item.repo_entry) == gh_repo.latest_release.tag_name
    assert item.method == Method.EXACT
    assert item.fn is not None  # map_version


def test_mapgithub2biotools_functions_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["functions"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.schema_entry) == bt_tool.function
    assert deep_unwrap(item.repo_entry) == gh_repo.readme
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_functions


def test_mapgithub2biotools_publication_mapping_from_yaml(monkeypatch, tmp_path):
    """
    Ensure publication.repo_entry comes from load_dict_from_yaml_file(repo_path / CITATION.cff)
    without touching the filesystem.
    """
    sentinel = {"title": "From CITATION.cff"}
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: sentinel)

    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()
    mapper = MapGitHub2BioTools(repo=gh_repo, metadata=bt_tool, repo_path=str(tmp_path))

    item = mapper.map["publication"]
    assert isinstance(item, MapItem)
    assert deep_unwrap(item.schema_entry) == bt_tool.publication
    assert deep_unwrap(item.repo_entry) == sentinel
    assert item.method == Method.FUZZY
    assert item.fn is not None  # map_publication
