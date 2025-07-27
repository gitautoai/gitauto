import pytest
from services.resend.text.suspend_email import get_suspend_email_text


def test_get_suspend_email_text_returns_tuple():
    """Test that get_suspend_email_text returns a tuple with subject and text."""
    result = get_suspend_email_text("John")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_get_suspend_email_text_with_simple_name():
    """Test get_suspend_email_text with a simple user name."""
    subject, text = get_suspend_email_text("John")
    
    assert subject == "Taking a break from GitAuto?"
    assert "Hi John," in text
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert "Wes" in text


def test_get_suspend_email_text_with_full_name():
    """Test get_suspend_email_text with a full name."""
    subject, text = get_suspend_email_text("John Doe")
    
    assert subject == "Taking a break from GitAuto?"
    assert "Hi John Doe," in text
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert "Wes" in text


def test_get_suspend_email_text_with_empty_string():
    """Test get_suspend_email_text with empty string."""
    subject, text = get_suspend_email_text("")
    
    assert subject == "Taking a break from GitAuto?"
    assert "Hi ," in text
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert "Wes" in text


def test_get_suspend_email_text_with_whitespace_name():
    """Test get_suspend_email_text with whitespace in name."""
    subject, text = get_suspend_email_text("  Jane Smith  ")
    
    assert subject == "Taking a break from GitAuto?"
    assert "Hi   Jane Smith  ," in text
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert "Wes" in text


def test_get_suspend_email_text_with_special_characters():
    """Test get_suspend_email_text with special characters in name."""
    subject, text = get_suspend_email_text("José María")
    
    assert subject == "Taking a break from GitAuto?"
    assert "Hi José María," in text
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert "Wes" in text


def test_get_suspend_email_text_subject_is_constant():
    """Test that the subject line is consistent regardless of user name."""
    names = ["Alice", "Bob", "Charlie", "", "  ", "José María"]
    subjects = [get_suspend_email_text(name)[0] for name in names]
    
    # All subjects should be identical
    assert all(subject == "Taking a break from GitAuto?" for subject in subjects)


def test_get_suspend_email_text_email_structure():
    """Test that the email text has the expected structure."""
    subject, text = get_suspend_email_text("TestUser")
    
    # Check that text starts with greeting
    assert text.startswith("Hi TestUser,")
    
    # Check that text ends with signature
    assert text.strip().endswith("Wes")
    
    # Check that text contains expected content in order
    lines = text.strip().split('\n')
    assert len(lines) >= 4  # At least greeting, blank line, content, signature
    assert lines[0] == "Hi TestUser,"
    assert lines[-1] == "Wes"


@pytest.mark.parametrize(
    "user_name,expected_greeting",
    [
        ("Alice", "Hi Alice,"),
        ("Bob Johnson", "Hi Bob Johnson,"),
        ("", "Hi ,"),
        ("123", "Hi 123,"),
        ("user@example.com", "Hi user@example.com,"),
        ("User-Name_123", "Hi User-Name_123,"),
    ],
)
def test_get_suspend_email_text_with_various_names(user_name, expected_greeting):
    """Test get_suspend_email_text with various user name formats."""
    subject, text = get_suspend_email_text(user_name)
    
    assert subject == "Taking a break from GitAuto?"
    assert text.startswith(expected_greeting)
    assert "I noticed you suspended GitAuto. What happened?" in text
    assert "Any feedback? Just hit reply and let me know." in text
    assert text.strip().endswith("Wes")


def test_get_suspend_email_text_return_types():
    """Test that both returned values are strings."""
    subject, text = get_suspend_email_text("TestUser")
    
    assert isinstance(subject, str)
    assert isinstance(text, str)
    assert len(subject) > 0
    assert len(text) > 0


def test_get_suspend_email_text_text_contains_newlines():
    """Test that the email text contains proper line breaks."""
    subject, text = get_suspend_email_text("TestUser")
    
    # Should contain newlines for proper email formatting
    assert '\n' in text
    
    # Should have multiple lines
    lines = text.split('\n')
    assert len(lines) > 1


def test_get_suspend_email_text_exact_content_match():
    """Test that the email content matches exactly what's expected."""
    subject, text = get_suspend_email_text("John")
    
    expected_text = """Hi John,

I noticed you suspended GitAuto. What happened?

Any feedback? Just hit reply and let me know.

Wes
"""
    
    assert subject == "Taking a break from GitAuto?"
    assert text == expected_text


def test_get_suspend_email_text_preserves_user_name_formatting():
    """Test that user name formatting is preserved exactly as provided."""
    test_cases = [
        "lowercase",
        "UPPERCASE", 
        "MixedCase",
        "with spaces",
        "with-dashes",
        "with_underscores",
        "with.dots",
        "123numbers",
        "special!@#chars",
    ]
    
    for user_name in test_cases:
        subject, text = get_suspend_email_text(user_name)
        assert f"Hi {user_name}," in text
        assert subject == "Taking a break from GitAuto?"


def test_get_suspend_email_text_multiline_structure():
    """Test that the email has the correct multiline structure."""
    subject, text = get_suspend_email_text("TestUser")
    
    lines = text.split('\n')
    
    # Verify exact structure
    assert lines[0] == "Hi TestUser,"
    assert lines[1] == ""  # Empty line
    assert lines[2] == "I noticed you suspended GitAuto. What happened?"
    assert lines[3] == ""  # Empty line
    assert lines[4] == "Any feedback? Just hit reply and let me know."
    assert lines[5] == ""  # Empty line
    assert lines[6] == "Wes"
    assert len(lines) == 7


def test_get_suspend_email_text_no_trailing_whitespace():
    """Test that the email text doesn't have unexpected trailing whitespace."""
    subject, text = get_suspend_email_text("TestUser")
    
    # Subject should not have trailing whitespace
    assert subject == subject.strip()
    
    # Each line should not have trailing whitespace (except intentional empty lines)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line:  # Non-empty lines should not have trailing whitespace
            assert line == line.rstrip()