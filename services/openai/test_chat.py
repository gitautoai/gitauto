from unittest.mock import MagicMock, patch
from openai import OpenAIError

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from config import OPENAI_MODEL_ID_O3_MINI
from services.openai.chat import chat_with_ai


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client with proper method chaining"""
    client = MagicMock()
    return client


@pytest.fixture
def mock_chat_completion():
    """Mock ChatCompletion response"""
    completion = MagicMock(spec=ChatCompletion)
    message = MagicMock(spec=ChatCompletionMessage)
    message.content = "Test response from AI"
    choice = MagicMock(spec=Choice)
    choice.message = message
    completion.choices = [choice]
    return completion


@pytest.fixture
def mock_chat_completion_empty():
    """Mock ChatCompletion response with empty content"""
    completion = MagicMock(spec=ChatCompletion)
    message = MagicMock(spec=ChatCompletionMessage)
    message.content = None
    choice = MagicMock(spec=Choice)
    choice.message = message
    completion.choices = [choice]
    return completion


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_success(
    mock_truncate_message, mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test successful chat completion"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_truncate_message.return_value = "truncated user input"
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Test inputs
    system_input = "You are a helpful assistant"
    user_input = "Hello, how are you?"

    # Call function
    result = chat_with_ai(system_input=system_input, user_input=user_input)

    # Assertions
    assert result == "Test response from AI"
    mock_create_client.assert_called_once()
    mock_truncate_message.assert_called_once_with(input_message=user_input)
    mock_openai_client.chat.completions.create.assert_called_once_with(
        messages=[
            {
                "role": "developer",
                "content": system_input,
            },
            {
                "role": "user",
                "content": "truncated user input",
            },
        ],
        model=OPENAI_MODEL_ID_O3_MINI,
    )


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_empty_truncated_message(
    mock_truncate_message, mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test chat completion when truncate_message returns empty string"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_truncate_message.return_value = ""
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Test inputs
    system_input = "You are a helpful assistant"
    user_input = "Hello, how are you?"

    # Call function
    result = chat_with_ai(system_input=system_input, user_input=user_input)

    # Assertions
    assert result == "Test response from AI"
    mock_openai_client.chat.completions.create.assert_called_once_with(
        messages=[
            {
                "role": "developer",
                "content": system_input,
            },
            {
                "role": "user",
                "content": user_input,  # Should use original user_input when truncated is empty
            },
        ],
        model=OPENAI_MODEL_ID_O3_MINI,
    )


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_none_content(
    mock_truncate_message, mock_create_client, mock_openai_client, mock_chat_completion_empty
):
    """Test chat completion when response content is None"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_truncate_message.return_value = "truncated user input"
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion_empty

    # Test inputs
    system_input = "You are a helpful assistant"
    user_input = "Hello, how are you?"

    # Call function
    result = chat_with_ai(system_input=system_input, user_input=user_input)

    # Assertions
    assert result == ""  # Should return empty string when content is None
    mock_create_client.assert_called_once()
    mock_truncate_message.assert_called_once_with(input_message=user_input)


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_with_long_inputs(
    mock_truncate_message, mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test chat completion with long inputs that need truncation"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    long_user_input = "x" * 10000
    truncated_input = "x" * 1000
    mock_truncate_message.return_value = truncated_input
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Test inputs
    system_input = "You are a helpful assistant"

    # Call function
    result = chat_with_ai(system_input=system_input, user_input=long_user_input)

    # Assertions
    assert result == "Test response from AI"
    mock_truncate_message.assert_called_once_with(input_message=long_user_input)
    mock_openai_client.chat.completions.create.assert_called_once_with(
        messages=[
            {
                "role": "developer",
                "content": system_input,
            },
            {
                "role": "user",
                "content": truncated_input,
            },
        ],
        model=OPENAI_MODEL_ID_O3_MINI,
    )


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_empty_inputs(
    mock_truncate_message, mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test chat completion with empty inputs"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_truncate_message.return_value = ""
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Test inputs
    system_input = ""
    user_input = ""

    # Call function
    result = chat_with_ai(system_input=system_input, user_input=user_input)

    # Assertions
    assert result == "Test response from AI"
    mock_openai_client.chat.completions.create.assert_called_once_with(
        messages=[
            {"role": "developer", "content": ""},
            {"role": "user", "content": ""},  # Uses original empty user_input
        ],
        model=OPENAI_MODEL_ID_O3_MINI,
    )


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_openai_error_raises(mock_truncate_message, mock_create_client, mock_openai_client):
    """Test that OpenAI errors are raised due to handle_exceptions(raise_on_error=True)"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_truncate_message.return_value = "truncated user input"
    mock_openai_client.chat.completions.create.side_effect = OpenAIError("API Error")

    # Test inputs
    system_input = "You are a helpful assistant"
    user_input = "Hello, how are you?"

    # Call function and expect exception
    with pytest.raises(OpenAIError):
        chat_with_ai(system_input=system_input, user_input=user_input)

    # Verify mocks were called
    mock_create_client.assert_called_once()
    mock_truncate_message.assert_called_once_with(input_message=user_input)


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_attribute_error_raises(mock_truncate_message, mock_create_client, mock_openai_client):
    """Test that AttributeError is raised due to handle_exceptions(raise_on_error=True)"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_truncate_message.return_value = "truncated user input"
    mock_openai_client.chat.completions.create.side_effect = AttributeError("Missing attribute")

    # Test inputs
    system_input = "You are a helpful assistant"
    user_input = "Hello, how are you?"

    # Call function and expect exception
    with pytest.raises(AttributeError):
        chat_with_ai(system_input=system_input, user_input=user_input)


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_unicode_inputs(
    mock_truncate_message, mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test chat completion with unicode characters in inputs"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_truncate_message.return_value = "🌟 truncated unicode input 🚀"
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Test inputs with unicode
    system_input = "You are a helpful assistant 🤖"
    user_input = "Hello 👋, how are you? 🌟"

    # Call function
    result = chat_with_ai(system_input=system_input, user_input=user_input)

    # Assertions
    assert result == "Test response from AI"
    mock_truncate_message.assert_called_once_with(input_message=user_input)
    # Verify unicode characters are preserved in system message
    call_args = mock_openai_client.chat.completions.create.call_args[1]
    assert call_args["messages"][0]["content"] == system_input
    assert call_args["messages"][1]["content"] == "🌟 truncated unicode input 🚀"


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_special_characters(
    mock_truncate_message, mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test chat completion with special characters and newlines"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_truncate_message.return_value = "Line 1\nLine 2\tTabbed"
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Test inputs with special characters
    system_input = "System message with\nnewlines and\ttabs"
    user_input = "User input with\nspecial\tcharacters"

    # Call function
    result = chat_with_ai(system_input=system_input, user_input=user_input)

    # Assertions
    assert result == "Test response from AI"
    mock_truncate_message.assert_called_once_with(input_message=user_input)


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_model_configuration(
    mock_truncate_message, mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test that the correct model is used in the API call"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_truncate_message.return_value = "test message"
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Call function
    chat_with_ai(system_input="test system", user_input="test user")

    # Verify the model parameter
    call_args = mock_openai_client.chat.completions.create.call_args[1]
    assert call_args["model"] == OPENAI_MODEL_ID_O3_MINI


@patch("services.openai.chat.create_openai_client")
@patch("services.openai.chat.truncate_message")
def test_chat_with_ai_message_structure(
    mock_truncate_message, mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test that messages are structured correctly with proper roles"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_truncate_message.return_value = "truncated"
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Call function
    chat_with_ai(system_input="system", user_input="user")

    # Verify message structure
    call_args = mock_openai_client.chat.completions.create.call_args[1]
    messages = call_args["messages"]
    
    assert len(messages) == 2
    assert messages[0]["role"] == "developer"
    assert messages[1]["role"] == "user"
    assert "content" in messages[0]
    assert "content" in messages[1]