# pyright: reportUnusedVariable=false
# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import re
from unittest.mock import patch

import pytest

from services.duckduckgo.web_search import web_search


class TestWebSearch:
    """Test cases for web_search function."""

    def test_web_search_empty_query(self, create_test_base_args):
        base_args = create_test_base_args()
        result = web_search(base_args, "")
        assert not result

    @patch("services.duckduckgo.web_search.slack_notify")
    @patch("services.duckduckgo.web_search.search_urls")
    def test_web_search_success_returns_search_results(
        self, mock_search_urls, _mock_slack, create_test_base_args
    ):
        base_args = create_test_base_args()
        mock_search_urls.return_value = [
            {
                "title": "Test Title",
                "description": "Test Desc",
                "url": "https://example.com",
            }
        ]

        result = web_search(base_args, "test query")

        assert len(result) == 1
        assert result[0]["title"] == "Test Title"
        assert result[0]["url"] == "https://example.com"
        assert result[0]["description"] == "Test Desc"

    @patch("services.duckduckgo.web_search.slack_notify")
    @patch("services.duckduckgo.web_search.search_urls")
    def test_web_search_no_urls_found(
        self, mock_search_urls, _mock_slack, create_test_base_args
    ):
        base_args = create_test_base_args()
        mock_search_urls.return_value = []

        result = web_search(base_args, "test query")

        assert not result

    @patch("services.duckduckgo.web_search.slack_notify")
    @patch("services.duckduckgo.web_search.search_urls")
    def test_web_search_exception_handling(
        self, mock_search_urls, _mock_slack, create_test_base_args
    ):
        base_args = create_test_base_args()
        mock_search_urls.side_effect = Exception("Search failed")

        result = web_search(base_args, "test query")

        assert not result

    def test_web_search_with_falsy_query_values(self, create_test_base_args):
        base_args = create_test_base_args()
        for falsy_value in ["", None, 0, False, [], {}]:
            result = web_search(base_args, falsy_value)
            assert not result, f"Expected [] for falsy query value: {falsy_value}"


@pytest.mark.skip(
    reason="DDG serves CAPTCHAs to automated requests, search_web disabled"
)
class TestWebSearchIntegration:
    """Integration tests with real DuckDuckGo search, only mocking slack_notify."""

    @pytest.mark.integration
    @patch("services.duckduckgo.web_search.slack_notify")
    def test_real_search_python_requests_returns_multiple_results(
        self, mock_slack, create_test_base_args
    ):
        base_args = create_test_base_args(owner="test-owner", repo="test-repo")

        result = web_search(base_args, "python requests library")

        assert len(result) == 10
        for r in result:
            assert r["url"].startswith("http")
            assert r["title"]
        # At least one result must mention "requests" (live integration data, regex match)
        combined = " ".join(
            r["title"] + r["description"] + r["url"] for r in result
        ).lower()
        assert re.search(r"requests", combined) is not None
        # Slack notification text is deterministic — assert exact value.
        mock_slack.assert_called_once_with(
            "🔍 Web search in `test-owner/test-repo`:\n"
            "Query: `python requests library`\n"
            "Results: 10"
        )

    @pytest.mark.integration
    @patch("services.duckduckgo.web_search.slack_notify")
    def test_real_search_github_actions_returns_relevant_results(
        self, mock_slack, create_test_base_args
    ):
        base_args = create_test_base_args(owner="org", repo="repo")

        result = web_search(base_args, "github actions checkout repository")

        assert len(result) >= 1
        combined = " ".join(
            r["title"] + r["description"] + r["url"] for r in result
        ).lower()
        assert re.search(r"checkout|github", combined) is not None
        mock_slack.assert_called_once()
