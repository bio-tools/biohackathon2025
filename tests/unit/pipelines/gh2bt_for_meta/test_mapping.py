"""
Unit tests for the mapping.
"""

import bridge.pipelines.gh2bt_for_meta.map as gh2bt_map_mod
from bridge.pipelines.gh2bt_for_meta.map import MapGitHub2BioTools
from bridge.pipelines.protocols import Method
from bridge.pipelines.protocols.map import MapItem
from bridge.pipelines.protocols.none_propagation import deep_unwrap

from ..dummy.dummy_biotools import DummyBioToolsTool
from ..dummy.dummy_github import DummyGitHubRepoModel


def test_mapgithub2biotools_map_returns_expected_map(tmp_path, monkeypatch):
    """
    Test for the github → biotools mapping function.
    """
    gh_repo = DummyGitHubRepoModel()
    bt_tool = DummyBioToolsTool()

    # The map property reads CITATION.cff through load_dict_from_yaml_file immediately.
    # Mock it so the test doesn't depend on filesystem contents or YAML parsing.
    monkeypatch.setattr(gh2bt_map_mod, "load_dict_from_yaml_file", lambda _path: {})

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
    }

    biotools_id_item = result["biotools_id"]
    assert isinstance(biotools_id_item, MapItem)
    assert deep_unwrap(biotools_id_item.repo_entry) == gh_repo.repo.name
    assert deep_unwrap(biotools_id_item.schema_entry) == bt_tool.biotoolsID
    assert biotools_id_item.method == Method.FUZZY

    name_item = result["name"]
    assert isinstance(name_item, MapItem)
    assert deep_unwrap(name_item.repo_entry) == gh_repo.repo.name
    assert deep_unwrap(name_item.schema_entry) == bt_tool.name
    assert name_item.method == Method.EXACT

    homepage_item = result["homepage"]
    assert isinstance(homepage_item, MapItem)
    assert deep_unwrap(homepage_item.repo_entry) == {
        "homepage": gh_repo.repo.homepage,
        "html_url": gh_repo.repo.html_url,
    }
    assert deep_unwrap(homepage_item.schema_entry) == bt_tool.homepage
    assert homepage_item.method == Method.FUZZY

    language_item = result["language"]
    assert isinstance(language_item, MapItem)
    assert deep_unwrap(language_item.repo_entry) == gh_repo.languages
    assert deep_unwrap(language_item.schema_entry) == bt_tool.language
    assert language_item.method == Method.EXACT

    version_item = result["version"]
    assert isinstance(version_item, MapItem)
    assert deep_unwrap(version_item.repo_entry) == gh_repo.latest_release.tag_name
    assert deep_unwrap(version_item.schema_entry) == bt_tool.version
    assert version_item.method == Method.EXACT

    link_item = result["link"]
    assert isinstance(link_item, MapItem)
    assert deep_unwrap(link_item.repo_entry) == gh_repo.repo.html_url
    assert deep_unwrap(link_item.schema_entry) == [link.url for link in bt_tool.link]
    assert link_item.method == Method.EXACT

    license_item = result["license"]
    assert isinstance(license_item, MapItem)
    assert deep_unwrap(license_item.repo_entry) == gh_repo.repo.license.spdx_id
    assert deep_unwrap(license_item.schema_entry) == bt_tool.license
    assert license_item.method == Method.EXACT
