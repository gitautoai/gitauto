import pytest

from services.resend.text.suspend_email import get_suspend_email_text


class TestGetSuspendEmailText:
    def test_get_suspend_email_text_with_name(self):
        subject, text = get_suspend_email_text("John")
        
        assert subject == "Taking a break from GitAuto?"
        expected_text = """Hi John,

I noticed you suspended GitAuto. What happened?

Any feedback? Just hit reply and let me know.

Wes
"""
        assert text == expected_text

    def test_get_suspend_email_text_with_different_name(self):
        subject, text = get_suspend_email_text("Alice")
        
        assert subject == "Taking a break from GitAuto?"
        expected_text = """Hi Alice,

I noticed you suspended GitAuto. What happened?

Any feedback? Just hit reply and let me know.

Wes
"""
        assert text == expected_text

    def test_get_suspend_email_text_with_empty_name(self):
        subject, text = get_suspend_email_text("")
        
        assert subject == "Taking a break from GitAuto?"
        assert "Hi ," in text

    def test_get_suspend_email_text_returns_tuple(self):
        result = get_suspend_email_text("Test")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)  # subject
        assert isinstance(result[1], str)  # text
