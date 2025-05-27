import pytest
from utils.objects.truncate_value import truncate_value


def test_truncate_string_shorter_than_max():
    """Test that strings shorter than max_length are returned unchanged."""
    result = truncate_value("short string", 30)
    assert result == "short string"


def test_truncate_string_longer_than_max():
    """Test that longer strings are truncated with ' ...' suffix."""
    long_string = "This is a very long string that exceeds the maximum length"
    result = truncate_value(long_string, 10)
    assert result == "This i ..."
    assert len(result) == 10


def test_truncate_string_equal_to_max():
    """Test that strings exactly equal to max_length are not truncated."""
    string = "Exactly thirty characters!!!!!!"
    result = truncate_value(string, 30)
    assert result == string
    assert len(result) == 30


def test_truncate_string_marginally_longer():
    """Test that strings only marginally longer (less than 4 chars) are not truncated."""
    # String is 32 chars, max is 30, difference is 2 (< 4), so no truncation
    string = "This string is thirty-two chars"
    result = truncate_value(string, 30)
    assert result == string
    assert len(result) == 32


def test_truncate_string_significantly_longer():
    """Test that strings significantly longer (4+ chars excess) are truncated."""
    # String is 34 chars, max is 30, difference is 4, so truncation occurs
    string = "This string is thirty-four chars!"
    result = truncate_value(string, 30)
    assert result == "This string is thirty-four ..."
    assert len(result) == 30


def test_truncate_dict():
    """Test that dictionary values are properly truncated."""
    test_dict = {
        "short_key": "short value",
        "long_key": "This is a very long value that should be truncated"
    }
    result = truncate_value(test_dict, 10)
    assert result["short_key"] == "short value"
    assert result["long_key"] == "This i ..."
    assert len(result["long_key"]) == 10


def test_truncate_list():
    """Test that list items are properly truncated."""
    test_list = ["short item", "This is a very long item that should be truncated"]
    result = truncate_value(test_list, 10)
    assert result[0] == "short item"
    assert result[1] == "This i ..."
    assert len(result[1]) == 10


def test_truncate_tuple():
    """Test that tuple items are properly truncated while maintaining tuple type."""
    test_tuple = ("short item", "This is a very long item that should be truncated")
    result = truncate_value(test_tuple, 10)
    assert isinstance(result, tuple)
    assert result[0] == "short item"
