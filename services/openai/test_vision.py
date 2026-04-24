from unittest.mock import MagicMock, patch

import pytest
from openai import OpenAIError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from config import OPENAI_MODEL_ID
from services.openai.vision import describe_image
from utils.prompts.describe_image import DESCRIBE_IMAGE


@pytest.fixture(autouse=True)
def mock_insert_llm_request():
    with patch("services.openai.vision.insert_llm_request") as mock:
        yield mock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client with proper method chaining"""
    client = MagicMock()
    return client


def _build_completion(content):
    completion = MagicMock(spec=ChatCompletion)
    message = MagicMock(spec=ChatCompletionMessage)
    message.content = content
    choice = MagicMock(spec=Choice)
    choice.message = message
    completion.choices = [choice]
    usage = MagicMock()
    usage.prompt_tokens = 11
    usage.completion_tokens = 22
    completion.usage = usage
    return completion


@pytest.fixture
def mock_chat_completion():
    return _build_completion("This is a detailed image description from AI")


@pytest.fixture
def mock_chat_completion_with_whitespace():
    return _build_completion("  \n  Image description with whitespace  \n  ")


@pytest.fixture
def mock_chat_completion_empty_content():
    return _build_completion(None)


@pytest.fixture
def mock_chat_completion_empty_string():
    return _build_completion("")


@pytest.fixture
def mock_chat_completion_whitespace_only():
    return _build_completion("   \n\t   ")


@patch("services.openai.vision.create_openai_client")
def test_describe_image_success_without_context(
    mock_create_client,
    mock_openai_client,
    mock_chat_completion,
    mock_insert_llm_request,
):
    """Test successful image description without context"""
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    result = describe_image(base64_image=base64_image, usage_id=7, created_by="tester")

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
        model=OPENAI_MODEL_ID,
        n=1,
    )
    mock_insert_llm_request.assert_called_once()
    call_kwargs = mock_insert_llm_request.call_args.kwargs
    assert call_kwargs["usage_id"] == 7
    assert call_kwargs["created_by"] == "tester"
    assert call_kwargs["provider"] == "openai"
    assert call_kwargs["model_id"] == OPENAI_MODEL_ID
    assert call_kwargs["input_tokens"] == 11
    assert call_kwargs["output_tokens"] == 22


@patch("services.openai.vision.create_openai_client")
def test_describe_image_success_with_context(
    mock_create_client, mock_openai_client, mock_chat_completion
):
    """Test successful image description with context"""
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = mock_chat_completion

    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    context = "This is a screenshot of a bug in the application"

    result = describe_image(
        base64_image=base64_image,
        usage_id=0,
        created_by="tester",
        context=context,
    )

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
        model=OPENAI_MODEL_ID,
        n=1,
    )


@patch("services.openai.vision.create_openai_client")
def test_describe_image_with_whitespace_content(
    mock_create_client, mock_openai_client, mock_chat_completion_with_whitespace
):
    """Test image description with content that has leading/trailing whitespace"""
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = (
        mock_chat_completion_with_whitespace
    )

    base64_image = "test_image_data"

    result = describe_image(base64_image=base64_image, usage_id=1, created_by="tester")

    assert result == "Image description with whitespace"
    mock_create_client.assert_called_once()


@patch("services.openai.vision.create_openai_client")
def test_describe_image_none_content(
    mock_create_client, mock_openai_client, mock_chat_completion_empty_content
):
    """Test image description when response content is None"""
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = (
        mock_chat_completion_empty_content
    )

    base64_image = "test_image_data"

    result = describe_image(base64_image=base64_image, usage_id=1, created_by="tester")

    assert result == "No response from OpenAI"
    mock_create_client.assert_called_once()


@patch("services.openai.vision.create_openai_client")
def test_describe_image_empty_string_content(
    mock_create_client, mock_openai_client, mock_chat_completion_empty_string
):
    """Test image description when response content is empty string"""
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = (
        mock_chat_completion_empty_string
    )

    base64_image = "test_image_data"

    result = describe_image(base64_image=base64_image, usage_id=1, created_by="tester")

    assert result == "No response from OpenAI"
    mock_create_client.assert_called_once()


@patch("services.openai.vision.create_openai_client")
def test_describe_image_whitespace_only_content(
    mock_create_client, mock_openai_client, mock_chat_completion_whitespace_only
):
    """Test image description when response content is whitespace only"""
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value = (
        mock_chat_completion_whitespace_only
    )

    base64_image = "test_image_data"

    result = describe_image(base64_image=base64_image, usage_id=1, created_by="tester")

    assert result == "No response from OpenAI"
    mock_create_client.assert_called_once()


@patch("services.openai.vision.create_openai_client")
def test_describe_image_openai_error_returns_default(
    mock_create_client, mock_openai_client
):
    """Test that OpenAI errors return default value due to handle_exceptions(raise_on_error=False)"""
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.side_effect = OpenAIError("API Error")

    base64_image = "test_image_data"

    result = describe_image(base64_image=base64_image, usage_id=1, created_by="tester")

    assert result == ""
    mock_create_client.assert_called_once()


@patch("services.openai.vision.create_openai_client")
def test_describe_image_attribute_error_returns_default(
    mock_create_client, mock_openai_client
):
    """Test that AttributeError returns default value due to handle_exceptions(raise_on_error=False)"""
    mock_create_client.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.side_effect = AttributeError(
        "Missing attribute"
    )

    base64_image = "test_image_data"

    result = describe_image(base64_image=base64_image, usage_id=1, created_by="tester")

    assert result == ""
    mock_create_client.assert_called_once()
