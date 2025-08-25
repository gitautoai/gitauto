# Standard imports
import os
from unittest.mock import patch, MagicMock

# Third party imports
import pytest
import requests

# Local imports
from services.slack.slack_notify import slack_notify


@pytest.fixture
def mock_requests_post():
    """Fixture to mock requests.post method."""
    with patch("services.slack.slack_notify.requests.post") as mock:
        yield mock


@pytest.fixture
def mock_is_prd_true():
    """Fixture to mock IS_PRD as True."""
    with patch("services.slack.slack_notify.IS_PRD", True):
        yield


@pytest.fixture
def mock_is_prd_false():
    """Fixture to mock IS_PRD as False."""
    with patch("services.slack.slack_notify.IS_PRD", False):
        yield


@pytest.fixture
def mock_slack_token():
    """Fixture to mock SLACK_BOT_TOKEN environment variable."""
    with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test-token-123"}):
        with patch(
            "services.slack.slack_notify.SLACK_BOT_TOKEN", "xoxb-test-token-123"
        ):
            yield "xoxb-test-token-123"


@pytest.fixture
def mock_no_slack_token():
    """Fixture to mock missing SLACK_BOT_TOKEN."""
    with patch("services.slack.slack_notify.SLACK_BOT_TOKEN", None):
        yield


def test_slack_notify_success_without_thread(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test successful Slack notification without thread."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
    mock_requests_post.return_value = mock_response

    # Execute
    result = slack_notify("Test message")

    # Assert
    assert result == "1234567890.123456"
    mock_requests_post.assert_called_once_with(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": "Bearer xoxb-test-token-123",
            "Content-Type": "application/json",
        },
        json={"channel": "C08PHH352S3", "text": "Test message"},
        timeout=120,
    )


def test_slack_notify_success_with_thread(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test successful Slack notification with thread."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "ts": "1234567890.654321"}
    mock_requests_post.return_value = mock_response

    # Execute
    result = slack_notify("Reply message", thread_ts="1234567890.123456")

    # Assert
    assert result == "1234567890.654321"
    mock_requests_post.assert_called_once_with(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": "Bearer xoxb-test-token-123",
            "Content-Type": "application/json",
        },
        json={
            "channel": "C08PHH352S3",
            "text": "Reply message",
            "thread_ts": "1234567890.123456",
        },
        timeout=120,
    )


def test_slack_notify_not_production_environment(mock_is_prd_false, mock_slack_token):
    """Test that notification returns None when not in production."""
    # Execute
    result = slack_notify("Test message")

    # Assert
    assert result is None


def test_slack_notify_missing_token(mock_is_prd_true, mock_no_slack_token):
    """Test error handling when SLACK_BOT_TOKEN is not set."""
    # Execute & Assert - should return None due to handle_exceptions decorator
    result = slack_notify("Test message")
    assert result is None


def test_slack_notify_http_error_status_code(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test handling of HTTP error status codes."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_requests_post.return_value = mock_response

    # Execute
    with patch("builtins.print") as mock_print:
        result = slack_notify("Test message")

    # Assert
    assert result is None
    mock_print.assert_called_with("Slack notification failed: 400 Bad Request")


def test_slack_notify_slack_api_error_response(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test handling of Slack API error responses."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": False, "error": "channel_not_found"}
    mock_requests_post.return_value = mock_response

    # Execute
    with patch("builtins.print") as mock_print:
        result = slack_notify("Test message")

    # Assert
    assert result is None
    mock_print.assert_called_with("Slack notification failed: channel_not_found")


def test_slack_notify_requests_exception(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test handling of requests exceptions."""
    # Setup
    mock_requests_post.side_effect = requests.exceptions.RequestException(
        "Network error"
    )

    # Execute
    result = slack_notify("Test message")

    # Assert - should return None due to handle_exceptions decorator
    assert result is None


def test_slack_notify_with_empty_message(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test notification with empty message."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "ts": "1234567890.111111"}
    mock_requests_post.return_value = mock_response

    # Execute
    result = slack_notify("")

    # Assert
    assert result == "1234567890.111111"

    call_args = mock_requests_post.call_args
    assert call_args[1]["json"]["text"] == ""


def test_slack_notify_with_special_characters(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test notification with special characters in message."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "ts": "1234567890.222222"}
    mock_requests_post.return_value = mock_response

    special_message = "Message with émojis 🚀 and special chars: <>&\"'\nNewline\tTab"

    # Execute
    result = slack_notify(special_message)

    # Assert
    assert result == "1234567890.222222"

    call_args = mock_requests_post.call_args
    assert call_args[1]["json"]["text"] == special_message


def test_slack_notify_timeout_parameter(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test that timeout parameter is passed correctly."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "ts": "1234567890.333333"}
    mock_requests_post.return_value = mock_response

    # Execute
    slack_notify("Test message")

    # Assert
    call_args = mock_requests_post.call_args
    assert call_args[1]["timeout"] == 120


def test_slack_notify_channel_parameter(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test that the correct channel is used."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "ts": "1234567890.444444"}
    mock_requests_post.return_value = mock_response

    # Execute
    slack_notify("Test message")

    # Assert
    call_args = mock_requests_post.call_args
    assert call_args[1]["json"]["channel"] == "C08PHH352S3"


def test_slack_notify_headers_structure(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test that headers are structured correctly."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "ts": "1234567890.555555"}
    mock_requests_post.return_value = mock_response

    # Execute
    slack_notify("Test message")

    # Assert
    call_args = mock_requests_post.call_args
    headers = call_args[1]["headers"]

    assert headers["Authorization"] == "Bearer xoxb-test-token-123"
    assert headers["Content-Type"] == "application/json"
    assert len(headers) == 2


def test_slack_notify_json_decode_error(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test handling of JSON decode errors."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests_post.return_value = mock_response

    # Execute
    result = slack_notify("Test message")

    # Assert - should return None due to handle_exceptions decorator
    assert result is None


def test_slack_notify_missing_ts_in_response(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test handling when 'ts' is missing from successful response."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True}  # Missing 'ts'
    mock_requests_post.return_value = mock_response

    # Execute
    result = slack_notify("Test message")

    # Assert
    assert result is None  # get() returns None when key is missing


def test_slack_notify_thread_ts_none_explicitly(
    mock_requests_post, mock_is_prd_true, mock_slack_token
):
    """Test notification with thread_ts explicitly set to None."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "ts": "1234567890.666666"}
    mock_requests_post.return_value = mock_response

    # Execute
    result = slack_notify("Test message", thread_ts=None)

    # Assert
    assert result == "1234567890.666666"

    call_args = mock_requests_post.call_args
    payload = call_args[1]["json"]

    # Verify thread_ts is not in payload when None
    assert "thread_ts" not in payload
    assert payload["channel"] == "C08PHH352S3"
    assert payload["text"] == "Test message"
