from unittest.mock import MagicMock, patch

import pytest
from openai import OpenAIError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from config import OPENAI_MODEL_ID_GPT_5
from services.openai.vision import describe_image
from utils.prompts.describe_image import DESCRIBE_IMAGE


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client with proper method chaining"""
    client = MagicMock()
    return client


@pytest.fixture
def mock_chat_completion():
    """Mock ChatCompletion response with content"""
    completion = MagicMock(spec=ChatCompletion)
    message = MagicMock(spec=ChatCompletionMessage)
    message.content = "This is a detailed image description from AI"
    choice = MagicMock(spec=Choice)
    choice.message = message
    completion.choices = [choice]
    return completion


@pytest.fixture
def mock_chat_completion_with_whitespace():
    """Mock ChatCompletion response with content that has whitespace"""
    completion = MagicMock(spec=ChatCompletion)
    message = MagicMock(spec=ChatCompletionMessage)
    message.content = "  \n  Image description with whitespace  \n  "
    choice = MagicMock(spec=Choice)
    choice.message = message
    completion.choices = [choice]
    return completion


@pytest.fixture
def mock_chat_completion_empty_content():
    """Mock ChatCompletion response with None content"""
    completion = MagicMock(spec=ChatCompletion)
    message = MagicMock(spec=ChatCompletionMessage)
    message.content = None
    choice = MagicMock(spec=Choice)
    choice.message = message
    completion.choices = [choice]
    return completion


@pytest.fixture
def mock_chat_completion_empty_string():
    """Mock ChatCompletion response with empty string content"""
    completion = MagicMock(spec=ChatCompletion)
    message = MagicMock(spec=ChatCompletionMessage)
    message.content = ""
    choice = MagicMock(spec=Choice)
    choice.message = message
    completion.choices = [choice]
    return completion


@pytest.fixture
def mock_chat_completion_whitespace_only():
    """Mock ChatCompletion response with whitespace-only content"""
    completion = MagicMock(spec=ChatCompletion)
    message = MagicMock(spec=ChatCompletionMessage)
    message.content = "   \n\t   "
    choice = MagicMock(spec=Choice)
    choice.message = message
    completion.choices = [choice]
    return completion


@patch("services.openai.vision.create_openai_client")
def test_describe_image_success_without_context(
    mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test successful image description without context"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Test input
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    # Call function
    result = describe_image(base64_image=base64_image)

    # Assertions
    assert result == "This is a detailed image description from AI"
    mock_create_client.assert_called_once()
    mock_openai_client.chat.completions.create.assert_called_once_with(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": DESCRIBE_IMAGE},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "auto",
                        },
                    },
                ],
            },
        ],
        model=OPENAI_MODEL_ID_GPT_5,
        n=1,
    )


@patch("services.openai.vision.create_openai_client")
def test_describe_image_success_with_context(
    mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test successful image description with context"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    # Test inputs
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    context = "This is a screenshot of a bug in the application"

    # Call function
    result = describe_image(base64_image=base64_image, context=context)

    # Assertions
    assert result == "This is a detailed image description from AI"
    mock_create_client.assert_called_once()
    mock_openai_client.chat.completions.create.assert_called_once_with(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": DESCRIBE_IMAGE},
                    {"type": "text", "text": context},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "auto",
                        },
                    },
                ],
            },
        ],
        model=OPENAI_MODEL_ID_GPT_5,
        n=1,
    )


@patch("services.openai.vision.create_openai_client")
def test_describe_image_with_whitespace_content(
    mock_create_client, mock_openai_client, mock_chat_completion_with_whitespace
):
    """Test image description with content that has leading/trailing whitespace"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = (
        mock_chat_completion_with_whitespace
    )

    # Test input
    base64_image = "test_image_data"

    # Call function
    result = describe_image(base64_image=base64_image)

    # Assertions - should strip whitespace
    assert result == "Image description with whitespace"
    mock_create_client.assert_called_once()


@patch("services.openai.vision.create_openai_client")
def test_describe_image_none_content(
    mock_create_client, mock_openai_client, mock_chat_completion_empty_content
):
    """Test image description when response content is None"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = (
        mock_chat_completion_empty_content
    )

    # Test input
    base64_image = "test_image_data"

    # Call function
    result = describe_image(base64_image=base64_image)

    # Assertions - should return default message
    assert result == "No response from OpenAI"
    mock_create_client.assert_called_once()


@patch("services.openai.vision.create_openai_client")
def test_describe_image_empty_string_content(
    mock_create_client, mock_openai_client, mock_chat_completion_empty_string
):
    """Test image description when response content is empty string"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = (
        mock_chat_completion_empty_string
    )

    # Test input
    base64_image = "test_image_data"

    # Call function
    result = describe_image(base64_image=base64_image)

    # Assertions - should return default message
    assert result == "No response from OpenAI"
    mock_create_client.assert_called_once()


@patch("services.openai.vision.create_openai_client")
def test_describe_image_whitespace_only_content(
    mock_create_client, mock_openai_client, mock_chat_completion_whitespace_only
):
    """Test image description when response content is whitespace only"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = (
        mock_chat_completion_whitespace_only
    )

    # Test input
    base64_image = "test_image_data"

    # Call function
    result = describe_image(base64_image=base64_image)

    # Assertions - should return default message after stripping whitespace
    assert result == "No response from OpenAI"
    mock_create_client.assert_called_once()


@patch("services.openai.vision.create_openai_client")
def test_describe_image_openai_error_returns_default(
    mock_create_client, mock_openai_client
):
    """Test that OpenAI errors return default value due to handle_exceptions(raise_on_error=False)"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.side_effect = OpenAIError("API Error")

    # Test input
    base64_image = "test_image_data"

    # Call function - should not raise exception
    result = describe_image(base64_image=base64_image)

    # Assertions - should return default value from decorator
    assert result == ""
    mock_create_client.assert_called_once()


@patch("services.openai.vision.create_openai_client")
def test_describe_image_attribute_error_returns_default(
    mock_create_client, mock_openai_client
):
    """Test that AttributeError returns default value due to handle_exceptions(raise_on_error=False)"""
    # Setup mocks
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.side_effect = AttributeError(
        "Missing attribute"
    )

    # Test input
    base64_image = "test_image_data"

    # Call function - should not raise exception
    result = describe_image(base64_image=base64_image)

    # Assertions - should return default value from decorator
    assert result == ""
    mock_create_client.assert_called_once()
