# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock, patch

import pytest

from scripts.sentry.resolve_issue import resolve_sentry_issue


@pytest.fixture
def mock_response_200():
    response = MagicMock()
    response.status_code = 200
    return response


@pytest.fixture
def mock_response_403():
    response = MagicMock()
    response.status_code = 403
    return response


@pytest.fixture
def mock_response_404():
    response = MagicMock()
    response.status_code = 404
    return response


@pytest.fixture
def headers():
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json",
    }


class TestResolveSentryIssue:
    @patch("scripts.sentry.resolve_issue.requests.put")
    def test_resolve_issue_success(self, mock_put, mock_response_200, headers, capsys):
        mock_put.return_value = mock_response_200

        result = resolve_sentry_issue("AGENT-229", headers, "my-org")

        assert result is True
        mock_put.assert_called_once_with(
            "https://sentry.io/api/0/organizations/my-org/issues/AGENT-229/",
            headers=headers,
            json={"status": "resolved"},
            timeout=30,
        )
        captured = capsys.readouterr()
        assert "AGENT-229" in captured.out
        assert "done" in captured.out

    @patch("scripts.sentry.resolve_issue.requests.put")
    def test_resolve_issue_http_403(self, mock_put, mock_response_403, headers, capsys):
        mock_put.return_value = mock_response_403

        result = resolve_sentry_issue("AGENT-229", headers, "my-org")

        assert result is False
        captured = capsys.readouterr()
        assert "failed" in captured.out
        assert "403" in captured.out

    @patch("scripts.sentry.resolve_issue.requests.put")
    def test_resolve_issue_http_404(self, mock_put, mock_response_404, headers, capsys):
        mock_put.return_value = mock_response_404

        result = resolve_sentry_issue("AGENT-22A", headers, "my-org")

        assert result is False
        captured = capsys.readouterr()
        assert "failed" in captured.out
        assert "404" in captured.out

    @patch("scripts.sentry.resolve_issue.requests.put")
    def test_resolve_issue_url_contains_org_and_issue_id(
        self, mock_put, mock_response_200, headers
    ):
        mock_put.return_value = mock_response_200

        resolve_sentry_issue("AGENT-XYZ", headers, "acme-corp")

        call_args = mock_put.call_args
        assert "acme-corp" in call_args[0][0]
        assert "AGENT-XYZ" in call_args[0][0]

    @patch("scripts.sentry.resolve_issue.requests.put")
    def test_resolve_issue_payload_sets_status_resolved(
        self, mock_put, mock_response_200, headers
    ):
        mock_put.return_value = mock_response_200

        resolve_sentry_issue("AGENT-001", headers, "my-org")

        call_kwargs = mock_put.call_args[1]
        assert call_kwargs["json"] == {"status": "resolved"}

    @patch("scripts.sentry.resolve_issue.requests.put")
    def test_resolve_issue_timeout_is_30(self, mock_put, mock_response_200, headers):
        mock_put.return_value = mock_response_200

        resolve_sentry_issue("AGENT-001", headers, "my-org")

        call_kwargs = mock_put.call_args[1]
        assert call_kwargs["timeout"] == 30

    @patch("scripts.sentry.resolve_issue.requests.put")
    def test_resolve_issue_prints_issue_id_before_request(
        self, mock_put, mock_response_200, headers, capsys
    ):
        mock_put.return_value = mock_response_200

        resolve_sentry_issue("AGENT-999", headers, "my-org")

        captured = capsys.readouterr()
        assert "AGENT-999" in captured.out

    @patch("scripts.sentry.resolve_issue.requests.put")
    def test_resolve_issue_http_500_returns_false(self, mock_put, headers, capsys):
        response = MagicMock()
        response.status_code = 500
        mock_put.return_value = response

        result = resolve_sentry_issue("AGENT-500", headers, "my-org")

        assert result is False
        captured = capsys.readouterr()
        assert "500" in captured.out
