from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import uuid

import pytest

from services.resend.send_email import send_email


class TestSendEmail:
    @pytest.fixture
    def mock_resend_emails(self):
        with patch("services.resend.send_email.resend.Emails") as mock:
            yield mock

    @pytest.fixture
    def mock_datetime_now(self):
        fixed_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch("services.resend.send_email.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            yield mock_dt

    @pytest.fixture
    def mock_random_randint(self):
        with patch("services.resend.send_email.random.randint") as mock:
            mock.return_value = 45  # Fixed delay for testing
            yield mock

    @pytest.fixture
    def mock_uuid4(self):
        with patch("services.resend.send_email.uuid.uuid4") as mock:
            mock.return_value = uuid.UUID("12345678-1234-5678-9012-123456789012")
            yield mock

    def test_send_email_success(
        self, mock_resend_emails, mock_datetime_now, mock_random_randint, mock_uuid4
    ):
        # Setup
        mock_result = {"id": "email_123", "status": "sent"}
        mock_resend_emails.send.return_value = mock_result

        # Call function
        result = send_email(
            to="test@example.com",
            subject="Test Subject",
            text="Test message content"
        )

        # Verify result
        assert result == mock_result

        # Verify API call
        mock_resend_emails.send.assert_called_once()
        call_args = mock_resend_emails.send.call_args
        params = call_args[0][0]
        options = call_args[0][1]

        # Verify params
        assert params["from"] == "Wes from GitAuto <wes@gitauto.ai>"
        assert params["to"] == "test@example.com"
        assert params["subject"] == "Test Subject"
        assert params["text"] == "Test message content"
        assert params["scheduled_at"] == "2023-01-01T12:45:00+00:00Z"

        # Verify options
        assert options["idempotency_key"] == "12345678-1234-5678-9012-123456789012"

    def test_send_email_with_different_delay(
        self, mock_resend_emails, mock_datetime_now, mock_random_randint, mock_uuid4
    ):
        # Setup different delay
        mock_random_randint.return_value = 30
        mock_result = {"id": "email_456"}
        mock_resend_emails.send.return_value = mock_result

        # Call function
        result = send_email(
            to="another@example.com",
            subject="Another Subject",
            text="Another message"
        )

        # Verify scheduled time with 30 minute delay
        call_args = mock_resend_emails.send.call_args
        params = call_args[0][0]
        assert params["scheduled_at"] == "2023-01-01T12:30:00+00:00Z"
        assert result == mock_result

    def test_send_email_random_delay_range(self, mock_random_randint):
        with patch("services.resend.send_email.resend.Emails.send"):
            send_email("test@example.com", "Subject", "Text")
            mock_random_randint.assert_called_once_with(30, 60)

    def test_send_email_unique_idempotency_key(self, mock_resend_emails):
        # Call function multiple times
        with patch("services.resend.send_email.uuid.uuid4") as mock_uuid:
            mock_uuid.side_effect = [
                uuid.UUID("11111111-1111-1111-1111-111111111111"),
                uuid.UUID("22222222-2222-2222-2222-222222222222"),
            ]

            send_email("test1@example.com", "Subject1", "Text1")
            send_email("test2@example.com", "Subject2", "Text2")

            # Verify different idempotency keys were used
            calls = mock_resend_emails.send.call_args_list
            key1 = calls[0][0][1]["idempotency_key"]
            key2 = calls[1][0][1]["idempotency_key"]
            assert key1 != key2
            assert key1 == "11111111-1111-1111-1111-111111111111"
            assert key2 == "22222222-2222-2222-2222-222222222222"

    def test_send_email_exception_handling(self, mock_resend_emails):
        # Setup exception
        mock_resend_emails.send.side_effect = Exception("API Error")

        # Call function - should return None due to handle_exceptions decorator
        result = send_email("test@example.com", "Subject", "Text")
        assert result is None
