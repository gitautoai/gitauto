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
    # Expected: length > 10, and if truncated, should reserve 4 chars for " ..."
    # So, original string length=... Given our logic, if excess is at least 4, then truncation happens.
    # The truncated string will be: first (10-4)=6 characters + " ..."
    expected = f"{long_string[:6]} ..."
    assert result == expected
    assert len(result) == 10


def test_truncate_string_equal_to_max():
    """Test that strings exactly equal to max_length are not truncated."""
    string = "Exactly thirty characters!!!!"
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
    # Truncated string: first (30-4)=26 chars from string + " ..."
    expected = f"{string[:26]} ..."
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
    # For long_key: (10-4)=6 chars + " ..."
    expected = f"{'This i' if 'This i' else ''} ..."  # Actually directly compute:
    expected = f"{test_dict['long_key'][:6]} ..."
    assert result["long_key"] == expected
    assert len(result["long_key"]) == 10


def test_truncate_list():
    """Test that list items are properly truncated."""
    test_list = ["short item", "This is a very long item that should be truncated"]
    result = truncate_value(test_list, 10)
    assert result[0] == "short item"
    expected = f"{test_list[1][:6]} ..."
    assert result[1] == expected
    assert len(result[1]) == 10


def test_truncate_tuple():
    """Test that tuple items are properly truncated while maintaining tuple type."""
    test_tuple = ("short item", "This is a very long item that should be truncated")
    result = truncate_value(test_tuple, 10)
    assert isinstance(result, tuple)
    assert result[0] == "short item"
    expected = f"{test_tuple[1][:6]} ..."
    assert result[1] == expected
    assert len(result[1]) == 10


def test_truncate_nested_structures():
    """Test that nested data structures are recursively truncated."""
    nested = {
        "tuple": ("short", "This is a very long item that should be truncated"),
        "list": ["short", "This is a very long item that should be truncated"],
        "dict": {"key": "This is a very long item that should be truncated"}
    }
    result = truncate_value(nested, 10)
    expected = f"{nested['tuple'][1][:6]} ..."
    assert result["tuple"][1] == expected
    expected = f"{nested['list'][1][:6]} ..."
    assert result["list"][1] == expected
    expected = f"{nested['dict']['key'][:6]} ..."
    assert result["dict"]["key"] == expected
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
    # For max_length 10, reserve 4 for " ...", leaving 6 for content
    result = truncate_value("1234567890123", 10)  # 13 chars, excess = 3 (< 4)
    assert result == "1234567890123"  # No truncation
    
    result = truncate_value("12345678901234", 10)  # 14 chars, excess = 4 (>= 4)
    # Truncated: first 6 chars + " ..."
    expected = f"{'123456' if True else ''} ..."
    expected = f"{'123456'} ..."
    assert result == expected
    assert len(result) == 10


def test_truncate_edge_cases():
    """Test edge cases for truncation logic."""
    # Test with max_length smaller than ellipsis
    result = truncate_value("hello", 3)
    assert result == "hello"  # No truncation since excess < 4
    
    # Test with very long string and small max_length
    result = truncate_value("This is a very long string", 5)
    expected = f"{ 'T' } ..."  # (5-4=1 char + " ...")
    assert result == expected
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
    expected = f"{mixed_dict['string'][:11]} ..."  # 15-4=11
    assert result["string"] == expected
    assert len(result["string"]) == 15
    assert result["number"] == 42
    assert result["boolean"] is True
    assert result["none"] is None
    assert result["list"][0] == "short"
    expected = f"{mixed_dict['list'][1][:11]} ..."
    assert result["list"][1] == expected
    assert len(result["list"][1]) == 15
