import pytest
from utils.objects.truncate_value import truncate_value


def test_truncate_string_shorter_than_max():
    result = truncate_value("short string", 30)
    assert result == "short string"


def test_truncate_string_longer_than_max():
    long_string = "This is a very long string that exceeds the maximum length"
    result = truncate_value(long_string, 10)
    assert result == "This i..."


def test_truncate_string_equal_to_max():
    string = "Exactly thirty characters long!!"
    result = truncate_value(string, 30)
    assert result == string


def test_truncate_dict():
    test_dict = {
        "short_key": "short value",
        "long_key": "This is a very long value that should be truncated"
    }
    result = truncate_value(test_dict, 10)
    assert result["short_key"] == "short value"
    assert result["long_key"] == "This i..."


def test_truncate_list():
    test_list = ["short item", "This is a very long item that should be truncated"]
    result = truncate_value(test_list, 10)
    assert result[0] == "short item"
    assert result[1] == "This i..."


def test_truncate_tuple():
    test_tuple = ("short item", "This is a very long item that should be truncated")
    result = truncate_value(test_tuple, 10)
    assert isinstance(result, tuple)
    assert result[0] == "short item"
    assert result[1] == "This i..."


def test_truncate_nested_structures():
    nested = {
        "tuple": ("short", "This is a very long item that should be truncated"),
        "list": ["short", "This is a very long item that should be truncated"],
        "dict": {"key": "This is a very long item that should be truncated"}
    }
    result = truncate_value(nested, 10)
    assert result["tuple"][1] == "This i..."
    assert result["list"][1] == "This i..."
    assert result["dict"]["key"] == "This i..."


def test_truncate_non_string_values():
    """Test that non-string values are returned unchanged"""
    assert truncate_value(42, 10) == 42
    assert truncate_value(3.14, 10) == 3.14
    assert truncate_value(None, 10) is None
    assert truncate_value(True, 10) is True


def test_truncate_empty_collections():
    """Test empty collections are handled correctly"""
    assert truncate_value({}, 10) == {}
    assert truncate_value([], 10) == []
    assert truncate_value((), 10) == ()


def test_truncate_with_default_max_length():
    """Test using the default max_length parameter"""
    long_string = "This is a string that is longer than thirty characters"
    result = truncate_value(long_string)  # Using default max_length=30
    assert result == "This is a string that is lon..."


def test_truncate_mixed_nested_structure():
    """Test a complex nested structure with mixed types"""
    complex_struct = {
        "int": 42,
        "str": "This is a very long string to be truncated",
        "list": [1, "Long string to truncate", {"nested": "Another long string"}],
        "tuple": (True, "Yet another long string", [1, 2, 3]),
        "dict": {"key": "A long string in a nested dict"}
    }
    result = truncate_value(complex_struct, 15)

    assert result["int"] == 42
    assert result["str"] == "This is a ve..."
    assert result["list"][0] == 1
    assert result["list"][1] == "Long strin..."
    assert result["list"][2]["nested"] == "Another lo..."
    assert result["tuple"][0] is True
    assert result["tuple"][1] == "Yet anothe..."
    assert result["tuple"][2] == [1, 2, 3]
    assert result["dict"]["key"] == "A long str..."
