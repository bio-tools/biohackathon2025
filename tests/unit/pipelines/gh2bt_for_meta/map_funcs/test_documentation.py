"""
Unit tests for documentation mapping functions.
"""

import bridge.pipelines.gh2bt_for_meta.map_funcs.documentation as docmap
from bridge.core.biotools import DocumentationItem, TypeEnum1
from bridge.core.github_pages import GitHubPages


class _CoCStub:
    """Minimal stub that mimics bridge.core.github_repo.CodeOfConduct for these tests."""


def __init__(self, html_url: str | None):
    self.html_url = html_url


class TestMapWiki:
    """Test wiki mapping functionality."""

    def test_map_wiki_with_wiki_enabled(self, monkeypatch):
        """Test mapping when wiki is enabled."""
        monkeypatch.setattr(docmap, "_wiki_repo_exists", lambda *_args, **_kw: True)

        gh_html_url = "https://github.com/owner/repo"
        gh_has_wiki = True
        bt_documentation = None

        result = docmap._map_wiki(gh_html_url, gh_has_wiki, bt_documentation)

        assert result is not None
        assert len(result) == 1
        assert str(result[0].url.root) == "https://github.com/owner/repo/wiki"
        assert TypeEnum1.General in result[0].type

    def test_map_wiki_without_wiki(self):
        """Test mapping when wiki is disabled."""
        gh_html_url = "https://github.com/owner/repo"
        gh_has_wiki = False
        bt_documentation = None

        result = docmap._map_wiki(gh_html_url, gh_has_wiki, bt_documentation)

        assert result is None

    def test_map_wiki_no_url(self):
        """Test mapping when URL is None."""
        gh_html_url = None
        gh_has_wiki = True
        bt_documentation = None

        result = docmap._map_wiki(gh_html_url, gh_has_wiki, bt_documentation)

        assert result is None

    def test_map_wiki_repo_probe_fails(self, monkeypatch):
        """Test mapping when wiki is enabled but the wiki repo probe fails."""
        monkeypatch.setattr(docmap, "_wiki_repo_exists", lambda *_args, **_kw: False)

        gh_html_url = "https://github.com/owner/repo"
        gh_has_wiki = True
        bt_documentation = None

        result = docmap._map_wiki(gh_html_url, gh_has_wiki, bt_documentation)

        assert result is None

    def test_map_wiki_duplicate_prevention(self, monkeypatch):
        """Test that duplicate wiki URLs are not added."""
        monkeypatch.setattr(docmap, "_wiki_repo_exists", lambda *_args, **_kw: True)

        gh_html_url = "https://github.com/owner/repo"
        gh_has_wiki = True
        existing_doc = DocumentationItem(url="https://github.com/owner/repo/wiki", type=[TypeEnum1.General])
        bt_documentation = [existing_doc]

        result = docmap._map_wiki(gh_html_url, gh_has_wiki, bt_documentation)

        assert result is not None
        assert len(result) == 1  # still 1, not 2


class TestMapCodeOfConduct:
    """Test code of conduct mapping functionality."""

    def test_map_code_of_conduct_with_coc(self):
        """Test mapping when code of conduct exists."""
        gh_code_of_conduct = _CoCStub(html_url="https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md")
        bt_documentation = None

        result = docmap._map_code_of_conduct(gh_code_of_conduct, bt_documentation)

        assert result is not None
        assert len(result) == 1
        assert str(result[0].url.root) == "https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md"
        assert TypeEnum1.Code_of_conduct in result[0].type

    def test_map_code_of_conduct_without_coc(self):
        """Test mapping when code of conduct doesn't exist."""
        result = docmap._map_code_of_conduct(None, None)
        assert result is None

    def test_map_code_of_conduct_empty_object(self):
        """Test mapping when code of conduct object has no html_url."""
        gh_code_of_conduct = _CoCStub(html_url=None)
        bt_documentation = None

        result = docmap._map_code_of_conduct(gh_code_of_conduct, bt_documentation)

        assert result is None

    def test_map_code_of_conduct_duplicate_prevention(self):
        """Test that duplicate CoC URLs are not added."""
        gh_code_of_conduct = _CoCStub(html_url="https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md")
        existing_doc = DocumentationItem(
            url="https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md",
            type=[TypeEnum1.Code_of_conduct],
        )
        bt_documentation = [existing_doc]

        result = docmap._map_code_of_conduct(gh_code_of_conduct, bt_documentation)

        assert result is not None
        assert len(result) == 1  # still 1, not 2


class TestMapGitHubPages:
    """Test GitHub Pages mapping functionality."""

    def test_map_github_pages_with_pages_object(self):
        """Test mapping when GitHubPages object is provided."""
        gh_pages = GitHubPages(
            url="https://api.github.com/repos/owner/repo/pages",
            status="built",
            cname=None,
            custom_404=False,
            html_url="https://owner.github.io/repo",
            public=True,
        )
        bt_documentation = None

        result = docmap._map_github_pages(gh_pages, bt_documentation)

        assert result is not None
        assert len(result) == 1
        assert str(result[0].url.root).rstrip("/") == "https://owner.github.io/repo"
        assert TypeEnum1.General in result[0].type

    def test_map_github_pages_with_custom_domain(self):
        """Test mapping when GitHub Pages has custom domain."""
        gh_pages = GitHubPages(
            url="https://api.github.com/repos/owner/repo/pages",
            status="built",
            custom_404=False,
            html_url="https://example.com",
            cname="example.com",
            public=True,
        )
        bt_documentation = None

        result = docmap._map_github_pages(gh_pages, bt_documentation)

        assert result is not None
        assert len(result) == 1
        assert str(result[0].url.root).rstrip("/") == "https://example.com"

    def test_map_github_pages_none(self):
        """Test mapping when GitHub Pages doesn't exist."""
        result = docmap._map_github_pages(None, None)
        assert result is None

    def test_map_github_pages_no_html_url(self):
        """Test mapping when GitHub Pages exists but has no html_url."""
        gh_pages = GitHubPages(
            url="https://api.github.com/repos/owner/repo/pages",
            status="building",
            cname=None,
            custom_404=False,
            html_url=None,
            public=True,
        )
        bt_documentation = None

        result = docmap._map_github_pages(gh_pages, bt_documentation)

        assert result is None

    def test_map_github_pages_duplicate_prevention(self):
        """Test that duplicate GitHub Pages URLs are not added."""
        gh_pages = GitHubPages(
            url="https://api.github.com/repos/owner/repo/pages",
            status="built",
            cname=None,
            custom_404=False,
            html_url="https://owner.github.io/repo",
            public=True,
        )
        existing_doc = DocumentationItem(url="https://owner.github.io/repo", type=[TypeEnum1.General])
        bt_documentation = [existing_doc]

        result = docmap._map_github_pages(gh_pages, bt_documentation)

        assert result is not None
        assert len(result) == 1  # still 1, not 2


class TestMapDocumentation:
    """Test the main documentation mapping function."""

    def test_map_documentation_all_features(self, monkeypatch):
        """Test mapping with all documentation features enabled."""
        monkeypatch.setattr(docmap, "_wiki_repo_exists", lambda *_args, **_kw: True)

        gh_pages = GitHubPages(
            url="https://api.github.com/repos/owner/repo/pages",
            status="built",
            cname=None,
            custom_404=False,
            html_url="https://owner.github.io/repo",
            public=True,
        )
        gh_repo_data = {
            "html_url": "https://github.com/owner/repo",
            "has_wiki": True,
            "code_of_conduct": _CoCStub(html_url="https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md"),
            "github_pages": gh_pages,
        }
        bt_documentation = None

        result = docmap.map_documentation(gh_repo_data, bt_documentation)

        assert result is not None
        assert len(result) == 3  # Wiki, CoC, and GitHub Pages
        urls = [str(doc.url.root).rstrip("/") for doc in result]
        assert "https://github.com/owner/repo/wiki" in urls
        assert "https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md" in urls
        assert "https://owner.github.io/repo" in urls

    def test_map_documentation_no_features(self, monkeypatch):
        """
        Test mapping with no documentation features.

        Note: _map_wiki only adds if has_wiki AND wiki repo probe succeeds.
        We mock probe to True here, but has_wiki is False so nothing should be added.
        """
        monkeypatch.setattr(docmap, "_wiki_repo_exists", lambda *_args, **_kw: True)

        gh_repo_data = {
            "html_url": "https://github.com/owner/repo",
            "has_wiki": False,
            "code_of_conduct": None,
            "github_pages": None,
        }
        bt_documentation = None

        result = docmap.map_documentation(gh_repo_data, bt_documentation)

        assert result is None

    def test_map_documentation_none_input(self):
        """Test mapping with None input."""
        result = docmap.map_documentation(None, None)
        assert result is None

    def test_map_documentation_with_existing_docs(self, monkeypatch):
        """Test mapping preserves existing documentation."""
        monkeypatch.setattr(docmap, "_wiki_repo_exists", lambda *_args, **_kw: True)

        gh_pages = GitHubPages(
            url="https://api.github.com/repos/owner/repo/pages",
            status="built",
            cname=None,
            custom_404=False,
            html_url="https://owner.github.io/repo",
            public=True,
        )
        gh_repo_data = {
            "html_url": "https://github.com/owner/repo",
            "has_wiki": True,
            "code_of_conduct": None,
            "github_pages": gh_pages,
        }
        existing_doc = DocumentationItem(url="https://example.com/docs", type=[TypeEnum1.API_documentation])
        bt_documentation = [existing_doc]

        result = docmap.map_documentation(gh_repo_data, bt_documentation)

        assert result is not None
        assert len(result) == 3  # Existing + Wiki + GitHub Pages
        urls = [str(doc.url.root).rstrip("/") for doc in result]
        assert "https://example.com/docs" in urls
        assert "https://github.com/owner/repo/wiki" in urls
        assert "https://owner.github.io/repo" in urls


class TestUrlNormalization:
    """Test URL normalization in duplicate detection."""

    def test_trailing_slash_normalization(self):
        """Test that URLs with and without trailing slashes are treated as duplicates."""
        existing_doc = DocumentationItem(url="https://example.com/docs", type=[TypeEnum1.General])
        bt_documentation = [existing_doc]

        result = docmap._add_doc_if_not_exists(bt_documentation, "https://example.com/docs/", TypeEnum1.General)

        assert len(result) == 1

    def test_case_insensitive_normalization(self):
        """Test that URLs with different cases are treated as duplicates."""
        existing_doc = DocumentationItem(url="https://example.com/docs", type=[TypeEnum1.General])
        bt_documentation = [existing_doc]

        result = docmap._add_doc_if_not_exists(bt_documentation, "https://EXAMPLE.com/docs", TypeEnum1.General)

        assert len(result) == 1

    def test_trailing_slash_and_case_normalization(self):
        """Test that URLs with both trailing slash and case differences are treated as duplicates."""
        existing_doc = DocumentationItem(url="https://example.com/docs", type=[TypeEnum1.General])
        bt_documentation = [existing_doc]

        result = docmap._add_doc_if_not_exists(bt_documentation, "https://Example.COM/docs/", TypeEnum1.General)

        assert len(result) == 1

    def test_different_urls_not_normalized_away(self):
        """Test that genuinely different URLs are not treated as duplicates."""
        existing_doc = DocumentationItem(url="https://example.com/docs", type=[TypeEnum1.General])
        bt_documentation = [existing_doc]

        result = docmap._add_doc_if_not_exists(bt_documentation, "https://example.com/wiki", TypeEnum1.General)

        assert len(result) == 2
