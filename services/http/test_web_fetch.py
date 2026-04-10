# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import Mock, patch

import pytest
import requests

from services.http.web_fetch import UNNECESSARY_TAGS, web_fetch

MOCK_HAIKU_PATH = "services.http.web_fetch.chat_with_claude_simple"


class TestWebFetch:
    """Test cases for web_fetch function."""

    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_success(
        self, _mock_slack, mock_get, mock_haiku, create_test_base_args
    ):
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
        mock_haiku.return_value = (
            "The page contains an article about Main Article Title."
        )
        base_args = create_test_base_args()

        result = web_fetch(
            base_args, "https://example.com", "What is the article about?"
        )

        assert result is not None
        assert result["title"] == "Test Page Title"
        assert result["url"] == "https://example.com"
        assert "Main Article Title" in result["content"]
        mock_haiku.assert_called_once()

    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_no_title(
        self, _mock_slack, mock_get, mock_haiku, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = (
            "<html><body><div>Content without title</div></body></html>"
        )
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_haiku.return_value = "Content without title"
        base_args = create_test_base_args()

        result = web_fetch(base_args, "https://example.com", "Summarize the page")

        assert result is not None
        assert result["title"] == ""
        assert "Content without title" in result["content"]

    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_extracts_main_tag(
        self, _mock_slack, mock_get, mock_haiku, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = """
        <html><head><title>Page with Main</title></head>
        <body><main><p>Main content here</p></main><div>Other content</div></body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_haiku.return_value = "Main content here"
        base_args = create_test_base_args()

        result = web_fetch(base_args, "https://example.com", "Get main content")

        assert result is not None
        assert result["title"] == "Page with Main"
        # Haiku receives only main content, not "Other content"
        call_args = mock_haiku.call_args
        user_input = call_args[1]["user_input"]
        assert "Main content here" in user_input
        assert "Other content" not in user_input

    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_extracts_article_tag(
        self, _mock_slack, mock_get, mock_haiku, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = """
        <html><head><title>Page with Article</title></head>
        <body><article><p>Article content here</p></article><div>Other content</div></body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_haiku.return_value = "Article content here"
        base_args = create_test_base_args()

        result = web_fetch(base_args, "https://example.com", "Get article content")

        assert result is not None
        # Haiku receives only article content, not "Other content"
        call_args = mock_haiku.call_args
        user_input = call_args[1]["user_input"]
        assert "Article content here" in user_input
        assert "Other content" not in user_input

    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_removes_unnecessary_tags(
        self, _mock_slack, mock_get, mock_haiku, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = """
        <html><head><title>Test</title><script>removed</script><style>removed</style></head>
        <body><header>Header</header><nav>Nav</nav><main><p>Keep this</p></main>
        <aside>Aside</aside><footer>Footer</footer></body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_haiku.return_value = "Keep this"
        base_args = create_test_base_args()

        result = web_fetch(base_args, "https://example.com", "What should we keep?")

        assert result is not None
        # Haiku receives only the main content
        call_args = mock_haiku.call_args
        user_input = call_args[1]["user_input"]
        assert "Keep this" in user_input

    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_http_error(self, _mock_slack, mock_get, create_test_base_args):
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.HTTPError("HTTP Error")
        http_error.response = mock_response
        mock_get.side_effect = http_error
        base_args = create_test_base_args()

        result = web_fetch(base_args, "https://example.com/404", "Get page content")

        assert result is None

    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_strips_whitespace_title(
        self, _mock_slack, mock_get, mock_haiku, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = "<html><head><title>   Title with spaces   </title></head><body><p>Content</p></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_haiku.return_value = "Content"
        base_args = create_test_base_args()

        result = web_fetch(base_args, "https://example.com", "Summarize")

        assert result is not None
        assert result["title"] == "Title with spaces"

    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_fallback_to_full_soup(
        self, _mock_slack, mock_get, mock_haiku, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = """
        <html><head><title>No Main</title></head>
        <body><div><p>Regular div content</p><span>Some span</span></div></body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_haiku.return_value = "Regular div content and some span"
        base_args = create_test_base_args()

        result = web_fetch(base_args, "https://example.com", "Summarize")

        assert result is not None
        assert "Regular div content" in result["content"]

    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_sends_slack_notification(
        self, mock_slack, mock_get, mock_haiku, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = (
            "<html><head><title>Page</title></head><body><p>Content</p></body></html>"
        )
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_haiku.return_value = "Content"
        base_args = create_test_base_args(owner="test-owner", repo="test-repo")

        web_fetch(base_args, "https://example.com", "Summarize")

        mock_slack.assert_called_once()
        call_text = mock_slack.call_args[0][0]
        assert "test-owner/test-repo" in call_text
        assert "https://example.com" in call_text

    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_passes_prompt_to_haiku(
        self, _mock_slack, mock_get, mock_haiku, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = (
            "<html><head><title>API Docs</title></head>"
            "<body><main><p>API documentation here</p></main></body></html>"
        )
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_haiku.return_value = "API endpoint details"
        base_args = create_test_base_args()

        result = web_fetch(
            base_args,
            "https://example.com/api",
            "What are the available API endpoints?",
        )

        assert result is not None
        call_args = mock_haiku.call_args
        user_input = call_args[1]["user_input"]
        assert "What are the available API endpoints?" in user_input
        assert "API documentation here" in user_input

    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.requests.get")
    @patch("services.http.web_fetch.slack_notify")
    def test_web_fetch_uses_haiku_model(
        self, _mock_slack, mock_get, mock_haiku, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = "<html><body><p>Content</p></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_haiku.return_value = "Content"
        base_args = create_test_base_args()

        web_fetch(base_args, "https://example.com", "Summarize")

        call_args = mock_haiku.call_args
        assert call_args[1]["model_id"] == "claude-haiku-4-5"


class TestWebFetchIntegration:
    """Integration tests with real HTTP calls, only mocking slack_notify and Haiku."""

    @pytest.mark.integration
    @patch(MOCK_HAIKU_PATH)
    @patch("services.http.web_fetch.slack_notify")
    def test_real_fetch_returns_summarized_content(
        self, _mock_slack, mock_haiku, create_test_base_args
    ):
        mock_haiku.return_value = (
            "Python json module documentation for encoding and decoding JSON data."
        )
        base_args = create_test_base_args()

        result = web_fetch(
            base_args,
            "https://docs.python.org/3/library/json.html",
            "What is this documentation about?",
        )

        assert result is not None
        assert result["title"]
        assert result["url"] == "https://docs.python.org/3/library/json.html"
        assert "json" in result["content"].lower()
        # Verify Haiku was called with real page content
        call_args = mock_haiku.call_args
        user_input = call_args[1]["user_input"]
        assert "json" in user_input.lower()


class TestConstants:
    """Test cases for web_fetch constants."""

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
