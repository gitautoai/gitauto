# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import Mock, patch

import pytest
import requests

from services.http.curl import MAX_CURL_CHARS, curl


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

        assert "<html>" not in result
        assert "<p>" not in result
        assert "Hello World" in result
        assert "HTML page detected" in result

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

        # Should contain truncated content + truncation notice
        assert "Truncated from 50,000" in result
        assert "web_fetch" in result

    @patch("services.http.curl.requests.get")
    @patch("services.http.curl.slack_notify")
    def test_curl_strips_html_then_truncates(
        self, _mock_slack, mock_get, create_test_base_args
    ):
        # 120K of CSS (the real-world scenario that cost $16)
        css = "<style>" + ".c{" + "color:red;" * 10000 + "}</style>"
        body_text = "A" * 20_000
        html = f"<!DOCTYPE html><html><head>{css}</head><body>{body_text}</body></html>"
        mock_response = Mock()
        mock_response.text = html
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        base_args = create_test_base_args()

        result = curl(
            base_args, "https://circleci.com/developer/orbs/orb/circleci/node"
        )

        # CSS should be stripped, body truncated to MAX_CURL_CHARS
        assert "color:red" not in result
        assert len(result) < MAX_CURL_CHARS + 500  # +buffer for suffix messages

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

        mock_slack.assert_called_once()
        call_text = mock_slack.call_args[0][0]
        assert "https://api.example.com/endpoint" in call_text


class TestCurlIntegration:
    @pytest.mark.integration
    @patch("services.http.curl.slack_notify")
    def test_real_curl_returns_raw_content(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()

        # httpbin.org/get returns a JSON response
        result = curl(base_args, "https://httpbin.org/get")

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        assert "headers" in result
