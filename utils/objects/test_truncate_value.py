from utils.objects.truncate_value import truncate_value


def test_truncate_value_short_string():
    """Test that short strings are not truncated."""
    short_string = "hello"
    result = truncate_value(short_string)
    assert result == "hello"


def test_truncate_value_long_string():
    """Test that long strings are truncated with ellipsis."""
    long_string = "a" * 50  # 50 characters, default max_length is 30
    result = truncate_value(long_string)
    expected = "a" * 30 + "..."
    assert result == expected
    assert len(result) == 33  # 30 chars + "..."


def test_truncate_value_string_exact_length():
    """Test string that is exactly max_length."""
    exact_string = "a" * 30  # Exactly 30 characters
    result = truncate_value(exact_string)
    assert result == exact_string
    assert len(result) == 30


def test_truncate_value_custom_max_length():
    """Test truncation with custom max_length."""
    long_string = "hello world this is a test"
    result = truncate_value(long_string, max_length=10)
    assert result == "hello worl..."
    assert len(result) == 13  # 10 chars + "..."


def test_truncate_value_dict():
    """Test truncation of dictionary values."""
    test_dict = {
        "short": "hello",
        "long": "a" * 50,
        "number": 42,
        "nested": {"inner": "b" * 40}
    }
    result = truncate_value(test_dict)
    
    assert result["short"] == "hello"
    assert result["long"] == "a" * 30 + "..."
    assert result["number"] == 42
    assert result["nested"]["inner"] == "b" * 30 + "..."


def test_truncate_value_list():
    """Test truncation of list items."""
    test_list = [
        "short",
        "a" * 50,
        42,
        ["nested", "b" * 40]
    ]
    result = truncate_value(test_list)
    
    assert result[0] == "short"
    assert result[1] == "a" * 30 + "..."
    assert result[2] == 42
    assert result[3][0] == "nested"
    assert result[3][1] == "b" * 30 + "..."


def test_truncate_value_tuple():
    """Test truncation of tuple items."""
    test_tuple = (
        "short",
        "a" * 50,
        42,
        ("nested", "b" * 40)
    )
    result = truncate_value(test_tuple)
    
    assert isinstance(result, tuple)
    assert result[0] == "short"
    assert result[1] == "a" * 30 + "..."
    assert result[2] == 42
    assert result[3][0] == "nested"
    assert result[3][1] == "b" * 30 + "..."


def test_truncate_value_primitive_types():
    """Test that primitive types are returned unchanged."""
    assert truncate_value(42) == 42
    assert truncate_value(3.14) == 3.14
    assert truncate_value(True) is True
    assert truncate_value(False) is False
    assert truncate_value(None) is None


def test_truncate_value_empty_containers():
    """Test truncation of empty containers."""
    assert truncate_value({}) == {}
    assert truncate_value([]) == []
    assert truncate_value(()) == ()


def test_truncate_value_complex_nested_structure():
    """Test truncation of complex nested data structures."""
    complex_data = {
        "users": [
            {
                "name": "John Doe",
                "bio": "a" * 100,  # Long bio
                "tags": ["developer", "b" * 50],  # Long tag
                "metadata": ("info", "c" * 60)  # Long tuple item
            }
        ],
        "settings": {
            "theme": "dark",
            "description": "d" * 80  # Long description
        }
    }
    
    result = truncate_value(complex_data)
    
    # Check that nested long strings are truncated
    assert result["users"][0]["bio"] == "a" * 30 + "..."
    assert result["users"][0]["tags"][1] == "b" * 30 + "..."
    assert result["users"][0]["metadata"][1] == "c" * 30 + "..."
    assert result["settings"]["description"] == "d" * 30 + "..."
    
    # Check that short strings remain unchanged
    assert result["users"][0]["name"] == "John Doe"
    assert result["users"][0]["tags"][0] == "developer"
    assert result["users"][0]["metadata"][0] == "info"
    assert result["settings"]["theme"] == "dark"