import pytest
from utils.objects.truncate_value import truncate_value


def test_truncate_string_shorter_than_max():
    result = truncate_value("short string", 30)
    assert result == "short string"


def test_truncate_string_longer_than_max():
    long_string = "This is a very long string that exceeds the maximum length"
    result = truncate_value(long_string, 10)
    assert result == "This i ..."


def test_truncate_string_equal_to_max():
    string = "Exactly thirty characters!!!!"
    result = truncate_value(string, 30)
    assert result == string


def test_truncate_dict():
    test_dict = {
        "short_key": "short value",
        "long_key": "This is a very long value that should be truncated"
    }
    result = truncate_value(test_dict, 10)
    assert result["short_key"] == "short value"
    assert result["long_key"] == "This i ..."


def test_truncate_list():
    test_list = ["short item", "This is a very long item that should be truncated"]
    result = truncate_value(test_list, 10)
    assert result[0] == "short item"
    assert result[1] == "This is ..."


def test_truncate_tuple():
    test_tuple = ("short item", "This is a very long item that should be truncated")
    result = truncate_value(test_tuple, 10)
    assert isinstance(result, tuple)
    assert result[0] == "short item"
    assert result[1] == "This is ..."


def test_truncate_nested_structures():
    nested = {
        "tuple": ("short", "This is a very long item that should be truncated"),
        "list": ["short", "This is a very long item that should be truncated"],
        "dict": {"key": "This is a very long item that should be truncated"}
    }
    result = truncate_value(nested, 10)
    assert result["tuple"][1] == "This is ..."
    assert result["list"][1] == "This is ..."
    assert result["dict"]["key"] == "This is ..."
