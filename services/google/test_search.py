from unittest.mock import Mock, patch
import pytest
import requests

from services.google.search import (
    search_urls,
    scrape_content_from_url,
    google_search,
    NUM_RESULTS_DEFAULT,
    UNNECESSARY_TAGS,
)


@pytest.fixture
def mock_search_result():
    """Fixture for mock search result object."""
    result = Mock()
    result.title = "Test Title"
    result.description = "Test Description"
    result.url = "https://example.com"
    return result


class TestSearchUrls:
    """Test cases for search_urls function."""

    @patch("services.google.search.search")
    def test_search_urls_success_single_result(self, mock_search, mock_search_result):
        """Test successful search with single result."""
        mock_search.return_value = [mock_search_result]

        result = search_urls("test query")

        assert len(result) == 1
        assert result[0]["title"] == "Test Title"
        assert result[0]["description"] == "Test Description"
        assert result[0]["url"] == "https://example.com"
        mock_search.assert_called_once_with(
            term="test query",
            num_results=NUM_RESULTS_DEFAULT,
            lang="en",
            safe=None,
            advanced=True,
        )

    @patch("services.google.search.search")
    def test_search_urls_success_multiple_results(self, mock_search):
        """Test successful search with multiple results."""
        result1 = Mock()
        result1.title = "Title 1"
        result1.description = "Description 1"
        result1.url = "https://example1.com"

        result2 = Mock()
        result2.title = "Title 2"
        result2.description = "Description 2"
        result2.url = "https://example2.com"

        mock_search.return_value = [result1, result2]

        result = search_urls("test query", num_results=2)

        assert len(result) == 2
        assert result[0]["title"] == "Title 1"
        assert result[1]["title"] == "Title 2"

    @patch("services.google.search.search")
    def test_search_urls_with_custom_params(self, mock_search, mock_search_result):
        """Test search with custom parameters."""
        mock_search.return_value = [mock_search_result]

        result = search_urls("test query", num_results=5, lang="fr")

        assert len(result) == 1
        mock_search.assert_called_once_with(
            term="test query", num_results=5, lang="fr", safe=None, advanced=True
        )

    @patch("services.google.search.search")
    def test_search_urls_empty_results(self, mock_search):
        """Test search with no results."""
        mock_search.return_value = []

        result = search_urls("test query")

        assert result == []

    @patch("services.google.search.search")
    def test_search_urls_exception_handling(self, mock_search):
        """Test search with exception (handled by decorator)."""
        mock_search.side_effect = Exception("Search failed")

        result = search_urls("test query")

        # Should return default value [] due to handle_exceptions decorator
        assert result == []


class TestScrapeContentFromUrl:
    """Test cases for scrape_content_from_url function."""

    @patch("services.google.search.get")
    @patch("builtins.print")
    def test_scrape_content_success(self, mock_print, mock_get):
        """Test successful content scraping."""
        html_content = """
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

        mock_response = Mock()
        mock_response.text = html_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scrape_content_from_url("https://example.com")

        assert result is not None
        assert result["title"] == "Test Page Title"
        assert result["url"] == "https://example.com"
        assert "Main Article Title" in result["content"]
        assert "main content of the article" in result["content"]

        # Verify print calls
        assert mock_print.call_count == 2

    @patch("services.google.search.get")
    @patch("builtins.print")
    def test_scrape_content_no_title(self, mock_print, mock_get):
        """Test scraping content without title."""
        html_no_title = """
        <html>
            <body>
                <div>Content without title</div>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = html_no_title
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scrape_content_from_url("https://example.com")

        assert result is not None
        assert result["title"] == ""
        assert result["url"] == "https://example.com"
        assert "Content without title" in result["content"]

    @patch("services.google.search.get")
    @patch("builtins.print")
    def test_scrape_content_with_main_tag(self, mock_print, mock_get):
        """Test scraping content with main tag."""
        html_with_main = """
        <html>
            <head><title>Page with Main</title></head>
            <body>
                <main>
                    <p>Main content here</p>
                </main>
                <div>Other content</div>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = html_with_main
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scrape_content_from_url("https://example.com")

        assert result is not None
        assert result["title"] == "Page with Main"
        assert "Main content here" in result["content"]
        # Should not contain content outside main tag
        assert "Other content" not in result["content"]

    @patch("services.google.search.get")
    @patch("builtins.print")
    def test_scrape_content_with_article_tag(self, mock_print, mock_get):
        """Test scraping content with article tag."""
        html_with_article = """
        <html>
            <head><title>Page with Article</title></head>
            <body>
                <article>
                    <p>Article content here</p>
                </article>
                <div>Other content</div>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = html_with_article
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scrape_content_from_url("https://example.com")

        assert result is not None
        assert result["title"] == "Page with Article"
        assert "Article content here" in result["content"]
        # Should not contain content outside article tag
        assert "Other content" not in result["content"]

    @patch("services.google.search.get")
    @patch("builtins.print")
    def test_scrape_content_removes_unnecessary_tags(self, mock_print, mock_get):
        """Test that unnecessary tags are removed."""
        html_with_unnecessary_tags = """
        <html>
            <head>
                <title>Test Title</title>
                <script>console.log('should be removed');</script>
                <style>body { color: red; }</style>
            </head>
            <body>
                <header>Header to remove</header>
                <nav>Nav to remove</nav>
                <main>
                    <p>Main content to keep</p>
                </main>
                <aside>Aside to remove</aside>
                <footer>Footer to remove</footer>
                <iframe src="test.html">Iframe to remove</iframe>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = html_with_unnecessary_tags
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scrape_content_from_url("https://example.com")

        assert result is not None
        assert "Main content to keep" in result["content"]
        # Verify unnecessary content is removed
        assert "should be removed" not in result["content"]
        assert "Header to remove" not in result["content"]
        assert "Nav to remove" not in result["content"]
        assert "Aside to remove" not in result["content"]
        assert "Footer to remove" not in result["content"]
        assert "Iframe to remove" not in result["content"]

    @patch("services.google.search.get")
    def test_scrape_content_http_error(self, mock_get):
        """Test scraping with HTTP error."""
        # Create a proper HTTPError with a mock response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Page not found"
        http_error = requests.HTTPError("HTTP Error")
        http_error.response = mock_response
        mock_get.side_effect = http_error

        result = scrape_content_from_url("https://example.com")

        # Should return None due to handle_exceptions decorator
        assert result is None

    @patch("services.google.search.get")
    def test_scrape_content_uses_correct_headers(self, mock_get):
        """Test that correct headers are used in request."""
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        scrape_content_from_url("https://example.com")

        # Verify get was called with correct headers and timeout
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://example.com"
        assert "User-Agent" in call_args[1]["headers"]
        assert "timeout" in call_args[1]

    @patch("services.google.search.get")
    @patch("builtins.print")
    def test_scrape_content_with_whitespace_title(self, mock_print, mock_get):
        """Test scraping content with title that has whitespace."""
        html_with_whitespace_title = """
        <html>
            <head><title>   Title with spaces   </title></head>
            <body><p>Content</p></body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = html_with_whitespace_title
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scrape_content_from_url("https://example.com")

        assert result is not None
        assert result["title"] == "Title with spaces"  # Should be stripped

    @patch("services.google.search.get")
    @patch("builtins.print")
    def test_scrape_content_fallback_to_soup(self, mock_print, mock_get):
        """Test scraping content when no main/article/div[role=main] found."""
        html_without_main = """
        <html>
            <head><title>No Main Content</title></head>
            <body>
                <div>
                    <p>Regular div content</p>
                    <span>Some span content</span>
                </div>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = html_without_main
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scrape_content_from_url("https://example.com")

        assert result is not None
        assert "Regular div content" in result["content"]
        assert "Some span content" in result["content"]


class TestGoogleSearch:
    """Test cases for google_search function."""

    def test_google_search_empty_query(self, create_test_base_args):
        """Test google_search with empty query."""
        base_args = create_test_base_args()

        result = google_search(base_args, "")

        assert result == []

    def test_google_search_none_query(self, create_test_base_args):
        """Test google_search with None query."""
        base_args = create_test_base_args()

        result = google_search(base_args, None)

        assert result == []

    @patch("services.google.search.scrape_content_from_url")
    @patch("services.google.search.search_urls")
    def test_google_search_success_single_url(
        self, mock_search_urls, mock_scrape, create_test_base_args
    ):
        """Test successful google_search with single URL."""
        base_args = create_test_base_args()

        mock_search_urls.return_value = [
            {
                "title": "Test Title",
                "description": "Test Desc",
                "url": "https://example.com",
            }
        ]
        mock_scrape.return_value = {
            "title": "Scraped Title",
            "content": "Scraped content",
            "url": "https://example.com",
        }

        result = google_search(base_args, "test query")

        assert len(result) == 1
        assert result[0]["title"] == "Scraped Title"
        assert result[0]["content"] == "Scraped content"

        mock_search_urls.assert_called_once_with(
            query="test query", num_results=NUM_RESULTS_DEFAULT, lang="en"
        )
        mock_scrape.assert_called_once_with("https://example.com")

    @patch("services.google.search.scrape_content_from_url")
    @patch("services.google.search.search_urls")
    def test_google_search_success_multiple_urls(
        self, mock_search_urls, mock_scrape, create_test_base_args
    ):
        """Test successful google_search with multiple URLs."""
        base_args = create_test_base_args()

        mock_search_urls.return_value = [
            {
                "title": "Title 1",
                "description": "Desc 1",
                "url": "https://example1.com",
            },
            {
                "title": "Title 2",
                "description": "Desc 2",
                "url": "https://example2.com",
            },
        ]
        mock_scrape.side_effect = [
            {
                "title": "Scraped Title 1",
                "content": "Content 1",
                "url": "https://example1.com",
            },
            {
                "title": "Scraped Title 2",
                "content": "Content 2",
                "url": "https://example2.com",
            },
        ]

        result = google_search(base_args, "test query", num_results=2)

        assert len(result) == 2
        assert result[0]["title"] == "Scraped Title 1"
        assert result[1]["title"] == "Scraped Title 2"

        mock_search_urls.assert_called_once_with(
            query="test query", num_results=2, lang="en"
        )
        assert mock_scrape.call_count == 2

    @patch("services.google.search.scrape_content_from_url")
    @patch("services.google.search.search_urls")
    def test_google_search_no_urls_found(
        self, mock_search_urls, mock_scrape, create_test_base_args
    ):
        """Test google_search when no URLs are found."""
        base_args = create_test_base_args()

        mock_search_urls.return_value = []

        result = google_search(base_args, "test query")

        assert result == []
        mock_scrape.assert_not_called()

    @patch("services.google.search.scrape_content_from_url")
    @patch("services.google.search.search_urls")
    def test_google_search_exception_handling(
        self, mock_search_urls, mock_scrape, create_test_base_args
    ):
        """Test google_search with exception."""
        base_args = create_test_base_args()

        mock_search_urls.side_effect = Exception("Search failed")

        result = google_search(base_args, "test query")

        # Should return default value [] due to handle_exceptions decorator
        assert result == []

    def test_google_search_with_falsy_query_values(self, create_test_base_args):
        """Test google_search with various falsy query values."""
        base_args = create_test_base_args()

        falsy_values = ["", None, 0, False, [], {}]

        for falsy_value in falsy_values:
            result = google_search(base_args, falsy_value)
            assert result == [], f"Expected [] for falsy query value: {falsy_value}"


class TestConstants:
    """Test cases for module constants."""

    def test_num_results_default(self):
        """Test NUM_RESULTS_DEFAULT constant."""
        assert NUM_RESULTS_DEFAULT == 1
        assert isinstance(NUM_RESULTS_DEFAULT, int)

    def test_unnecessary_tags(self):
        """Test UNNECESSARY_TAGS constant."""
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
        assert isinstance(UNNECESSARY_TAGS, list)
        assert all(isinstance(tag, str) for tag in UNNECESSARY_TAGS)
