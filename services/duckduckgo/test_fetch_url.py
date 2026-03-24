# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import Mock, patch

import pytest
import requests

from services.duckduckgo.fetch_url import UNNECESSARY_TAGS, fetch_url


class TestFetchUrl:
    """Test cases for fetch_url function."""

    @patch("services.duckduckgo.fetch_url.requests.get")
    @patch("services.duckduckgo.fetch_url.slack_notify")
    def test_fetch_url_success(self, _mock_slack, mock_get, create_test_base_args):
        mock_response = Mock()
        mock_response.text = """
        <html>
            <head>
                <title>Test Page Title</title>
                <script>console.log('test');</script>
            </head>
            <body>
                <header>Header content</header>
                <nav>Navigation</nav>
                <main>
                    <article>
                        <h1>Main Article Title</h1>
                        <p>This is the main content of the article.</p>
                    </article>
                </main>
                <aside>Sidebar content</aside>
                <footer>Footer content</footer>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = fetch_url(base_args, "https://example.com")

        assert result is not None
        assert result["title"] == "Test Page Title"
        assert result["url"] == "https://example.com"
        assert "Main Article Title" in result["content"]
        assert "main content of the article" in result["content"]

    @patch("services.duckduckgo.fetch_url.requests.get")
    @patch("services.duckduckgo.fetch_url.slack_notify")
    def test_fetch_url_no_title(self, _mock_slack, mock_get, create_test_base_args):
        mock_response = Mock()
        mock_response.text = (
            "<html><body><div>Content without title</div></body></html>"
        )
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = fetch_url(base_args, "https://example.com")

        assert result is not None
        assert result["title"] == ""
        assert "Content without title" in result["content"]

    @patch("services.duckduckgo.fetch_url.requests.get")
    @patch("services.duckduckgo.fetch_url.slack_notify")
    def test_fetch_url_extracts_main_tag(
        self, _mock_slack, mock_get, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = """
        <html><head><title>Page with Main</title></head>
        <body><main><p>Main content here</p></main><div>Other content</div></body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = fetch_url(base_args, "https://example.com")

        assert result is not None
        assert result["title"] == "Page with Main"
        assert "Main content here" in result["content"]
        assert "Other content" not in result["content"]

    @patch("services.duckduckgo.fetch_url.requests.get")
    @patch("services.duckduckgo.fetch_url.slack_notify")
    def test_fetch_url_extracts_article_tag(
        self, _mock_slack, mock_get, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = """
        <html><head><title>Page with Article</title></head>
        <body><article><p>Article content here</p></article><div>Other content</div></body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = fetch_url(base_args, "https://example.com")

        assert result is not None
        assert "Article content here" in result["content"]
        assert "Other content" not in result["content"]

    @patch("services.duckduckgo.fetch_url.requests.get")
    @patch("services.duckduckgo.fetch_url.slack_notify")
    def test_fetch_url_removes_unnecessary_tags(
        self, _mock_slack, mock_get, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = """
        <html><head><title>Test</title><script>removed</script><style>removed</style></head>
        <body><header>Header</header><nav>Nav</nav><main><p>Keep this</p></main>
        <aside>Aside</aside><footer>Footer</footer></body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = fetch_url(base_args, "https://example.com")

        assert result is not None
        assert "Keep this" in result["content"]
        assert "removed" not in result["content"]
        assert "Header" not in result["content"]
        assert "Nav" not in result["content"]

    @patch("services.duckduckgo.fetch_url.requests.get")
    @patch("services.duckduckgo.fetch_url.slack_notify")
    def test_fetch_url_http_error(self, _mock_slack, mock_get, create_test_base_args):
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.HTTPError("HTTP Error")
        http_error.response = mock_response
        mock_get.side_effect = http_error
        base_args = create_test_base_args()

        result = fetch_url(base_args, "https://example.com/404")

        assert result is None

    @patch("services.duckduckgo.fetch_url.requests.get")
    @patch("services.duckduckgo.fetch_url.slack_notify")
    def test_fetch_url_strips_whitespace_title(
        self, _mock_slack, mock_get, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = "<html><head><title>   Title with spaces   </title></head><body><p>Content</p></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = fetch_url(base_args, "https://example.com")

        assert result is not None
        assert result["title"] == "Title with spaces"

    @patch("services.duckduckgo.fetch_url.requests.get")
    @patch("services.duckduckgo.fetch_url.slack_notify")
    def test_fetch_url_fallback_to_full_soup(
        self, _mock_slack, mock_get, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = """
        <html><head><title>No Main</title></head>
        <body><div><p>Regular div content</p><span>Some span</span></div></body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = fetch_url(base_args, "https://example.com")

        assert result is not None
        assert "Regular div content" in result["content"]
        assert "Some span" in result["content"]

    @patch("services.duckduckgo.fetch_url.requests.get")
    @patch("services.duckduckgo.fetch_url.slack_notify")
    def test_fetch_url_sends_slack_notification(
        self, mock_slack, mock_get, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = (
            "<html><head><title>Page</title></head><body><p>Content</p></body></html>"
        )
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args(owner="test-owner", repo="test-repo")

        fetch_url(base_args, "https://example.com")

        mock_slack.assert_called_once()
        call_text = mock_slack.call_args[0][0]
        assert "test-owner/test-repo" in call_text
        assert "https://example.com" in call_text


class TestFetchUrlIntegration:
    """Integration tests with real HTTP calls, only mocking slack_notify."""

    @pytest.mark.integration
    @patch("services.duckduckgo.fetch_url.slack_notify")
    def test_real_fetch_returns_markdown_content(
        self, _mock_slack, create_test_base_args
    ):
        base_args = create_test_base_args()

        result = fetch_url(base_args, "https://docs.python.org/3/library/json.html")

        assert result is not None
        assert result["title"]
        assert result["url"] == "https://docs.python.org/3/library/json.html"
        assert "json" in result["content"].lower()
        assert len(result["content"]) > 100


class TestConstants:
    """Test cases for fetch_url constants."""

    def test_unnecessary_tags(self):
        expected_tags = [
            "ads",
            "advertisement",
            "aside",
            "footer",
            "head",
            "header",
            "iframe",
            "link",
            "meta",
            "nav",
            "noscript",
            "path",
            "script",
            "style",
            "svg",
        ]
        assert UNNECESSARY_TAGS == expected_tags
