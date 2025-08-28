from unittest.mock import patch

import pytest

from utils.text.get_insufficient_credits_message import get_insufficient_credits_message


@pytest.fixture
def mock_constants():
    with patch(
        "utils.text.get_insufficient_credits_message.EMAIL_LINK", "test@example.com"
    ), patch(
        "utils.text.get_insufficient_credits_message.DASHBOARD_CREDITS_URL",
        "https://dashboard/credits",
    ), patch(
        "utils.text.get_insufficient_credits_message.CONTACT_URL", "https://contact"
    ):
        yield


def test_get_insufficient_credits_message_format(_mock_constants):
    """Test that the message follows the expected format with all required components."""
    username = "testuser"
    message = get_insufficient_credits_message(username)

    # Check that the message contains all required components
    assert f"@{username}" in message
    assert "insufficient credits" in message.lower()
    assert "<a href='" in message
    assert "Add credits" in message
    assert "visit our contact page" in message
    assert "email us at" in message


def test_get_insufficient_credits_message_user_mention(_mock_constants):
    """Test that the message correctly mentions different usernames."""
    message = get_insufficient_credits_message("different_user")
    assert "@different_user" in message
