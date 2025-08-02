import pytest

from services.resend.text.suspend_email import get_suspend_email_text


def test_get_suspend_email_text_with_regular_name():
    """Test email generation with a regular user name."""
    subject, text = get_suspend_email_text("John")
    
    assert subject == "Taking a break from GitAuto?"
    assert "Hi John," in text
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert "Wes\nGitAuto" in text


def test_get_suspend_email_text_with_empty_name():
    """Test email generation with empty user name."""
    subject, text = get_suspend_email_text("")
    
    assert subject == "Taking a break from GitAuto?"
    assert "Hi ," in text
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert "Wes\nGitAuto" in text


def test_get_suspend_email_text_with_special_characters():
    """Test email generation with special characters in name."""
    subject, text = get_suspend_email_text("José María")
    
    assert subject == "Taking a break from GitAuto?"
    assert "Hi José María," in text
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert "Wes\nGitAuto" in text


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
def test_get_suspend_email_text_parametrized(user_name):
    """Test email generation with various user names."""
    subject, text = get_suspend_email_text(user_name)
    
    assert subject == "Taking a break from GitAuto?"
    assert f"Hi {user_name}," in text
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert "Wes\nGitAuto" in text


def test_get_suspend_email_text_return_type():
    """Test that function returns a tuple of two strings."""
    result = get_suspend_email_text("TestUser")
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)  # subject
    assert isinstance(result[1], str)  # text


def test_get_suspend_email_text_type_annotation():
    """Test that function accepts string parameter and returns correct types."""
    # Test with string parameter
    result = get_suspend_email_text("TestUser")
    assert isinstance(result[0], str)
    assert isinstance(result[1], str)
    
    # Test return type matches annotation
    subject, text = get_suspend_email_text("TestUser")
    assert isinstance(subject, str)
    assert isinstance(text, str)
