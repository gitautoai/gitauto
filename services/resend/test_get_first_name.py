import pytest

from services.resend.get_first_name import get_first_name


class TestGetFirstName:
    def test_get_first_name_with_single_name(self):
        result = get_first_name("John")
        assert result == "John"

    def test_get_first_name_with_full_name(self):
        result = get_first_name("John Doe")
        assert result == "John"

    def test_get_first_name_with_multiple_names(self):
        result = get_first_name("John Michael Doe")
        assert result == "John"

    def test_get_first_name_with_empty_string(self):
        result = get_first_name("")
        assert result == "there"

    def test_get_first_name_with_none(self):
        result = get_first_name(None)
        assert result == "there"

    def test_get_first_name_with_whitespace_only(self):
        result = get_first_name("   ")
        assert result == "there"

    def test_get_first_name_with_leading_whitespace(self):
        result = get_first_name("  John Doe")
        assert result == "John"

    def test_get_first_name_with_trailing_whitespace(self):
        result = get_first_name("John Doe  ")
        assert result == "John"

    def test_get_first_name_with_multiple_spaces(self):
        result = get_first_name("John    Doe")
        assert result == "John"

    def test_get_first_name_with_special_characters(self):
        result = get_first_name("John-Michael O'Connor")
        assert result == "John-Michael"

    def test_get_first_name_with_numbers(self):
        result = get_first_name("John123 Doe456")
        assert result == "John123"
