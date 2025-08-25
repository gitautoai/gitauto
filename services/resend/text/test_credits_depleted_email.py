from unittest.mock import patch

import pytest

from services.resend.text.credits_depleted_email import get_credits_depleted_email_text


def test_get_credits_depleted_email_text_basic():
    """Test basic functionality with a simple user name."""
    subject, text = get_credits_depleted_email_text("John")

    assert subject == "You're out of credits!"
    assert "Hey John!" in text
    assert "Just used your last GitAuto credits on that PR. Nice work!" in text
    assert "Grab more credits here:" in text
    assert "Wes\nGitAuto" in text


def test_get_credits_depleted_email_text_with_full_name():
    """Test with a full name containing spaces."""
    subject, text = get_credits_depleted_email_text("John Doe")

    assert subject == "You're out of credits!"
    assert "Hey John Doe!" in text
    assert "Just used your last GitAuto credits on that PR. Nice work!" in text


def test_get_credits_depleted_email_text_with_special_characters():
    """Test with user name containing special characters."""
    subject, text = get_credits_depleted_email_text("José María")

    assert subject == "You're out of credits!"
    assert "Hey José María!" in text
    assert "Just used your last GitAuto credits on that PR. Nice work!" in text


def test_get_credits_depleted_email_text_with_empty_string():
    """Test with empty string as user name."""
    subject, text = get_credits_depleted_email_text("")

    assert subject == "You're out of credits!"
    assert "Hey !" in text
    assert "Just used your last GitAuto credits on that PR. Nice work!" in text


def test_get_credits_depleted_email_text_with_none():
    """Test with None as user name."""
    subject, text = get_credits_depleted_email_text(None)

    assert subject == "You're out of credits!"
    assert "Hey None!" in text
    assert "Just used your last GitAuto credits on that PR. Nice work!" in text


def test_get_credits_depleted_email_text_includes_dashboard_url():
    """Test that the email includes the dashboard credits URL."""
    with patch(
        "services.resend.text.credits_depleted_email.DASHBOARD_CREDITS_URL",
        "https://test.com/credits",
    ):
        _, text = get_credits_depleted_email_text("Alice")

        assert "https://test.com/credits" in text
        assert "Grab more credits here: https://test.com/credits" in text


def test_get_credits_depleted_email_text_includes_email_signature():
    """Test that the email includes the email signature."""
    with patch(
        "services.resend.text.credits_depleted_email.EMAIL_SIGNATURE",
        "Custom Signature",
    ):
        _, text = get_credits_depleted_email_text("Bob")

        assert "Custom Signature" in text
        assert text.endswith("Custom Signature")


def test_get_credits_depleted_email_text_return_type():
    """Test that the function returns a tuple of two strings."""
    result = get_credits_depleted_email_text("Test User")

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)  # subject
    assert isinstance(result[1], str)  # text


@pytest.mark.parametrize(
    "user_name,expected_greeting",
    [
        ("Alice", "Hey Alice!"),
        ("Bob Smith", "Hey Bob Smith!"),
        ("李小明", "Hey 李小明!"),
        ("O'Connor", "Hey O'Connor!"),
        ("user@example.com", "Hey user@example.com!"),
        ("123", "Hey 123!"),
        ("user-name_test", "Hey user-name_test!"),
    ],
)
def test_get_credits_depleted_email_text_parametrized(user_name, expected_greeting):
    """Test various user name scenarios with parametrized test cases."""
    subject, text = get_credits_depleted_email_text(user_name)

    assert subject == "You're out of credits!"
    assert expected_greeting in text
