# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import Mock, patch

import pytest

from services.duckduckgo.search_urls import DDG_URL, NUM_RESULTS_DEFAULT, search_urls


@pytest.mark.skip(reason="DDG serves CAPTCHAs to automated requests, search_web disabled")
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
