from unittest.mock import patch

import pytest

from utils.email.check_email_is_valid import check_email_is_valid


def test_check_email_is_valid_with_none():
    """Test that None email returns False."""
    assert check_email_is_valid(None) is False


def test_check_email_is_valid_with_valid_email():
    """Test that valid email returns True."""
    assert check_email_is_valid("user@example.com") is True


def test_check_email_is_valid_with_missing_at_symbol():
    """Test that email without @ symbol returns False."""
    assert check_email_is_valid("userexample.com") is False


def test_check_email_is_valid_with_missing_dot():
    """Test that email without dot returns False."""
    assert check_email_is_valid("user@examplecom") is False


def test_check_email_is_valid_with_missing_both_at_and_dot():
    """Test that email without @ and dot returns False."""
    assert check_email_is_valid("userexamplecom") is False


def test_check_email_is_valid_with_github_noreply_email():
    """Test that GitHub noreply email returns False."""
    assert check_email_is_valid("user@users.noreply.github.com") is False


def test_check_email_is_valid_with_github_noreply_email_uppercase():
    """Test that GitHub noreply email with uppercase returns False."""
    assert check_email_is_valid("USER@USERS.NOREPLY.GITHUB.COM") is False


def test_check_email_is_valid_with_github_noreply_email_mixed_case():
    """Test that GitHub noreply email with mixed case returns False."""
    assert check_email_is_valid("User@Users.NoReply.GitHub.Com") is False


def test_check_email_is_valid_with_empty_string():
    """Test that empty string returns False."""
    assert check_email_is_valid("") is False


def test_check_email_is_valid_with_whitespace_only():
    """Test that whitespace-only string returns False."""
    assert check_email_is_valid("   ") is False


def test_check_email_is_valid_with_at_symbol_only():
    """Test that string with only @ symbol returns False."""
    assert check_email_is_valid("@") is False


def test_check_email_is_valid_with_dot_only():
    """Test that string with only dot returns False."""
    assert check_email_is_valid(".") is False


def test_check_email_is_valid_with_at_and_dot_only():
    """Test that string with only @ and dot returns True."""
    assert check_email_is_valid("@.") is True


@pytest.mark.parametrize("email,expected", [
    ("user@example.com", True),
    ("test.email@domain.org", True),
    ("user+tag@example.co.uk", True),
    ("user123@test-domain.com", True),
    ("user@sub.domain.example.com", True),
    ("user@users.noreply.github.com", False),
    ("123456+username@users.noreply.github.com", False),
    ("user@example", False),
    ("@example.com", True),
    ("user@", False),
    ("user.example.com", False),
    ("", False),
    (None, False),
])
def test_check_email_is_valid_parametrized(email, expected):
    """Test various email formats with parametrized inputs."""
    assert check_email_is_valid(email) is expected


def test_check_email_is_valid_with_mocked_github_domain():
    """Test that function correctly uses the GitHub domain constant."""
    with patch("utils.email.check_email_is_valid.GITHUB_NOREPLY_EMAIL_DOMAIN", "test.domain.com"):
        assert check_email_is_valid("user@test.domain.com") is False
        assert check_email_is_valid("user@other.domain.com") is True


def test_check_email_is_valid_case_insensitive_github_domain():
    """Test that GitHub domain check is case insensitive."""
    test_emails = [
        "user@users.noreply.github.com",
        "user@USERS.NOREPLY.GITHUB.COM", 
        "user@Users.NoReply.GitHub.Com",
        "user@users.NOREPLY.github.COM",
    ]
    for email in test_emails:
        assert check_email_is_valid(email) is False


def test_check_email_is_valid_with_numeric_email():
    """Test that numeric email addresses work correctly."""
    assert check_email_is_valid("123@456.789") is True


def test_check_email_is_valid_with_special_characters():
    """Test that emails with special characters work correctly."""
    assert check_email_is_valid("user+tag@example.com") is True
    assert check_email_is_valid("user-name@example.com") is True
    assert check_email_is_valid("user_name@example.com") is True
    assert check_email_is_valid("user.name@example.com") is True


def test_check_email_is_valid_with_multiple_dots():
    """Test that emails with multiple dots work correctly."""
    assert check_email_is_valid("user@sub.domain.example.com") is True
    assert check_email_is_valid("user.name@sub.domain.example.com") is True


def test_check_email_is_valid_edge_cases():
    """Test edge cases for email validation."""
    # Minimum valid email format
    assert check_email_is_valid("a@b.c") is True
    
    # Multiple @ symbols (still considered valid by this simple validator)
    assert check_email_is_valid("user@@example.com") is True
    
    # Multiple dots in domain
    assert check_email_is_valid("user@example..com") is True
    
    # Email starting/ending with special characters
    assert check_email_is_valid(".user@example.com") is True
    assert check_email_is_valid("user.@example.com") is True
