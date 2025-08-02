import pytest

from services.resend.text.no_credits_email import get_no_credits_email_text


def test_get_no_credits_email_text_with_regular_name():
    """Test email generation with a regular user name."""
    subject, text = get_no_credits_email_text("John")
    
    assert subject == "Add credits to continue"
    assert "Hi John," in text
    assert "Looks like you're trying to use GitAuto but you're out of credits." in text
    assert "Add some credits to keep going: https://gitauto.ai/dashboard/credits" in text
    assert "Wes" in text and "GitAuto" in text


def test_get_no_credits_email_text_with_empty_name():
    """Test email generation with empty user name."""
    subject, text = get_no_credits_email_text("")
    
    assert subject == "Add credits to continue"
    assert "Hi ," in text
    assert "Looks like you're trying to use GitAuto but you're out of credits." in text
    assert "Add some credits to keep going: https://gitauto.ai/dashboard/credits" in text
    assert "Wes" in text and "GitAuto" in text


def test_get_no_credits_email_text_with_special_characters():
    """Test email generation with special characters in name."""
    subject, text = get_no_credits_email_text("José María")
    
    assert subject == "Add credits to continue"
    assert "Hi José María," in text
    assert "Looks like you're trying to use GitAuto but you're out of credits." in text
    assert "Add some credits to keep going: https://gitauto.ai/dashboard/credits" in text
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
def test_get_no_credits_email_text_parametrized(user_name):
    """Test email generation with various user names."""
    subject, text = get_no_credits_email_text(user_name)
    
    assert subject == "Add credits to continue"
    assert f"Hi {user_name}," in text
    assert "Looks like you're trying to use GitAuto but you're out of credits." in text
    assert "Add some credits to keep going: https://gitauto.ai/dashboard/credits" in text
    assert "Wes" in text and "GitAuto" in text


def test_get_no_credits_email_text_return_type():
    """Test that function returns a tuple of two strings."""
    result = get_no_credits_email_text("TestUser")
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)  # subject
    assert isinstance(result[1], str)  # text
