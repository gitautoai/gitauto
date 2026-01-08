import pytest

from services.resend.get_first_name import get_first_name


def test_get_first_name_with_empty_string():
    """Test that empty string returns 'there'."""
    result = get_first_name("")
    assert result == "there"


def test_get_first_name_with_single_name():
    """Test that single name returns the name itself."""
    result = get_first_name("John")
    assert result == "John"


def test_get_first_name_with_full_name():
    """Test that full name returns only the first name."""
    result = get_first_name("John Doe")
    assert result == "John"


def test_get_first_name_with_multiple_names():
    """Test that multiple names returns only the first name."""
    result = get_first_name("John Michael Doe")
    assert result == "John"


def test_get_first_name_with_leading_whitespace():
    """Test that leading whitespace is stripped before processing."""
    result = get_first_name("  John Doe")
    assert result == "John"


def test_get_first_name_with_trailing_whitespace():
    """Test that trailing whitespace is stripped before processing."""
    result = get_first_name("John Doe  ")
    assert result == "John"


def test_get_first_name_with_surrounding_whitespace():
    """Test that surrounding whitespace is stripped before processing."""
    result = get_first_name("  John Doe  ")
    assert result == "John"


def test_get_first_name_with_multiple_spaces_between_names():
    """Test that multiple spaces between names are handled correctly."""
    result = get_first_name("John    Doe")
    assert result == "John"


def test_get_first_name_with_only_whitespace():
    """Test that string with only whitespace returns 'there'."""
    result = get_first_name("   ")
    assert result == "there"


def test_get_first_name_with_tabs_and_newlines():
    """Test that tabs and newlines are treated as whitespace."""
    result = get_first_name("\t\nJohn\t\nDoe\t\n")
    assert result == "John"


def test_get_first_name_with_special_characters():
    """Test that names with special characters are handled correctly."""
    result = get_first_name("Jean-Pierre Dupont")
    assert result == "Jean-Pierre"


@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("", "there"),
        (None, "there"),
        ("   ", "there"),
        ("Alice", "Alice"),
        ("Alice Bob", "Alice"),
        ("Alice Bob Charlie", "Alice"),
        ("  Alice  Bob  ", "Alice"),
        ("Mary-Jane Watson", "Mary-Jane"),
        ("José María García", "José"),
        ("李小明 李", "李小明"),
        ("O'Connor Smith", "O'Connor"),
        ("van der Berg", "van"),
        ("123 456", "123"),
        ("@username display", "@username"),
    ],
)
def test_get_first_name_parametrized(input_name, expected):
    """Test various input scenarios with parametrized test cases."""
    result = get_first_name(input_name)
    assert result == expected
