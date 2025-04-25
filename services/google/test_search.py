from unittest.mock import patch, MagicMock
import pytest
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

from tests.constants import OWNER
from services.google.search import (
    search_urls,
    scrape_content_from_url,
    google_search,
    UNNECESSARY_TAGS,
)


def test_search_urls_success():
    mock_result = MagicMock()
    mock_result.title = "Test Title"
    mock_result.description = "Test Description"
    mock_result.url = "https://example.com"

    with patch("services.google.search.search") as mock_search:
        mock_search.return_value = [mock_result]
        results = search_urls("test query", num_results=1)

    assert len(results) == 1
    assert results[0]["title"] == "Test Title"
    assert results[0]["description"] == "Test Description"
    assert results[0]["url"] == "https://example.com"


def test_search_urls_empty_results():
    with patch("services.google.search.search") as mock_search:
        mock_search.return_value = []
        results = search_urls("test query", num_results=1)

    assert results == []


def test_search_urls_error():
    with patch("services.google.search.search") as mock_search:
        mock_search.side_effect = Exception("Search error")
        results = search_urls("test query")

    assert results == []


def test_scrape_content_from_url_success():
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <main>Main content</main>
            <script>alert('test');</script>
            <footer>Footer content</footer>
        </body>
    </html>
    """

    with patch("services.google.search.get") as mock_get:
        mock_get.return_value = mock_response
        result = scrape_content_from_url("https://example.com")

    assert result["title"] == "Test Page"
    assert "Main content" in result["content"]
    assert "alert" not in result["content"]
    assert "Footer content" not in result["content"]


def test_scrape_content_from_url_no_title():
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <body>
            <main>Main content</main>
        </body>
    </html>
    """

    with patch("services.google.search.get") as mock_get:
        mock_get.return_value = mock_response
        result = scrape_content_from_url("https://example.com")

    assert result["title"] == ""
    assert "Main content" in result["content"]


def test_scrape_content_from_url_no_main_content():
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <div>Regular content</div>
        </body>
    </html>
    """

    with patch("services.google.search.get") as mock_get:
        mock_get.return_value = mock_response
        result = scrape_content_from_url("https://example.com")

    assert result["title"] == "Test Page"
    assert "Regular content" in result["content"]


def test_scrape_content_from_url_network_error():
    with patch("services.google.search.get") as mock_get:
        mock_get.side_effect = RequestException("Network error")
        result = scrape_content_from_url("https://example.com")

    assert result is None


def test_scrape_content_from_url_invalid_html():
    mock_response = MagicMock()
    mock_response.text = "Invalid HTML"

    with patch("services.google.search.get") as mock_get:
        mock_get.return_value = mock_response
        result = scrape_content_from_url("https://example.com")

    assert result["title"] == ""
    assert "Invalid HTML" in result["content"]


def test_scrape_content_from_url_removes_unnecessary_tags():
    mock_response = MagicMock()
    html_content = "<html><head><title>Test</title></head><body>"
    for tag in UNNECESSARY_TAGS:
        html_content += f"<{tag}>Should be removed</{tag}>"
    html_content += "<main>Main content</main></body></html>"
    mock_response.text = html_content

    with patch("services.google.search.get") as mock_get:
        mock_get.return_value = mock_response
        result = scrape_content_from_url("https://example.com")

    assert "Should be removed" not in result["content"]
    assert "Main content" in result["content"]


def test_google_search_empty_query():
    result = google_search({"owner": OWNER}, query="", num_results=1)
    assert result == []


def test_google_search_success():
    mock_search_result = [{"title": "Test", "description": "Desc", "url": "https://example.com"}]
    mock_scrape_result = {"title": "Test", "content": "Content", "url": "https://example.com"}

    with patch("services.google.search.search_urls") as mock_search:
        mock_search.return_value = mock_search_result
        with patch("services.google.search.scrape_content_from_url") as mock_scrape:
            mock_scrape.return_value = mock_scrape_result
            result = google_search({"owner": OWNER}, query="test", num_results=1)

    assert len(result) == 1
    assert result[0]["title"] == "Test"
    assert result[0]["content"] == "Content"


def test_google_search_failed_scraping():
    mock_search_result = [{"title": "Test", "description": "Desc", "url": "https://example.com"}]

    with patch("services.google.search.search_urls") as mock_search:
        mock_search.return_value = mock_search_result
        with patch("services.google.search.scrape_content_from_url") as mock_scrape:
            mock_scrape.return_value = None
            result = google_search({"owner": OWNER}, query="test", num_results=1)

    assert len(result) == 1
    assert result[0] is None