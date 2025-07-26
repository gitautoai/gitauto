import pytest

from services.resend.text.uninstall_email import get_uninstall_email_text


class TestGetUninstallEmailText:
    def test_get_uninstall_email_text_with_name(self):
        subject, text = get_uninstall_email_text("John")
        
        assert subject == "Sorry to see you go"
        expected_text = """Hi John,

I noticed you uninstalled GitAuto. What went wrong?

Your feedback would really help us improve - just reply to this email.

Thanks for trying GitAuto.

Wes
"""
        assert text == expected_text

    def test_get_uninstall_email_text_with_different_name(self):
        subject, text = get_uninstall_email_text("Alice")
        
        assert subject == "Sorry to see you go"
        expected_text = """Hi Alice,

I noticed you uninstalled GitAuto. What went wrong?

Your feedback would really help us improve - just reply to this email.

Thanks for trying GitAuto.

Wes
"""
        assert text == expected_text

    def test_get_uninstall_email_text_with_empty_name(self):
        subject, text = get_uninstall_email_text("")
        
        assert subject == "Sorry to see you go"
        assert "Hi ," in text

    def test_get_uninstall_email_text_returns_tuple(self):
        result = get_uninstall_email_text("Test")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)  # subject
        assert isinstance(result[1], str)  # text
