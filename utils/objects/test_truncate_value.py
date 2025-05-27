import pytest
from utils.objects.truncate_value import truncate_value


def test_truncate_string_shorter_than_max():
    """Test that strings shorter than max_length are returned unchanged."""
    result = truncate_value("short string", 30)
    assert result == "short string"


def test_truncate_string_longer_than_max():
    """Test that strings longer than max_length are truncated with ' ...' suffix."""
    long_string = "This is a very long string that exceeds the maximum length"
    result = truncate_value(long_string, 10)
    assert result == "This i ..."


def test_truncate_string_equal_to_max():
    """Test that strings exactly equal to max_length are returned unchanged."""
    string = "Exactly thirty characters!!!!"
    result = truncate_value(string, 30)
    assert result == string


def test_truncate_dict():
    """Test that dictionary values are properly truncated."""
    test_dict = {
        "short_key": "short value",
        "long_key": "This is a very long value that should be truncated"
    }
    result = truncate_value(test_dict, 10)
    assert result["short_key"] == "short value"
    assert result["long_key"] == "This i ..."


def test_truncate_list():
    """Test that list items are properly truncated."""
    test_list = ["short item", "This is a very long item that should be truncated"]
    result = truncate_value(test_list, 10)
    assert result[0] == "short item"
    assert result[1] == "This i ..."


def test_truncate_tuple():
    """Test that tuple items are properly truncated while maintaining tuple type."""
    test_tuple = ("short item", "This is a very long item that should be truncated")
    result = truncate_value(test_tuple, 10)
    assert isinstance(result, tuple)
    assert result[0] == "short item"
    assert result[1] == "This i ..."


def test_truncate_nested_structures():
    """Test that nested data structures are recursively truncated."""
    nested = {
        "tuple": ("short", "This is a very long item that should be truncated"),
        "list": ["short", "This is a very long item that should be truncated"],
        "dict": {"key": "This is a very long item that should be truncated"}
    }
    result = truncate_value(nested, 10)
    assert result["tuple"][1] == "This i ..."
    assert result["list"][1] == "This i ..."
    assert result["dict"]["key"] == "This i ..."


def test_non_string_values():
    """Test that non-string values are returned unchanged."""
    assert truncate_value(42, 10) == 42
    assert truncate_value(3.14, 10) == 3.14
    assert truncate_value(None, 10) is None
    assert truncate_value(True, 10) is True


def test_empty_string():
    """Test that empty strings are returned unchanged."""
    assert truncate_value("", 10) == ""