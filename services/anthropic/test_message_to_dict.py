from services.anthropic.message_to_dict import message_to_dict


def create_mock_message(**kwargs):
    from types import SimpleNamespace
    return SimpleNamespace(**kwargs)


def test_message_to_dict_with_dict():
    """Test that a dictionary is returned as is."""
    message = {"role": "user", "content": "Hello"}
    result = message_to_dict(message)
    assert result is message


def test_message_to_dict_with_object_all_attributes():
    """Test with an object that has all attributes."""
    message = create_mock_message(
        role="assistant",
        content="Hello there",
        tool_calls=[{"type": "function", "function": {"name": "get_weather"}}],
        tool_call_id="call_123",
        name="weather_tool",
    )

    result = message_to_dict(message)

    assert result == {
        "role": "assistant",
        "content": "Hello there",
        "tool_calls": [{"type": "function", "function": {"name": "get_weather"}}],
        "tool_call_id": "call_123",
        "name": "weather_tool",
    }


def test_message_to_dict_with_object_some_attributes():
    """Test with an object that has only some attributes."""
    message = create_mock_message(role="user", content="Hello")

    result = message_to_dict(message)

    assert result == {"role": "user", "content": "Hello"}


def test_message_to_dict_with_object_no_attributes():
    """Test with an object that has none of the expected attributes."""
    message = create_mock_message(unexpected="value")

    result = message_to_dict(message)

    assert result == {}


def test_message_to_dict_with_object_none_values():
    """Test with an object that has attributes with None values."""
    message = create_mock_message(
        role="user", content=None, tool_calls=None, tool_call_id=None, name=None
    )

    result = message_to_dict(message)

    assert result == {"role": "user"}


def test_message_to_dict_with_empty_object():
    """Test with an empty object."""
    message = create_mock_message()

    result = message_to_dict(message)

    assert result == {}


def test_message_to_dict_with_none():
    """Test with None as input."""
    result = message_to_dict(None)

    assert result == {}


def test_message_to_dict_with_primitive_types():
    """Test with primitive types that don't have attributes."""
    for value in [42, "string", True, 3.14]:
        result = message_to_dict(value)
        assert result == {}
