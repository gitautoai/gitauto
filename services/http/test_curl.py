# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import Mock, patch

import pytest
import requests

from constants.requests import USER_AGENT
from services.http.curl import MAX_CURL_CHARS, curl

HTML_SUFFIX = (
    "\n\n[HTML page detected — tags stripped. "
    "For better results, use web_fetch instead.]"
)


def _truncation_suffix(raw_len: int):
    return (
        f"\n\n[Truncated from {raw_len:,} to {MAX_CURL_CHARS:,} chars. "
        "Use web_fetch for full HTML page summarization.]"
    )


class TestCurl:
    @patch("services.http.curl.requests.get")
    @patch("services.http.curl.slack_notify")
    def test_curl_returns_raw_json(self, _mock_slack, mock_get, create_test_base_args):
        mock_response = Mock()
        mock_response.text = '{"key": "value", "count": 42}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = curl(base_args, "https://api.example.com/data")

        assert result == '{"key": "value", "count": 42}'

    @patch("services.http.curl.requests.get")
    @patch("services.http.curl.slack_notify")
    def test_curl_strips_html_tags(self, _mock_slack, mock_get, create_test_base_args):
        html_content = "<html><body><p>Hello World</p></body></html>"
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = curl(base_args, "https://example.com")

        assert result == "Hello World" + HTML_SUFFIX

    @patch("services.http.curl.requests.get")
    @patch("services.http.curl.slack_notify")
    def test_curl_truncates_large_response(
        self, _mock_slack, mock_get, create_test_base_args
    ):
        large_content = "x" * 50_000
        mock_response = Mock()
        mock_response.text = large_content
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = curl(base_args, "https://example.com/big.txt")

        assert result == ("x" * MAX_CURL_CHARS) + _truncation_suffix(50_000)

    @patch("services.http.curl.requests.get")
    @patch("services.http.curl.slack_notify")
    def test_curl_strips_html_then_truncates(
        self, _mock_slack, mock_get, create_test_base_args
    ):
        # HTML with CSS that was costing $16/run before we stripped and truncated it.
        css = "<style>" + ".c{" + "color:red;" * 10000 + "}</style>"
        body_text = "A" * 20_000
        html = f"<!DOCTYPE html><html><head>{css}</head><body>{body_text}</body></html>"
        raw_len = len(html)
        mock_response = Mock()
        mock_response.text = html
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = curl(
            base_args, "https://circleci.com/developer/orbs/orb/circleci/node"
        )

        # After strip_html: "A" * 20_000 (CSS inside <style> removed, tags removed).
        # Suffix order in curl.py: HTML notice is prepended in front of the
        # truncation notice, so the final string is content + html + trunc.
        stripped = "A" * 20_000
        truncated = stripped[:MAX_CURL_CHARS]
        expected = truncated + HTML_SUFFIX + _truncation_suffix(raw_len)
        assert result == expected

    @patch("services.http.curl.requests.get")
    @patch("services.http.curl.slack_notify")
    def test_curl_returns_raw_text(self, _mock_slack, mock_get, create_test_base_args):
        mock_response = Mock()
        mock_response.text = "line1\nline2\nline3"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = curl(base_args, "https://example.com/file.txt")

        assert result == "line1\nline2\nline3"

    @patch("services.http.curl.requests.get")
    @patch("services.http.curl.slack_notify")
    def test_curl_http_error(self, _mock_slack, mock_get, create_test_base_args):
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.HTTPError("HTTP Error")
        http_error.response = mock_response
        mock_get.side_effect = http_error
        base_args = create_test_base_args()

        result = curl(base_args, "https://example.com/404")

        assert result is None

    @patch("services.http.curl.requests.get")
    @patch("services.http.curl.slack_notify")
    def test_curl_sends_slack_notification(
        self, mock_slack, mock_get, create_test_base_args
    ):
        mock_response = Mock()
        mock_response.text = "response content"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args(owner="test-owner", repo="test-repo")

        curl(base_args, "https://api.example.com/endpoint")

        mock_slack.assert_called_once_with(
            "🌐 Curl: `https://api.example.com/endpoint` (16 raw, 16 final)",
            base_args.get("slack_thread_ts"),
        )

    @patch("services.http.curl.requests.get")
    @patch("services.http.curl.slack_notify")
    def test_curl_adds_bearer_for_github_api_when_token_present(
        self, _mock_slack, mock_get, create_test_base_args
    ):
        """AGENT-35Y/35X: curl on api.github.com for a private repo must send
        the installation token or GitHub returns 404."""
        mock_response = Mock()
        mock_response.text = '{"name": "file.ts"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args(token="ghs_installation_token")

        curl(
            base_args,
            "https://api.github.com/repos/Foxquilt/foxden-billing/contents/x.ts?ref=abc",
        )

        sent_headers = mock_get.call_args.kwargs["headers"]
        assert sent_headers == {
            "User-Agent": USER_AGENT,
            "Authorization": "Bearer ghs_installation_token",
        }

    @patch("services.http.curl.requests.get")
    @patch("services.http.curl.slack_notify")
    def test_curl_does_not_leak_token_to_non_github_hosts(
        self, _mock_slack, mock_get, create_test_base_args
    ):
        """Never send the installation token to arbitrary third-party URLs."""
        mock_response = Mock()
        mock_response.text = "hello"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args(token="ghs_installation_token")

        curl(base_args, "https://httpbin.org/get")

        sent_headers = mock_get.call_args.kwargs["headers"]
        assert sent_headers == {"User-Agent": USER_AGENT}


class TestCurlIntegration:
    @pytest.mark.integration
    @patch("services.http.curl.slack_notify")
    def test_real_curl_returns_raw_content(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()

        # httpbin.org/get returns a JSON response whose exact bytes vary on
        # every call (IP, user-agent headers echoed back). Assert the response
        # is a non-empty string and parses as JSON with an expected shape.
        result = curl(base_args, "https://httpbin.org/get")
        assert isinstance(result, str)
        assert result != ""
        import json  # pylint: disable=import-outside-toplevel

        parsed = json.loads(result)
        assert set(parsed.keys()) >= {"args", "headers", "url"}
