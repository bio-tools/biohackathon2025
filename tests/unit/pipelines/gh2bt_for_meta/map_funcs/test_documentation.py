"""
Unit tests for documentation mapping functions.
"""

from bridge.core.biotools import DocumentationItem, TypeEnum1
from bridge.core.github_pages import GitHubPages
from bridge.pipelines.gh2bt_for_meta.map_funcs.documentation import (
    map_code_of_conduct,
    map_documentation,
    map_github_pages,
    map_wiki,
)


class TestMapWiki:
    """Test wiki mapping functionality."""

    def test_map_wiki_with_wiki_enabled(self):
        """Test mapping when wiki is enabled."""
        gh_html_url = "https://github.com/owner/repo"
        gh_has_wiki = True
        bt_documentation = None

        result = map_wiki(gh_html_url, gh_has_wiki, bt_documentation)

        assert result is not None
        assert len(result) == 1
        assert str(result[0].url.root) == "https://github.com/owner/repo/wiki"
        assert TypeEnum1.General in result[0].type

    def test_map_wiki_without_wiki(self):
        """Test mapping when wiki is disabled."""
        gh_html_url = "https://github.com/owner/repo"
        gh_has_wiki = False
        bt_documentation = None

        result = map_wiki(gh_html_url, gh_has_wiki, bt_documentation)

        assert result is None

    def test_map_wiki_no_url(self):
        """Test mapping when URL is None."""
        gh_html_url = None
        gh_has_wiki = True
        bt_documentation = None

        result = map_wiki(gh_html_url, gh_has_wiki, bt_documentation)

        assert result is None

    def test_map_wiki_duplicate_prevention(self):
        """Test that duplicate wiki URLs are not added."""
        gh_html_url = "https://github.com/owner/repo"
        gh_has_wiki = True
        # Pre-existing documentation with wiki URL
        existing_doc = DocumentationItem(url="https://github.com/owner/repo/wiki", type=[TypeEnum1.General])
        bt_documentation = [existing_doc]

        result = map_wiki(gh_html_url, gh_has_wiki, bt_documentation)

        assert result is not None
        assert len(result) == 1  # Should still be 1, not 2


class TestMapCodeOfConduct:
    """Test code of conduct mapping functionality."""

    def test_map_code_of_conduct_with_coc(self):
        """Test mapping when code of conduct exists."""
        gh_code_of_conduct = {"html_url": "https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md"}
        bt_documentation = None

        result = map_code_of_conduct(gh_code_of_conduct, bt_documentation)

        assert result is not None
        assert len(result) == 1
        assert str(result[0].url.root) == "https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md"
        assert TypeEnum1.Code_of_conduct in result[0].type

    def test_map_code_of_conduct_without_coc(self):
        """Test mapping when code of conduct doesn't exist."""
        gh_code_of_conduct = None
        bt_documentation = None

        result = map_code_of_conduct(gh_code_of_conduct, bt_documentation)

        assert result is None

    def test_map_code_of_conduct_empty_dict(self):
        """Test mapping when code of conduct is empty dict."""
        gh_code_of_conduct = {}
        bt_documentation = None

        result = map_code_of_conduct(gh_code_of_conduct, bt_documentation)

        assert result is None

    def test_map_code_of_conduct_duplicate_prevention(self):
        """Test that duplicate CoC URLs are not added."""
        gh_code_of_conduct = {"html_url": "https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md"}
        existing_doc = DocumentationItem(
            url="https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md",
            type=[TypeEnum1.Code_of_conduct],
        )
        bt_documentation = [existing_doc]

        result = map_code_of_conduct(gh_code_of_conduct, bt_documentation)

        assert result is not None
        assert len(result) == 1  # Should still be 1, not 2


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

        result = map_github_pages(gh_pages, bt_documentation)

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

        result = map_github_pages(gh_pages, bt_documentation)

        assert result is not None
        assert len(result) == 1
        assert str(result[0].url.root).rstrip("/") == "https://example.com"

    def test_map_github_pages_none(self):
        """Test mapping when GitHub Pages doesn't exist."""
        gh_pages = None
        bt_documentation = None

        result = map_github_pages(gh_pages, bt_documentation)

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

        result = map_github_pages(gh_pages, bt_documentation)

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

        result = map_github_pages(gh_pages, bt_documentation)

        assert result is not None
        assert len(result) == 1  # Should still be 1, not 2


class TestMapDocumentation:
    """Test the main documentation mapping function."""

    def test_map_documentation_all_features(self):
        """Test mapping with all documentation features enabled."""
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
            "code_of_conduct": {"html_url": "https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md"},
            "github_pages": gh_pages,
        }
        bt_documentation = None

        result = map_documentation(gh_repo_data, bt_documentation)

        assert result is not None
        assert len(result) == 3  # Wiki, CoC, and GitHub Pages
        urls = [str(doc.url.root).rstrip("/") for doc in result]
        assert "https://github.com/owner/repo/wiki" in urls
        assert "https://github.com/owner/repo/blob/main/CODE_OF_CONDUCT.md" in urls
        assert "https://owner.github.io/repo" in urls

    def test_map_documentation_no_features(self):
        """Test mapping with no documentation features."""
        gh_repo_data = {
            "html_url": "https://github.com/owner/repo",
            "has_wiki": False,
            "code_of_conduct": None,
            "github_pages": None,
        }
        bt_documentation = None

        result = map_documentation(gh_repo_data, bt_documentation)

        assert result is None

    def test_map_documentation_none_input(self):
        """Test mapping with None input."""
        result = map_documentation(None, None)

        assert result is None

    def test_map_documentation_with_existing_docs(self):
        """Test mapping preserves existing documentation."""
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

        result = map_documentation(gh_repo_data, bt_documentation)

        assert result is not None
        assert len(result) == 3  # Existing + Wiki + GitHub Pages
        urls = [str(doc.url.root).rstrip("/") for doc in result]
        assert "https://example.com/docs" in urls
        assert "https://github.com/owner/repo/wiki" in urls
        assert "https://owner.github.io/repo" in urls
