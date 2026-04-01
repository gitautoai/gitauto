# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import Mock, patch

import pytest
from services.duckduckgo.search_urls import (DDG_URL, NUM_RESULTS_DEFAULT,
                                             search_urls)


@pytest.mark.skip(
    reason="DDG serves CAPTCHAs to automated requests, search_web disabled"
)
class TestSearchUrls:
    """Test cases for search_urls function."""

    @pytest.mark.integration
    def test_search_urls_returns_expected_count(self):
        result = search_urls("python requests library")
        assert len(result) == NUM_RESULTS_DEFAULT
        for r in result:
            assert r["title"]
            assert r["url"].startswith("http")

    @pytest.mark.integration
    def test_search_urls_results_have_distinct_urls(self):
        result = search_urls("python requests library")
        urls = [r["url"] for r in result]
        assert len(set(urls)) == NUM_RESULTS_DEFAULT

    @pytest.mark.integration
    def test_search_urls_results_are_relevant(self):
        result = search_urls("python requests library")
        combined = " ".join(
            r["title"] + r["description"] + r["url"] for r in result
        ).lower()
        assert "requests" in combined

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_search_urls_exception_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        result = search_urls("test query")
        assert not result

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_search_urls_parses_ddg_html(self, mock_get):
        # Real DuckDuckGo HTML structure captured 2026-03-23
        mock_response = Mock()
        mock_response.text = """
        <html><body>
            <div class="results">
                <div class="result">
                    <h2 class="result__title">
                        <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com&amp;rut=abc">
                            Example Title
                        </a>
                    </h2>
                </div>
            </div>
        </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = search_urls("test query")

        assert len(result) == 1
        assert result[0]["title"] == "Example Title"
        assert result[0]["url"] == "https://example.com"
        mock_get.assert_called_once_with(
            DDG_URL,
            headers=mock_get.call_args[1]["headers"],
            params={"q": "test query", "kl": "us-en"},
            timeout=mock_get.call_args[1]["timeout"],
        )


class TestConstants:
    """Test cases for search_urls constants."""

    def test_num_results_default(self):
        assert NUM_RESULTS_DEFAULT == 10


class TestSearchUrlsUnit:
    """Unit tests for search_urls with mocked HTTP requests."""

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_happy_path_with_ddg_redirect_urls(self, mock_get):
        # Verifies full parsing: DDG redirect extraction, title, description, and URL
        mock_response = Mock()
        mock_response.text = """
        <html><body>
            <div class="result">
                <h2 class="result__title">
                    <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage&amp;rut=x">
                        Example Page
                    </a>
                </h2>
                <a class="result__snippet">A description of the page.</a>
            </div>
            <div class="result">
                <h2 class="result__title">
                    <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fother.com&amp;rut=y">
                        Other Page
                    </a>
                </h2>
                <a class="result__snippet">Another description.</a>
            </div>
        </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = search_urls("test query")

        assert len(result) == 2
        assert result[0]["title"] == "Example Page"
        assert result[0]["url"] == "https://example.com/page"
        assert result[0]["description"] == "A description of the page."
        assert result[1]["title"] == "Other Page"
        assert result[1]["url"] == "https://other.com"
        assert result[1]["description"] == "Another description."

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_no_results_returns_empty_list(self, mock_get):
        # When DDG returns HTML with no result links, should return empty list
        mock_response = Mock()
        mock_response.text = "<html><body><div>No results found</div></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = search_urls("xyznonexistentquery12345")

        assert result == []

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_direct_href_without_ddg_redirect(self, mock_get):
        # When href doesn't contain DDG redirect, use href as-is (branch: line 33 → 38)
        mock_response = Mock()
        mock_response.text = """
        <html><body>
            <div class="result">
                <h2 class="result__title">
                    <a class="result__a" href="https://direct-link.com/page">
                        Direct Link
                    </a>
                </h2>
            </div>
        </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = search_urls("direct query")

        assert len(result) == 1
        assert result[0]["url"] == "https://direct-link.com/page"
        assert result[0]["title"] == "Direct Link"
        assert result[0]["description"] == ""

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_ddg_redirect_without_uddg_param(self, mock_get):
        # When DDG redirect URL lacks uddg param, href stays as original (branch: line 36 → 38)
        mock_response = Mock()
        mock_response.text = """
        <html><body>
            <div class="result">
                <h2 class="result__title">
                    <a class="result__a" href="//duckduckgo.com/l/?rut=abc">
                        No Uddg Param
                    </a>
                </h2>
            </div>
        </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = search_urls("no uddg")

        assert len(result) == 1
        assert result[0]["url"] == "//duckduckgo.com/l/?rut=abc"
        assert result[0]["title"] == "No Uddg Param"

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_no_snippet_tag_parent(self, mock_get):
        # When link has no parent h2, description should be empty (branch: line 42 → 46)
        mock_response = Mock()
        mock_response.text = """
        <html><body>
            <a class="result__a" href="https://orphan-link.com">Orphan Link</a>
        </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = search_urls("orphan")

        assert len(result) == 1
        assert result[0]["title"] == "Orphan Link"
        assert result[0]["description"] == ""
        assert result[0]["url"] == "https://orphan-link.com"

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_snippet_tag_without_sibling_snippet(self, mock_get):
        # When h2 parent exists but no result__snippet sibling (branch: line 44 → 46)
        mock_response = Mock()
        mock_response.text = """
        <html><body>
            <div class="result">
                <h2 class="result__title">
                    <a class="result__a" href="https://no-snippet.com">No Snippet</a>
                </h2>
                <div class="other_class">Not a snippet</div>
            </div>
        </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = search_urls("no snippet")

        assert len(result) == 1
        assert result[0]["title"] == "No Snippet"
        assert result[0]["description"] == ""

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_exception_returns_empty_list(self, mock_get):
        # handle_exceptions decorator catches errors and returns default []
        mock_get.side_effect = Exception("Connection timeout")

        result = search_urls("failing query")

        assert result == []

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_http_error_returns_empty_list(self, mock_get):
        # HTTP errors (e.g., 500) are caught by decorator and return []
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            response=Mock(status_code=500, reason="Server Error", text="Internal Server Error")
        )
        mock_get.return_value = mock_response

        result = search_urls("server error query")

        assert result == []

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_results_capped_at_num_results_default(self, mock_get):
        # Verify only NUM_RESULTS_DEFAULT results are returned even if more links exist
        links_html = ""
        for i in range(15):
            links_html += f"""
            <div class="result">
                <h2 class="result__title">
                    <a class="result__a" href="https://example{i}.com">Title {i}</a>
                </h2>
            </div>
            """
        mock_response = Mock()
        mock_response.text = f"<html><body>{links_html}</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = search_urls("many results")

        assert len(result) == NUM_RESULTS_DEFAULT

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_request_params_are_correct(self, mock_get):
        # Verify the HTTP request is made with correct URL, headers, params, and timeout
        mock_response = Mock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        search_urls("verify params")

        mock_get.assert_called_once_with(
            DDG_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"},
            params={"q": "verify params", "kl": "us-en"},
            timeout=120,
        )

    @patch("services.duckduckgo.search_urls.requests.get")
    def test_link_with_empty_href(self, mock_get):
        # When link has no href attribute, should use empty string as URL
        mock_response = Mock()
        mock_response.text = """
        <html><body>
            <div class="result">
                <h2 class="result__title">
                    <a class="result__a">No Href Link</a>
                </h2>
            </div>
        </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = search_urls("no href")

        assert len(result) == 1
        assert result[0]["url"] == ""
        assert result[0]["title"] == "No Href Link"
