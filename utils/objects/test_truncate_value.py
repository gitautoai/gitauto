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
    # For max_length 10, truncation happens if excess >= 4, so we take first 6 characters and append " ..."
    # Expected: first 6 characters + " ..." = "This i ..."
    assert result == "This i ..."
    assert len(result) == 10


def test_truncate_string_equal_to_max():
    """Test that strings exactly equal to max_length are not truncated."""
    string = "Exactly thirty characters!!!!"
    result = truncate_value(string, 30)
    assert result == string
    assert len(result) == 30


def test_truncate_string_marginally_longer():
    """Test that strings only marginally longer (less than 4 chars excess) are not truncated."""
    # String length is 32, max_length is 30, excess = 2 (<4), so no truncation
    string = "This string is thirty-two chars"
    result = truncate_value(string, 30)
    assert result == string
    assert len(result) == 32


def test_truncate_string_significantly_longer():
    """Test that strings significantly longer (4+ chars excess) are truncated."""
    # Ensure the string length is at least max_length + 4 to trigger truncation
    # Using a string of length 34: "This string is thirty-four chars!!" (34 characters)
    # For max_length=30, result should be first (30-4)=26 characters + " ...".
    string = "This string is thirty-four chars!!"
    result = truncate_value(string, 30)
    expected = string[:26] + " ..."
    assert result == expected
    assert len(result) == 30


def test_truncate_dict():
    """Test that dictionary values are properly truncated."""
    test_dict = {
        "short_key": "short value",
        "long_key": "This is a very long value that should be truncated"
    }
    result = truncate_value(test_dict, 10)
    assert result["short_key"] == "short value"
    # For max_length 10, expected: first (10-4)=6 characters + " ..."
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
    assert result[1] == "This i ..."
    assert len(result[1]) == 10


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
    assert len(result["tuple"][1]) == 10
    assert len(result["list"][1]) == 10
    assert len(result["dict"]["key"]) == 10


def test_non_string_values():
    """Test that non-string values are returned unchanged."""
    assert truncate_value(42, 10) == 42
    assert truncate_value(3.14, 10) == 3.14
    assert truncate_value(None, 10) is None
    assert truncate_value(True, 10) is True


def test_truncate_empty_string():
    """Test that empty strings are returned unchanged."""
    assert truncate_value("", 10) == ""


def test_truncate_whitespace_string():
    """Test that strings containing only whitespace are handled correctly."""
    assert truncate_value("   ", 10) == "   "


def test_truncate_exact_boundary():
    """Test truncation at exact boundary conditions."""
    # For max_length 10, we reserve 4 characters for " ...", leaving 6 for content
    result = truncate_value("1234567890123", 10)  # 13 chars, excess = 3 (< 4)
    assert result == "1234567890123"  # No truncation
    
    result = truncate_value("12345678901234", 10)  # 14 chars, excess = 4 (>= 4)
    # Expected: first 6 characters + " ..." = "123456 ..."
    assert result == "123456 ..."
    assert len(result) == 10


def test_truncate_edge_cases():
    """Test edge cases for truncation logic."""
    # Test with max_length smaller than needed for ellipsis truncation
    result = truncate_value("hello", 3)
    assert result == "hello"  # No truncation since excess < 4
    
    # Test with very long string and a small max_length
    result = truncate_value("This is a very long string", 5)
    # For max_length 5, (5-4)=1 char + " ..." = "T ..."
    assert result == "T ..."
    assert len(result) == 5


def test_truncate_collections_with_mixed_types():
    """Test collections containing mixed data types."""
    mixed_dict = {
        "string": "This is a long string that needs truncation",
        "number": 42,
        "boolean": True,
        "none": None,
        "list": ["short", "This is another long string for truncation"]
    }
    result = truncate_value(mixed_dict, 15)
    # For max_length 15, we reserve 4 characters for " ...", so first 11 characters are kept
    assert result["string"] == "This is a l ..."
    assert len(result["string"]) == 15
    assert result["number"] == 42
    assert result["boolean"] is True
    assert result["none"] is None
    assert result["list"][0] == "short"
    assert result["list"][1] == "This is ano ..."
    assert len(result["list"][1]) == 15
