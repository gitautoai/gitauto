# Standard imports
from unittest.mock import patch

# Third party imports
import pytest

# Local imports
from services.resend.text.no_credits_email import get_no_credits_email_text


def test_get_no_credits_email_text_basic():
    """Test basic functionality with a simple user name."""
    subject, text = get_no_credits_email_text("John")

    assert subject == "Add credits to continue"
    assert "Hi John," in text
    assert "Looks like you're trying to use GitAuto but you're out of credits." in text
    assert "Add some credits to keep going:" in text
    assert "Wes\nGitAuto" in text


def test_get_no_credits_email_text_with_full_name():
    """Test with a full name containing spaces."""
    subject, text = get_no_credits_email_text("John Doe")

    assert subject == "Add credits to continue"
    assert "Hi John Doe," in text
    assert "Looks like you're trying to use GitAuto but you're out of credits." in text


def test_get_no_credits_email_text_with_special_characters():
    """Test with user name containing special characters."""
    subject, text = get_no_credits_email_text("José María")

    assert subject == "Add credits to continue"
    assert "Hi José María," in text
    assert "Looks like you're trying to use GitAuto but you're out of credits." in text


def test_get_no_credits_email_text_with_empty_string():
    """Test with empty string as user name."""
    subject, text = get_no_credits_email_text("")

    assert subject == "Add credits to continue"
    assert "Hi ," in text
    assert "Looks like you're trying to use GitAuto but you're out of credits." in text


def test_get_no_credits_email_text_with_none():
    """Test with None as user name."""
    subject, text = get_no_credits_email_text(None)

    assert subject == "Add credits to continue"
    assert "Hi None," in text
    assert "Looks like you're trying to use GitAuto but you're out of credits." in text


def test_get_no_credits_email_text_return_type():
    """Test that function returns a tuple with two strings."""
    result = get_no_credits_email_text("TestUser")

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)  # subject
    assert isinstance(result[1], str)  # text


def test_get_no_credits_email_text_includes_dashboard_url():
    """Test that the email text includes the dashboard credits URL."""
    with patch(
        "services.resend.text.no_credits_email.DASHBOARD_CREDITS_URL",
        "https://test.gitauto.ai/dashboard/credits",
    ):
        _, text = get_no_credits_email_text("TestUser")

        assert "https://test.gitauto.ai/dashboard/credits" in text


def test_get_no_credits_email_text_includes_email_signature():
    """Test that the email text includes the email signature."""
    with patch(
        "services.resend.text.no_credits_email.EMAIL_SIGNATURE", "Test Signature"
    ):
        _, text = get_no_credits_email_text("TestUser")

        assert "Test Signature" in text


@pytest.mark.parametrize(
    "user_name,expected_greeting",
    [
        ("Alice", "Hi Alice,"),
        ("Bob Smith", "Hi Bob Smith,"),
        ("李小明", "Hi 李小明,"),
        ("O'Connor", "Hi O'Connor,"),
        ("user@example.com", "Hi user@example.com,"),
        ("123", "Hi 123,"),
        ("user-name_test", "Hi user-name_test,"),
        ("", "Hi ,"),
        (None, "Hi None,"),
    ],
)
def test_get_no_credits_email_text_parametrized(user_name, expected_greeting):
    """Test various user name scenarios with parametrized test cases."""
    subject, text = get_no_credits_email_text(user_name)

    assert subject == "Add credits to continue"
    assert expected_greeting in text
