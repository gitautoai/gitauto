import pytest

from services.resend.text.uninstall_email import get_uninstall_email_text


def test_get_uninstall_email_text_with_regular_name():
    """Test email generation with a regular user name."""
    subject, text = get_uninstall_email_text("John")
    
    assert subject == "Sorry to see you go"
    assert "Hi John," in text
    assert "I noticed you uninstalled GitAuto. What went wrong?" in text
    assert "Your feedback would really help us improve - just reply to this email." in text
    assert "Thanks for trying GitAuto." in text
    assert "Wes" in text and "GitAuto" in text


def test_get_uninstall_email_text_with_empty_name():
    """Test email generation with empty user name."""
    subject, text = get_uninstall_email_text("")
    
    assert subject == "Sorry to see you go"
    assert "Hi ," in text
    assert "I noticed you uninstalled GitAuto. What went wrong?" in text
    assert "Your feedback would really help us improve - just reply to this email." in text
    assert "Thanks for trying GitAuto." in text
    assert "Wes" in text and "GitAuto" in text


def test_get_uninstall_email_text_with_special_characters():
    """Test email generation with special characters in name."""
    subject, text = get_uninstall_email_text("José María")
    
    assert subject == "Sorry to see you go"
    assert "Hi José María," in text
    assert "I noticed you uninstalled GitAuto. What went wrong?" in text
    assert "Your feedback would really help us improve - just reply to this email." in text
    assert "Thanks for trying GitAuto." in text
    assert "Wes" in text and "GitAuto" in text


@pytest.mark.parametrize(
    "user_name",
    [
        "Alice",
        "Bob Smith", 
        "李小明",
        "O'Connor",
        "123user",
        "@username",
    ],
)
def test_get_uninstall_email_text_parametrized(user_name):
    """Test email generation with various user names."""
    subject, text = get_uninstall_email_text(user_name)
    
    assert subject == "Sorry to see you go"
    assert f"Hi {user_name}," in text
    assert "I noticed you uninstalled GitAuto. What went wrong?" in text
    assert "Your feedback would really help us improve - just reply to this email." in text
    assert "Thanks for trying GitAuto." in text
    assert "Wes" in text and "GitAuto" in text


def test_get_uninstall_email_text_return_type():
    """Test that function returns a tuple of two strings."""
    result = get_uninstall_email_text("TestUser")
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)  # subject
    assert isinstance(result[1], str)  # text


def test_get_uninstall_email_text_type_annotation():
    """Test that function accepts string parameter and returns correct types."""
    # Test with string parameter
    result = get_uninstall_email_text("TestUser")
    assert isinstance(result[0], str)
    assert isinstance(result[1], str)
    
    # Test return type matches annotation
    subject, text = get_uninstall_email_text("TestUser")
    assert isinstance(subject, str)
    assert isinstance(text, str)
