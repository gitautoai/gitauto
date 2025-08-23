from unittest.mock import patch

import pytest

from services.resend.text.suspend_email import get_suspend_email_text


def test_get_suspend_email_text_basic():
    """Test basic functionality with a simple user name."""
    subject, text = get_suspend_email_text("John")

    assert subject == "Taking a break from GitAuto?"
    assert "Hi John," in text
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert "Wes\nGitAuto" in text


def test_get_suspend_email_text_with_full_name():
    """Test with a full name containing spaces."""
    subject, text = get_suspend_email_text("John Doe")

    assert subject == "Taking a break from GitAuto?"
    assert "Hi John Doe," in text
    assert "I noticed you suspended GitAuto. What happened?" in text


def test_get_suspend_email_text_with_special_characters():
    """Test with user name containing special characters."""
    subject, text = get_suspend_email_text("José María")

    assert subject == "Taking a break from GitAuto?"
    assert "Hi José María," in text
    assert "I noticed you suspended GitAuto. What happened?" in text


def test_get_suspend_email_text_with_empty_string():
    """Test with empty string as user name."""
    subject, text = get_suspend_email_text("")

    assert subject == "Taking a break from GitAuto?"
    assert "Hi ," in text
    assert "I noticed you suspended GitAuto. What happened?" in text


def test_get_suspend_email_text_with_none():
    """Test with None as user name."""
    subject, text = get_suspend_email_text(None)

    assert subject == "Taking a break from GitAuto?"
    assert "Hi None," in text
    assert "I noticed you suspended GitAuto. What happened?" in text


def test_get_suspend_email_text_includes_email_signature():
    """Test that the email includes the email signature."""
    with patch(
        "services.resend.text.suspend_email.EMAIL_SIGNATURE",
        "Custom Signature",
    ):
        subject, text = get_suspend_email_text("Bob")

        assert "Custom Signature" in text
        assert text.endswith("Custom Signature")


def test_get_suspend_email_text_return_type():
    """Test that the function returns a tuple of two strings."""
    result = get_suspend_email_text("Test User")

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)  # subject
    assert isinstance(result[1], str)  # text


def test_get_suspend_email_text_subject_is_constant():
    """Test that the subject is always the same regardless of user name."""
    subject1, _ = get_suspend_email_text("Alice")
    subject2, _ = get_suspend_email_text("Bob")
    subject3, _ = get_suspend_email_text("")

    assert subject1 == subject2 == subject3 == "Taking a break from GitAuto?"


def test_get_suspend_email_text_email_structure():
    """Test that the email has the expected structure and content."""
    subject, text = get_suspend_email_text("TestUser")

    # Check that all expected content is present
    expected_content = [
        "Hi TestUser,",
        "I noticed you suspended GitAuto. What happened?",
        "Any feedback? Just hit reply and let me know.",
        "Wes\nGitAuto"
    ]
    
    for content in expected_content:
        assert content in text


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
def test_get_suspend_email_text_parametrized(user_name, expected_greeting):
    """Test various user name scenarios with parametrized test cases."""
    subject, text = get_suspend_email_text(user_name)

    assert subject == "Taking a break from GitAuto?"
    assert expected_greeting in text
