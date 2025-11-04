# python
from bridge.pipelines.mapping.main import MapBioTools2GitHub, MapItem
from bridge.pipelines.protocols import Method


class DummyTopic:
    def __init__(self, term: str):
        self.term = term


class DummyGHRepo:
    def __init__(self):
        self.name = "tool-name"
        self.homepage = "https://example.org"
        self.topics = "topics"



class DummyBTMetadata:
    def __init__(self):
        self.name = "tool-name-on-gh"
        self.homepage = "https://gh.example"
        self.version = "0.1.2"
        self.topic = DummyTopic(term="genomics")


def test_mapbiotools2github_map_returns_expected_map():
    gh_repo = DummyGHRepo()
    bt_metadata = DummyBTMetadata()
    mapper = MapBioTools2GitHub(repo=bt_metadata, metadata=gh_repo)

    result = mapper.map()

    name_item = result["name"]
    assert isinstance(name_item, MapItem)
    assert name_item.bt_entry == bt_metadata.name
    assert name_item.gh_entry == gh_repo.name
    assert name_item.method == Method.EXACT

    homepage_item = result["homepage"]
    assert isinstance(homepage_item, MapItem)
    assert homepage_item.bt_entry == bt_metadata.homepage
    assert homepage_item.gh_entry == gh_repo.homepage
    assert homepage_item.method == Method.EXACT
