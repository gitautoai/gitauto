# Standard imports
from datetime import datetime, timezone
import uuid
from unittest.mock import patch

# Third party imports
import pytest

# Local imports
from services.resend.send_email import send_email


@pytest.fixture
def mock_resend_emails():
    """Fixture to mock resend.Emails.send method."""
    with patch("services.resend.send_email.resend.Emails.send") as mock:
        yield mock


@pytest.fixture
def mock_datetime_now():
    """Fixture to mock datetime.now for consistent testing."""
    fixed_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    with patch("services.resend.send_email.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = datetime
        yield mock_dt


@pytest.fixture
def mock_random_randint():
    """Fixture to mock random.randint for consistent testing."""
    with patch("services.resend.send_email.random.randint") as mock:
        mock.return_value = 45  # Fixed delay of 45 minutes
        yield mock


@pytest.fixture
def mock_uuid():
    """Fixture to mock uuid.uuid4 for consistent testing."""
    with patch("services.resend.send_email.uuid.uuid4") as mock:
        mock.return_value = uuid.UUID("12345678-1234-5678-9abc-123456789012")
        yield mock


def test_send_email_success(
    mock_resend_emails, mock_datetime_now, mock_random_randint, mock_uuid
):
    """Test successful email sending with all parameters."""
    # Setup
    mock_result = {"id": "email_123", "status": "sent"}
    mock_resend_emails.return_value = mock_result

    # Execute
    result = send_email(
        to="test@example.com", subject="Test Subject", text="Test email content"
    )

    # Assert
    assert result == mock_result
    mock_resend_emails.assert_called_once()

    # Verify call arguments
    call_args = mock_resend_emails.call_args
    params = call_args[0][0]
    options = call_args[0][1]

    assert params["to"] == "test@example.com"
    assert params["subject"] == "Test Subject"
    assert params["text"] == "Test email content"
    assert params["from"] == "Wes from GitAuto <wes@gitauto.ai>"
    assert params["bcc"] == "Wes from GitAuto <wes@gitauto.ai>"
    assert "scheduled_at" in params

    assert options["idempotency_key"] == "12345678-1234-5678-9abc-123456789012"


def test_send_email_scheduled_time_calculation(
    mock_resend_emails, mock_datetime_now, mock_random_randint, mock_uuid
):
    """Test that scheduled time is calculated correctly."""
    # Setup
    mock_resend_emails.return_value = {"id": "email_123"}

    # Execute
    send_email("test@example.com", "Subject", "Text")

    # Assert
    mock_random_randint.assert_called_once_with(30, 60)

    # Verify scheduled time calculation
    call_args = mock_resend_emails.call_args[0][0]
    scheduled_at = call_args["scheduled_at"]

    # Expected time: 2024-01-15 10:30:00 + 45 minutes = 2024-01-15 11:15:00
    expected_time = datetime(2024, 1, 15, 11, 15, 0, tzinfo=timezone.utc)
    assert scheduled_at == expected_time.isoformat()


def test_send_email_with_empty_parameters(
    mock_resend_emails, mock_datetime_now, mock_random_randint, mock_uuid
):
    """Test email sending with empty parameters."""
    # Setup
    mock_resend_emails.return_value = {"id": "email_empty"}

    # Execute
    result = send_email(to="", subject="", text="")

    # Assert
    assert result == {"id": "email_empty"}

    call_args = mock_resend_emails.call_args[0][0]
    assert call_args["to"] == ""
    assert call_args["subject"] == ""
    assert call_args["text"] == ""


def test_send_email_with_special_characters(
    mock_resend_emails, mock_datetime_now, mock_random_randint, mock_uuid
):
    """Test email sending with special characters in parameters."""
    # Setup
    mock_resend_emails.return_value = {"id": "email_special"}

    # Execute
    result = send_email(
        to="test+tag@example.com",
        subject="Subject with émojis 🚀 and special chars: <>&\"'",
        text="Text with\nnewlines\tand\ttabs",
    )

    # Assert
    assert result == {"id": "email_special"}

    call_args = mock_resend_emails.call_args[0][0]
    assert call_args["to"] == "test+tag@example.com"
    assert call_args["subject"] == "Subject with émojis 🚀 and special chars: <>&\"'"
    assert call_args["text"] == "Text with\nnewlines\tand\ttabs"


def test_send_email_resend_api_error(
    mock_resend_emails, mock_datetime_now, mock_random_randint, mock_uuid
):
    """Test error handling when Resend API raises an exception."""
    # Setup
    mock_resend_emails.side_effect = Exception("Resend API error")

    # Execute
    result = send_email("test@example.com", "Subject", "Text")

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_resend_emails.assert_called_once()


def test_send_email_unique_idempotency_keys(
    mock_resend_emails, mock_datetime_now, mock_random_randint
):
    """Test that each email gets a unique idempotency key."""
    # Setup
    mock_resend_emails.return_value = {"id": "email_123"}

    # Execute multiple calls
    send_email("test1@example.com", "Subject 1", "Text 1")
    send_email("test2@example.com", "Subject 2", "Text 2")

    # Assert
    assert mock_resend_emails.call_count == 2

    # Get idempotency keys from both calls
    call1_options = mock_resend_emails.call_args_list[0][0][1]
    call2_options = mock_resend_emails.call_args_list[1][0][1]

    # Verify they are different
    assert call1_options["idempotency_key"] != call2_options["idempotency_key"]


def test_send_email_random_delay_range(
    mock_resend_emails, mock_datetime_now, mock_uuid
):
    """Test that random delay is within expected range."""
    # Setup
    mock_resend_emails.return_value = {"id": "email_123"}

    # Execute
    send_email("test@example.com", "Subject", "Text")

    # Assert
    with patch("services.resend.send_email.random.randint") as mock_randint:
        mock_randint.return_value = 30
        send_email("test@example.com", "Subject", "Text")
        mock_randint.assert_called_with(30, 60)


def test_send_email_params_structure(
    mock_resend_emails, mock_datetime_now, mock_random_randint, mock_uuid
):
    """Test that email parameters are structured correctly."""
    # Setup
    mock_resend_emails.return_value = {"id": "email_123"}

    # Execute
    send_email("test@example.com", "Test Subject", "Test Content")

    # Assert
    call_args = mock_resend_emails.call_args
    params = call_args[0][0]
    options = call_args[0][1]

    # Verify params structure
    assert isinstance(params, dict)
    assert set(params.keys()) == {
        "from",
        "to",
        "bcc",
        "subject",
        "text",
        "scheduled_at",
    }

    # Verify options structure
    assert isinstance(options, dict)
    assert "idempotency_key" in options
    assert isinstance(options["idempotency_key"], str)


def test_send_email_timezone_handling(
    mock_resend_emails, mock_random_randint, mock_uuid
):
    """Test that timezone is handled correctly in scheduled_at."""
    # Setup
    mock_resend_emails.return_value = {"id": "email_123"}

    # Execute with a specific timezone-aware datetime
    with patch("services.resend.send_email.datetime") as mock_dt:
        fixed_time = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        send_email("test@example.com", "Subject", "Text")

    # Assert
    call_args = mock_resend_emails.call_args[0][0]
    scheduled_at = call_args["scheduled_at"]

    # Verify ISO format with timezone
    assert scheduled_at.endswith("+00:00") or scheduled_at.endswith("Z")

    # Verify it's a valid ISO datetime
    parsed_time = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
    assert parsed_time.tzinfo is not None
