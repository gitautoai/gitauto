import unittest
from unittest.mock import patch, MagicMock, Mock
from bs4 import BeautifulSoup

from services.google.search import (
    search_urls,
    scrape_content_from_url,
    google_search,
    NUM_RESULTS_DEFAULT,
    UNNECESSARY_TAGS,
)
from services.github.github_types import BaseArgs
from tests.constants import OWNER, REPO


def test_search_urls_success():
    mock_result = MagicMock()
    mock_result.title = "Test Title"
    mock_result.description = "Test Description"
    mock_result.url = "https://example.com"
    
    with patch("services.google.search.search", return_value=[mock_result]):
        results = search_urls("test query")
        
        assert len(results) == 1
        assert results[0]["title"] == "Test Title"
        assert results[0]["description"] == "Test Description"
        assert results[0]["url"] == "https://example.com"


def test_search_urls_multiple_results():
    mock_results = []
    for i in range(3):
        mock_result = MagicMock()
        mock_result.title = f"Test Title {i}"
        mock_result.description = f"Test Description {i}"
        mock_result.url = f"https://example{i}.com"
        mock_results.append(mock_result)
    
    with patch("services.google.search.search", return_value=mock_results):
        results = search_urls("test query", num_results=3)
        
        assert len(results) == 3
        for i in range(3):
            assert results[i]["title"] == f"Test Title {i}"
            assert results[i]["description"] == f"Test Description {i}"
            assert results[i]["url"] == f"https://example{i}.com"


def test_search_urls_empty_results():
    with patch("services.google.search.search", return_value=[]):
        results = search_urls("test query")
        
        assert results == []


def test_search_urls_exception():
    with patch("services.google.search.search", side_effect=Exception("Test exception")):
        results = search_urls("test query")
        
        assert results == []


def test_scrape_content_from_url_success():
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <head>
            <title>Test Page</title>
            <script>console.log('test');</script>
            <style>.test{color:red;}</style>
        </head>
        <body>
            <header>Header content</header>
            <main>
                <p>Main content paragraph</p>
                <div>More content</div>
            </main>
            <footer>Footer content</footer>
        </body>
    </html>
    """
    
    with patch("services.google.search.get", return_value=mock_response), \
         patch("services.google.search.print"):  # Suppress print statements
        result = scrape_content_from_url("https://example.com")
        
        assert result["title"] == "Test Page"
        assert "Main content paragraph" in result["content"]
        assert "More content" in result["content"]
        assert "Header content" not in result["content"]
        assert "Footer content" not in result["content"]
        assert result["url"] == "https://example.com"


def test_scrape_content_from_url_no_title():
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <body>
            <main>
                <p>Main content paragraph</p>
            </main>
        </body>
    </html>
    """
    
    with patch("services.google.search.get", return_value=mock_response), \
         patch("services.google.search.print"):  # Suppress print statements
        result = scrape_content_from_url("https://example.com")
        
        assert result["title"] == ""
        assert "Main content paragraph" in result["content"]
        assert result["url"] == "https://example.com"


def test_scrape_content_from_url_no_main_content():
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <p>Some paragraph</p>
            <div>Some div content</div>
        </body>
    </html>
    """
    
    with patch("services.google.search.get", return_value=mock_response), \
         patch("services.google.search.print"):  # Suppress print statements
        result = scrape_content_from_url("https://example.com")
        
        assert result["title"] == "Test Page"
        assert "Some paragraph" in result["content"]
        assert "Some div content" in result["content"]
        assert result["url"] == "https://example.com"


def test_scrape_content_from_url_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP Error")
    
    with patch("services.google.search.get", return_value=mock_response):
        result = scrape_content_from_url("https://example.com")
        
        assert result is None


def test_scrape_content_from_url_request_exception():
    with patch("services.google.search.get", side_effect=Exception("Request failed")):
        result = scrape_content_from_url("https://example.com")
        
        assert result is None


def test_google_search_success():
    base_args = BaseArgs(owner=OWNER, repo=REPO, token="test_token")
    mock_search_result = [{"title": "Test", "description": "Test Desc", "url": "https://example.com"}]
    mock_scrape_result = {"title": "Test Page", "content": "Test content", "url": "https://example.com"}
    
    with patch("services.google.search.search_urls", return_value=mock_search_result), \
         patch("services.google.search.scrape_content_from_url", return_value=mock_scrape_result):
        results = google_search(base_args, "test query")
        
        assert len(results) == 1
        assert results[0]["title"] == "Test Page"
        assert results[0]["content"] == "Test content"
        assert results[0]["url"] == "https://example.com"


def test_google_search_multiple_results():
    base_args = BaseArgs(owner=OWNER, repo=REPO, token="test_token")
    mock_search_results = [
        {"title": f"Test {i}", "description": f"Test Desc {i}", "url": f"https://example{i}.com"}
        for i in range(3)
    ]
    
    def mock_scrape_side_effect(url):
        i = url.replace("https://example", "").replace(".com", "")
        return {
            "title": f"Test Page {i}",
            "content": f"Test content {i}",
            "url": url
        }
    
    with patch("services.google.search.search_urls", return_value=mock_search_results), \
         patch("services.google.search.scrape_content_from_url", side_effect=mock_scrape_side_effect):
        results = google_search(base_args, "test query", num_results=3)
        
        assert len(results) == 3
        for i in range(3):
            assert results[i]["title"] == f"Test Page {i}"
            assert results[i]["content"] == f"Test content {i}"
            assert results[i]["url"] == f"https://example{i}.com"


def test_google_search_empty_query():
    base_args = BaseArgs(owner=OWNER, repo=REPO, token="test_token")
    
    results = google_search(base_args, "")
    
    assert results == []


def test_google_search_scrape_failure():
    base_args = BaseArgs(owner=OWNER, repo=REPO, token="test_token")
    mock_search_result = [{"title": "Test", "description": "Test Desc", "url": "https://example.com"}]
    
    with patch("services.google.search.search_urls", return_value=mock_search_result), \
         patch("services.google.search.scrape_content_from_url", return_value=None):
        results = google_search(base_args, "test query")
        
        assert len(results) == 1
        assert results[0] is None


def test_google_search_search_exception():
    base_args = BaseArgs(owner=OWNER, repo=REPO, token="test_token")
    
    with patch("services.google.search.search_urls", side_effect=Exception("Search failed")):
        results = google_search(base_args, "test query")
        
        assert results == []


def test_unnecessary_tags_removal():
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <script>console.log('test');</script>
            <style>.test{color:red;}</style>
            <meta name="description" content="Test">
            <link rel="stylesheet" href="style.css">
        </head>
        <body>
            <header>Header content</header>
            <nav>Navigation</nav>
            <main>
                <p>Main content paragraph</p>
                <div>More content</div>
                <iframe src="test.html"></iframe>
                <svg width="100" height="100"></svg>
                <aside>Sidebar content</aside>
                <noscript>Enable JavaScript</noscript>
            </main>
            <footer>Footer content</footer>
            <div class="ads">Advertisement</div>
            <div class="advertisement">Another ad</div>
        </body>
    </html>
    """
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Test that all unnecessary tags are defined
    for tag in ["script", "style", "meta", "link", "header", "nav", "iframe", 
                "svg", "aside", "noscript", "footer", "ads", "advertisement"]:
        assert tag in UNNECESSARY_TAGS or any(tag in t for t in UNNECESSARY_TAGS)
    
    # Test tag removal
    for element in soup(UNNECESSARY_TAGS):
        element.decompose()
    
    # Verify tags were removed
    assert soup.find("script") is None
    assert soup.find("style") is None
    assert soup.find("meta") is None
    assert soup.find("link") is None
    assert soup.find("header") is None
    assert soup.find("nav") is None
    assert soup.find("iframe") is None
    assert soup.find("svg") is None
    assert soup.find("aside") is None
    assert soup.find("noscript") is None
    assert soup.find("footer") is None
    
    # Verify content remains
    assert "Main content paragraph" in soup.get_text()
    assert "More content" in soup.get_text()