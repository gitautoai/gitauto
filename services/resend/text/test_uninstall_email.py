from services.resend.text.uninstall_email import get_uninstall_email_text


def test_get_uninstall_email_text_returns_tuple():
    """Test that get_uninstall_email_text returns a tuple"""
    result = get_uninstall_email_text("John")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_get_uninstall_email_text_returns_subject_and_text():
    """Test that the function returns subject and text in correct order"""
    subject, text = get_uninstall_email_text("John")
    assert isinstance(subject, str)
    assert isinstance(text, str)
    assert len(subject) > 0
    assert len(text) > 0


def test_get_uninstall_email_text_subject_content():
    """Test that the subject has the expected content"""
    subject, _ = get_uninstall_email_text("John")
    assert subject == "Sorry to see you go"


def test_get_uninstall_email_text_includes_user_name():
    """Test that the email text includes the provided user name"""
    user_name = "John"
    _, text = get_uninstall_email_text(user_name)
    assert f"Hi {user_name}," in text


def test_get_uninstall_email_text_with_different_names():
    """Test the function with various user names"""
    test_names = ["Alice", "Bob", "Charlie", "Diana"]
    
    for name in test_names:
        subject, text = get_uninstall_email_text(name)
        assert subject == "Sorry to see you go"
        assert f"Hi {name}," in text


def test_get_uninstall_email_text_with_empty_string():
    """Test the function with empty string user name"""
    subject, text = get_uninstall_email_text("")
    assert subject == "Sorry to see you go"
    assert "Hi ," in text


def test_get_uninstall_email_text_with_whitespace_name():
    """Test the function with whitespace in user name"""
    user_name = "  John Doe  "
    subject, text = get_uninstall_email_text(user_name)
    assert subject == "Sorry to see you go"
    assert f"Hi {user_name}," in text


def test_get_uninstall_email_text_with_special_characters():
    """Test the function with special characters in user name"""
    user_name = "John-O'Connor"
    subject, text = get_uninstall_email_text(user_name)
    assert subject == "Sorry to see you go"
    assert f"Hi {user_name}," in text


def test_get_uninstall_email_text_with_unicode_characters():
    """Test the function with unicode characters in user name"""
    user_name = "José"
    subject, text = get_uninstall_email_text(user_name)
    assert subject == "Sorry to see you go"
    assert f"Hi {user_name}," in text


def test_get_uninstall_email_text_contains_expected_content():
    """Test that the email text contains all expected content"""
    _, text = get_uninstall_email_text("John")
    
    expected_phrases = [
        "I noticed you uninstalled GitAuto",
        "What went wrong?",
        "Your feedback would really help us improve",
        "just reply to this email",
        "Thanks for trying GitAuto",
        "Wes"
    ]
    
    for phrase in expected_phrases:
        assert phrase in text


def test_get_uninstall_email_text_structure():
    """Test that the email text has the expected structure"""
    user_name = "John"
    _, text = get_uninstall_email_text(user_name)
    
    # Check that text starts with greeting
    assert text.startswith(f"Hi {user_name},")
    
    # Check that text ends with signature
    assert text.strip().endswith("Wes\nGitAuto")
    
    # Check for proper line breaks
    lines = text.split('\n')
    assert len(lines) > 5  # Should have multiple lines


def test_get_uninstall_email_text_consistency():
    """Test that multiple calls with same input return identical results"""
    user_name = "John"
    result1 = get_uninstall_email_text(user_name)
    result2 = get_uninstall_email_text(user_name)
    
    assert result1 == result2
    assert result1[0] == result2[0]  # Same subject
    assert result1[1] == result2[1]  # Same text


def test_get_uninstall_email_text_immutability():
    """Test that the function doesn't modify input parameters"""
    original_name = "John"
    user_name = original_name
    get_uninstall_email_text(user_name)
    assert user_name == original_name
