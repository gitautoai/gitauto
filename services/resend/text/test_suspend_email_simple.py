import pytest
from services.resend.text.suspend_email import get_suspend_email_text


def test_basic_functionality():
    """Test basic functionality of get_suspend_email_text."""
    subject, text = get_suspend_email_text("John")
    assert subject == "Taking a break from GitAuto?"
    assert "Hi John," in text
    assert "Wes" in text
