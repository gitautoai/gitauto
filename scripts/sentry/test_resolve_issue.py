# pylint: disable=redefined-outer-name, unused-argument
import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

from scripts.sentry.resolve_issue import resolve_sentry_issue

MOCK_HEADERS = {
    "Authorization": "Bearer test-token",
    "Content-Type": "application/json",
}
MOCK_ORG = "test-org"


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_success(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    result = resolve_sentry_issue("AGENT-123", MOCK_HEADERS, MOCK_ORG)

    assert result is True
    mock_put.assert_called_once_with(
        "https://sentry.io/api/0/organizations/test-org/issues/AGENT-123/",
        headers=MOCK_HEADERS,
        json={"status": "resolved"},
        timeout=30,
    )


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_failure_404(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_put.return_value = mock_response

    result = resolve_sentry_issue("AGENT-999", MOCK_HEADERS, MOCK_ORG)

    assert result is False


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_failure_500(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_put.return_value = mock_response

    result = resolve_sentry_issue("AGENT-500", MOCK_HEADERS, MOCK_ORG)

    assert result is False


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_failure_401(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_put.return_value = mock_response

    result = resolve_sentry_issue("AGENT-401", MOCK_HEADERS, MOCK_ORG)

    assert result is False


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_url_construction_with_custom_org(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    resolve_sentry_issue("MY-ISSUE-42", MOCK_HEADERS, "custom-org")

    call_url = mock_put.call_args[0][0]
    assert (
        call_url
        == "https://sentry.io/api/0/organizations/custom-org/issues/MY-ISSUE-42/"
    )


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_sends_resolved_payload(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    resolve_sentry_issue("AGENT-1", MOCK_HEADERS, MOCK_ORG)

    call_kwargs = mock_put.call_args[1]
    assert call_kwargs["json"] == {"status": "resolved"}


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_prints_done_on_success(mock_put, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    resolve_sentry_issue("AGENT-1", MOCK_HEADERS, MOCK_ORG)

    captured = capsys.readouterr()
    assert "Resolving AGENT-1..." in captured.out
    assert "done" in captured.out


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_prints_failed_with_status_code(mock_put, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_put.return_value = mock_response

    resolve_sentry_issue("AGENT-1", MOCK_HEADERS, MOCK_ORG)

    captured = capsys.readouterr()
    assert "Resolving AGENT-1..." in captured.out
    assert "failed (HTTP 403)" in captured.out


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_passes_custom_headers(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    custom_headers = {"Authorization": "Bearer custom-token", "X-Custom": "value"}
    resolve_sentry_issue("AGENT-1", custom_headers, MOCK_ORG)

    call_kwargs = mock_put.call_args[1]
    assert call_kwargs["headers"] == custom_headers


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_uses_30s_timeout(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    resolve_sentry_issue("AGENT-1", MOCK_HEADERS, MOCK_ORG)

    call_kwargs = mock_put.call_args[1]
    assert call_kwargs["timeout"] == 30


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_empty_issue_id(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    result = resolve_sentry_issue("", MOCK_HEADERS, MOCK_ORG)

    assert result is True
    call_url = mock_put.call_args[0][0]
    assert call_url == "https://sentry.io/api/0/organizations/test-org/issues//"


def test_main_missing_env_vars_exits_with_error():
    clean_env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": ".",
        "HOME": os.environ.get("HOME", ""),
        # Set empty values so load_dotenv(override=False) won't load from .env
        "SENTRY_PERSONAL_TOKEN": "",
        "SENTRY_ORG_SLUG": "",
    }
    result = subprocess.run(
        [sys.executable, "-m", "scripts.sentry.resolve_issue", "AGENT-1"],
        capture_output=True,
        check=False,
        text=True,
        env=clean_env,
        timeout=10,
    )

    assert result.returncode == 1
    assert "SENTRY_PERSONAL_TOKEN" in result.stdout


def test_main_no_args_exits_with_error():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.sentry.resolve_issue"],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )

    assert result.returncode != 0
