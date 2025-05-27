import pytest
from utils.objects.truncate_value import truncate_value


def test_truncate_string_exceeding_max_length():
    long_string = "This is a very long string that exceeds the max length"
    result = truncate_value(long_string, max_length=10)
    assert result == "This is a ..."
    assert len(result) == 13  # 10 chars + 3 dots


def test_truncate_string_within_max_length():
    short_string = "Short string"
    result = truncate_value(short_string, max_length=30)
    assert result == short_string


def test_truncate_dict_with_long_string_values():
    test_dict = {
        "key1": "This is a very long string that exceeds the max length",
        "key2": "Short string"
    }
    result = truncate_value(test_dict, max_length=10)
    assert result["key1"] == "This is a ..."
    assert result["key2"] == "Short string"


def test_truncate_list_with_long_string_values():
    test_list = [
        "This is a very long string that exceeds the max length",
        "Short string"
    ]
    result = truncate_value(test_list, max_length=10)
    assert result[0] == "This is a ..."
    assert result[1] == "Short string"


def test_truncate_tuple_with_long_string_values():
    test_tuple = (
        "This is a very long string that exceeds the max length",
        "Short string"
    )
    result = truncate_value(test_tuple, max_length=10)
    assert isinstance(result, tuple)
    assert result[0] == "This is a ..."
    assert result[1] == "Short string"


def test_truncate_nested_structures():
    nested_structure = {
        "tuple_key": ("Long string to be truncated", "Short"),
        "list_key": ["Another long string to truncate", 123],
        "dict_key": {"inner_key": "Very long inner string value"}
    }
    result = truncate_value(nested_structure, max_length=15)
    assert result["tuple_key"][0] == "Long string to ..."
    assert result["list_key"][0] == "Another long s..."
    assert result["dict_key"]["inner_key"] == "Very long inner..."