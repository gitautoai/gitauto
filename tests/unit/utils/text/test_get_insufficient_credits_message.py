import pytest
from unittest.mock import patch

from utils.text.get_insufficient_credits_message import get_insufficient_credits_message


@pytest.fixture
def mock_constants():
    with patch('utils.text.get_insufficient_credits_message.EMAIL_LINK', 'test@example.com'), \
         patch('utils.text.get_insufficient_credits_message.DASHBOARD_CREDITS_URL', 'https://dashboard/credits'), \
         patch('utils.text.get_insufficient_credits_message.CONTACT_URL', 'https://contact'):
        yield


def test_get_insufficient_credits_message_format(mock_constants):
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


def test_get_insufficient_credits_message_user_mention(mock_constants):
    """Test that the message correctly mentions different usernames."""
    message = get_insufficient_credits_message("different_user")
    assert "@different_user" in message

def test_get_insufficient_credits_message_urls(mock_constants):
    """Test that the message contains the exact URLs."""
    message = get_insufficient_credits_message("testuser")
    
    # Check exact URLs are included
    assert "https://dashboard/credits" in message
    assert "https://contact" in message


def test_get_insufficient_credits_message_email(mock_constants):
    """Test that the message contains the exact email link."""
    message = get_insufficient_credits_message("testuser")
    assert "test@example.com" in message


def test_get_insufficient_credits_message_special_chars():
    """Test that the message handles usernames with special characters."""
    special_usernames = [
        "user.name",
        "user-name",
        "user_name",
        "123user",
        "user123",
        "USER_CAPS"
    ]
    
    for username in special_usernames:
        message = get_insufficient_credits_message(username)
        # Verify the username is included exactly as provided
        assert f"@{username}" in message
        # Verify the message is still properly formatted
