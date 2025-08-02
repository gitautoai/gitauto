import pytest

from services.resend.text.credits_depleted_email import get_credits_depleted_email_text


def test_get_credits_depleted_email_text_with_regular_name():
    """Test email generation with a regular user name."""
    subject, text = get_credits_depleted_email_text("John")
    
    assert subject == "You're out of credits!"
    assert "Hey John!" in text
    assert "Just used your last GitAuto credits on that PR. Nice work!" in text
    assert "Grab more credits here: https://gitauto.ai/dashboard/credits" in text
    assert "Wes" in text and "GitAuto" in text


def test_get_credits_depleted_email_text_with_empty_name():
    """Test email generation with empty user name."""
    subject, text = get_credits_depleted_email_text("")
    
    assert subject == "You're out of credits!"
    assert "Hey !" in text
    assert "Just used your last GitAuto credits on that PR. Nice work!" in text
    assert "Grab more credits here: https://gitauto.ai/dashboard/credits" in text
    assert "Wes" in text and "GitAuto" in text


def test_get_credits_depleted_email_text_with_special_characters():
    """Test email generation with special characters in name."""
    subject, text = get_credits_depleted_email_text("José María")
    
    assert subject == "You're out of credits!"
    assert "Hey José María!" in text
    assert "Just used your last GitAuto credits on that PR. Nice work!" in text
    assert "Grab more credits here: https://gitauto.ai/dashboard/credits" in text
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
def test_get_credits_depleted_email_text_parametrized(user_name):
    """Test email generation with various user names."""
    subject, text = get_credits_depleted_email_text(user_name)
    
    assert subject == "You're out of credits!"
    assert f"Hey {user_name}!" in text
    assert "Just used your last GitAuto credits on that PR. Nice work!" in text
    assert "Grab more credits here: https://gitauto.ai/dashboard/credits" in text
    assert "Wes" in text and "GitAuto" in text


def test_get_credits_depleted_email_text_return_type():
    """Test that function returns a tuple of two strings."""
    result = get_credits_depleted_email_text("TestUser")
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)  # subject
    assert isinstance(result[1], str)  # text
