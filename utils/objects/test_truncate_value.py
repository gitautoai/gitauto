from utils.objects.truncate_value import truncate_value
from datetime import datetime


def test_truncate_string_within_limit():
    result = truncate_value("short", 10)
    assert result == "short"


def test_truncate_string_exceeds_limit():
    result = truncate_value("this is a very long string", 10)
    assert result == "this is a ..."


def test_truncate_string_exactly_at_limit():
    result = truncate_value("exactly ten", 11)
    assert result == "exactly ten"


def test_truncate_string_one_over_limit():
    result = truncate_value("exactly tens", 11)
    assert result == "exactly ten..."


def test_truncate_empty_string():
    result = truncate_value("", 10)
    assert result == ""


def test_truncate_string_with_custom_max_length():
    result = truncate_value("hello world", 5)
    assert result == "hello..."


def test_truncate_dict_simple():
    input_dict = {"key": "short"}
    result = truncate_value(input_dict, 10)
    assert result == {"key": "short"}


def test_truncate_dict_with_long_values():
    input_dict = {"key": "this is a very long string"}
    result = truncate_value(input_dict, 10)
    assert result == {"key": "this is a ..."}


def test_truncate_nested_dict():
    input_dict = {"outer": {"inner": "this is a very long string"}}
    result = truncate_value(input_dict, 10)
    assert result == {"outer": {"inner": "this is a ..."}}


def test_truncate_empty_dict():
    result = truncate_value({}, 10)
    assert result == {}


def test_truncate_list_simple():
    input_list = ["short", "text"]
    result = truncate_value(input_list, 10)
    assert result == ["short", "text"]


def test_truncate_list_with_long_strings():
    input_list = ["this is a very long string", "short"]
    result = truncate_value(input_list, 10)
    assert result == ["this is a ...", "short"]


def test_truncate_empty_list():
    result = truncate_value([], 10)
    assert result == []


def test_truncate_tuple_simple():
    input_tuple = ("short", "text")
    result = truncate_value(input_tuple, 10)
    assert result == ("short", "text")


def test_truncate_tuple_with_long_strings():
    input_tuple = ("this is a very long string", "short")
    result = truncate_value(input_tuple, 10)
    assert result == ("this is a ...", "short")


def test_truncate_empty_tuple():
    result = truncate_value((), 10)
    assert result == ()


def test_truncate_nested_structures():
    input_data = {
        "list": ["this is a very long string", "short"],
        "tuple": ("this is a very long string", "short"),
        "dict": {"nested": "this is a very long string"},
    }
    result = truncate_value(input_data, 10)
    expected = {
        "list": ["this is a ...", "short"],
        "tuple": ("this is a ...", "short"),
        "dict": {"nested": "this is a ..."},
    }
    assert result == expected


def test_truncate_non_string_types():
    assert truncate_value(42, 10) == 42
    assert truncate_value(3.14, 10) == 3.14
    assert truncate_value(True, 10) is True
    assert truncate_value(None, 10) is None


def test_truncate_with_default_max_length():
    long_string = "a" * 50
    result = truncate_value(long_string)
    assert result == "a" * 30 + "..."


def test_truncate_complex_nested_structure():
    input_data = [
        {
            "users": [
                ("this is a very long username", "this is a very long email"),
                {"name": "this is a very long name", "age": 25},
            ]
        }
    ]
    result = truncate_value(input_data, 15)
    expected = [
        {
            "users": [
                ("this is a very ...", "this is a very ..."),
                {"name": "this is a very ...", "age": 25},
            ]
        }
    ]
    assert result == expected

def test_truncate_datetime():
    """Test that datetime objects are converted to ISO format strings."""
    dt = datetime(2023, 1, 1, 12, 30, 45)
    result = truncate_value(dt)
    assert result == "2023-01-01T12:30:45"


def test_truncate_datetime_in_dict():
    """Test that datetime objects in dictionaries are converted to ISO format strings."""
    input_dict = {"created_at": datetime(2023, 1, 1, 12, 30, 45), "name": "test"}
    result = truncate_value(input_dict)
