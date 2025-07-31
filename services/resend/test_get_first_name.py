import pytest

from services.resend.get_first_name import get_first_name


def test_get_first_name_with_empty_string():
    """Test that empty string returns 'there'."""
    result = get_first_name("")
    assert result == "there"


def test_get_first_name_with_none():
    """Test that None returns 'there'."""
    result = get_first_name(None)
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


def test_get_first_name_with_single_character():
    """Test that single character name is handled correctly."""
    result = get_first_name("A")
    assert result == "A"


def test_get_first_name_with_single_character_and_space():
    """Test that single character followed by space and name works."""
    result = get_first_name("A B")
    assert result == "A"


def test_get_first_name_with_numeric_first_name():
    """Test that numeric first name is handled correctly."""
    result = get_first_name("123 Smith")
    assert result == "123"


def test_get_first_name_with_mixed_whitespace_types():
    """Test that mixed whitespace types are handled correctly."""
    result = get_first_name(" \t\n John \r\n Doe \t ")
    assert result == "John"


def test_get_first_name_with_unicode_characters():
    """Test that unicode characters are handled correctly."""
    result = get_first_name("José María")
    assert result == "José"


def test_get_first_name_with_emoji():
    """Test that emoji characters are handled correctly."""
    result = get_first_name("😀 Smith")
    assert result == "😀"


def test_get_first_name_with_very_long_name():
    """Test that very long names are handled correctly."""
    long_name = "Supercalifragilisticexpialidocious Johnson"
    result = get_first_name(long_name)
    assert result == "Supercalifragilisticexpialidocious"


def test_get_first_name_with_apostrophe():
    """Test that names with apostrophes are handled correctly."""
    result = get_first_name("O'Connor Smith")
    assert result == "O'Connor"


def test_get_first_name_with_hyphenated_last_name():
    """Test that hyphenated last names don't affect first name extraction."""
    result = get_first_name("John Smith-Jones")
    assert result == "John"


def test_get_first_name_with_title_case():
    """Test that title case names are preserved."""
    result = get_first_name("McDonald Johnson")
    assert result == "McDonald"


def test_get_first_name_with_lowercase():
    """Test that lowercase names are preserved."""
    result = get_first_name("john doe")
    assert result == "john"


def test_get_first_name_with_uppercase():
    """Test that uppercase names are preserved."""
    result = get_first_name("JOHN DOE")
    assert result == "JOHN"


def test_get_first_name_with_mixed_case():
    """Test that mixed case names are preserved."""
    result = get_first_name("jOhN dOe")
    assert result == "jOhN"


def test_get_first_name_with_zero_width_space():
    """Test that zero-width spaces are handled correctly."""
    result = get_first_name("John\u200b Doe")
    assert result == "John"


def test_get_first_name_with_non_breaking_space():
    """Test that non-breaking spaces are handled correctly."""
    result = get_first_name("John\u00a0Doe")
    assert result == "John"


@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("", "there"),
        (None, "there"),
        ("   ", "there"),
        ("\t\n\r", "there"),
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
        ("A B C D E", "A"),
        ("😀 😁 😂", "😀"),
        ("McDonald Johnson", "McDonald"),
        ("john doe", "john"),
        ("JOHN DOE", "JOHN"),
        ("jOhN dOe", "jOhN"),
        ("X Æ A-12", "X"),
        ("Dr. Smith", "Dr."),
        ("Mr. John Doe", "Mr."),
        ("von Neumann", "von"),
        ("de la Cruz", "de"),
        ("al-Rashid", "al-Rashid"),
        ("bin Laden", "bin"),
        ("ibn Sina", "ibn"),
        ("Ñoño García", "Ñoño"),
        ("Müller Schmidt", "Müller"),
        ("Øyvind Hansen", "Øyvind"),
        ("Žiga Novak", "Žiga"),
        ("Çağlar Öztürk", "Çağlar"),
        ("Владимир Путин", "Владимир"),
        ("محمد علي", "محمد"),
        ("田中 太郎", "田中"),
        ("김철수 김", "김철수"),
        ("Αλέξανδρος Παπαδόπουλος", "Αλέξανδρος"),
    ],
)
def test_get_first_name_parametrized(input_name, expected):
    """Test various input scenarios with parametrized test cases."""
    result = get_first_name(input_name)
    assert result == expected


class TestGetFirstNameEdgeCases:
    """Test class for edge cases and boundary conditions."""

    def test_falsy_values(self):
        """Test various falsy values."""
        falsy_values = [None, "", 0, False, [], {}]
        for value in falsy_values:
            if isinstance(value, str) or value is None:
                result = get_first_name(value)
                assert result == "there"

    def test_whitespace_only_variations(self):
        """Test different types of whitespace-only strings."""
        whitespace_variations = [
            " ",
            "  ",
            "\t",
            "\n",
            "\r",
            "\r\n",
            " \t\n\r ",
            "\u00a0",  # non-breaking space
            "\u2000",  # en quad
            "\u2001",  # em quad
            "\u2002",  # en space
            "\u2003",  # em space
        ]
        for whitespace in whitespace_variations:
            result = get_first_name(whitespace)
            assert result == "there"

    def test_single_word_variations(self):
        """Test single word with various characteristics."""
        single_words = [
            "A",
            "Ab",
            "ABC",
            "a",
            "ab",
            "abc",
            "123",
            "1a2b3c",
            "@user",
            "#tag",
            "$money",
            "%percent",
            "&and",
            "*star",
            "+plus",
            "=equal",
            "?question",
            "!exclamation",
            "~tilde",
            "`backtick",
            "|pipe",
            "\\backslash",
            "/slash",
            "<less",
            ">greater",
            "\"quote",
            "'apostrophe",
            ";semicolon",
            ":colon",
            ",comma",
            ".period",
            "()parentheses",
            "[]brackets",
            "{}braces",
        ]
        for word in single_words:
            result = get_first_name(word)
            assert result == word

    def test_multiple_consecutive_spaces(self):
        """Test names with multiple consecutive spaces."""
        test_cases = [
            ("John  Doe", "John"),
            ("John   Doe", "John"),
            ("John    Doe", "John"),
            ("John     Doe", "John"),
            ("John      Doe", "John"),
        ]
        for input_name, expected in test_cases:
            result = get_first_name(input_name)
            assert result == expected

    def test_mixed_whitespace_and_names(self):
        """Test names with mixed whitespace characters."""
        test_cases = [
            ("\tJohn\tDoe\t", "John"),
            ("\nJohn\nDoe\n", "John"),
            ("\rJohn\rDoe\r", "John"),
            (" \t\nJohn \t\nDoe \t\n", "John"),
            ("\u00a0John\u00a0Doe\u00a0", "John"),
        ]
        for input_name, expected in test_cases:
            result = get_first_name(input_name)
            assert result == expected
