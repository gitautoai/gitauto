import pytest
from utils.objects.truncate_value import truncate_value


def test_truncate_string_exceeding_max_length():
    """Test truncation of strings that exceed max_length."""
    long_string = "This is a very long string that exceeds the max length"
    result = truncate_value(long_string, max_length=10)
    assert result == "This is a ..."
    assert len(result) == 13  # 10 chars + 3 dots


def test_truncate_string_within_max_length():
    """Test that strings within max_length are not truncated."""
    short_string = "Short string"
    result = truncate_value(short_string, max_length=30)
    assert result == short_string


def test_truncate_dict_with_long_string_values():
    """Test truncation of string values within dictionaries."""
    test_dict = {
        "key1": "This is a very long string that exceeds the max length",
        "key2": "Short string"
    }
    result = truncate_value(test_dict, max_length=10)
    assert result["key1"] == "This is a ..."
    assert result["key2"] == "Short stri..."


def test_truncate_list_with_long_string_values():
    """Test truncation of string values within lists."""
    test_list = [
        "This is a very long string that exceeds the max length",
        "Short string"
    ]
    result = truncate_value(test_list, max_length=10)
    assert result[0] == "This is a ..."
    assert result[1] == "Short stri..."


def test_truncate_tuple_with_long_string_values():
    """Test truncation of string values within tuples."""
    test_tuple = (
        "This is a very long string that exceeds the max length",
        "Short string"
    )
    result = truncate_value(test_tuple, max_length=10)
    assert isinstance(result, tuple)
    assert result[0] == "This is a ..."
    assert result[1] == "Short stri..."


def test_truncate_nested_structures():
    """Test truncation of strings in nested data structures."""
    nested_structure = {
        "tuple_key": ("Long string to be truncated", "Short"),
        "list_key": ["Another long string to truncate", 123],
        "dict_key": {"inner_key": "Very long inner string value"}
    }
    result = truncate_value(nested_structure, max_length=15)
    assert result["tuple_key"][0] == "Long string to ..."
    assert result["tuple_key"][1] == "Short"
    assert result["list_key"][0] == "Another long st..."
    assert result["list_key"][1] == 123
    assert result["dict_key"]["inner_key"] == "Very long inner..."


def test_truncate_non_string_values():
    """Test that non-string values remain unchanged."""
    non_string_values = [123, 45.67, True, None, [1, 2, 3], {"a": 1}]
    for value in non_string_values:
        result = truncate_value(value)
        assert result == value


def test_truncate_empty_collections():
    """Test that empty collections remain unchanged."""
    assert truncate_value({}) == {}
    assert truncate_value([]) == []
    assert truncate_value(()) == ()


def test_truncate_with_zero_max_length():
    """Test truncation behavior with zero max_length."""
    test_string = "Test string"
    result = truncate_value(test_string, max_length=0)
    assert result == "..."
    
    # Test non-string values with zero max_length
    assert truncate_value((), max_length=0) == ()
    assert truncate_value(123, max_length=0) == 123
    assert truncate_value(None, max_length=0) is None


def test_truncate_with_negative_max_length():
    """Test truncation behavior with negative max_length."""
    test_string = "Test string"
    result = truncate_value(test_string, max_length=-5)
    assert result == "..."
    
    # Test non-string values with negative max_length
    assert truncate_value(123, max_length=-5) == 123
    assert truncate_value(None, max_length=-5) is None


def test_truncate_empty_string():
    """Test truncation of empty strings."""
    assert truncate_value("") == ""
    assert truncate_value("", max_length=0) == "..."
    assert truncate_value("", max_length=-1) == "..."


def test_truncate_default_max_length():
    """Test truncation using the default max_length value."""
    long_string = "x" * 40
    result = truncate_value(long_string)  # default max_length=30
    assert len(result) == 33  # 30 chars + 3 dots
    assert result == ("x" * 30) + "..."


def test_truncate_exact_max_length():
    """Test string exactly at max_length boundary."""
    exact_string = "x" * 10
    result = truncate_value(exact_string, max_length=10)
    assert result == exact_string  # Should not be truncated
    
    over_string = "x" * 11
    result = truncate_value(over_string, max_length=10)
    assert result == ("x" * 10) + "..."  # Should be truncated