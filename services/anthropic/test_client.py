from unittest.mock import patch, MagicMock

import pytest
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY
from services.anthropic.client import get_anthropic_client


@pytest.fixture
def mock_anthropic():
    """Fixture to provide a mocked Anthropic class."""
    with patch("services.anthropic.client.Anthropic") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_api_key():
    """Fixture to provide a test API key."""
    return "test_api_key_12345"


def test_get_anthropic_client_returns_anthropic_instance():
    """Test that get_anthropic_client returns an Anthropic client instance."""
    client = get_anthropic_client()
    assert isinstance(client, Anthropic)


def test_get_anthropic_client_uses_configured_api_key():
    """Test that the client uses the API key from configuration."""
    client = get_anthropic_client()
    assert client.api_key == ANTHROPIC_API_KEY


def test_get_anthropic_client_with_custom_api_key(mock_api_key):
    """Test that the client uses a custom API key when configuration is patched."""
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", mock_api_key):
        client = get_anthropic_client()
        assert client.api_key == mock_api_key


def test_get_anthropic_client_creates_new_instance_each_call():
    """Test that each call to get_anthropic_client returns a new instance."""
    client1 = get_anthropic_client()
    client2 = get_anthropic_client()
    assert client1 is not client2
    assert isinstance(client1, Anthropic)
    assert isinstance(client2, Anthropic)


def test_get_anthropic_client_constructor_called_with_api_key(mock_anthropic):
    """Test that Anthropic constructor is called with the correct API key."""
    client = get_anthropic_client()

    mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)
    assert client == mock_anthropic.return_value


def test_get_anthropic_client_handles_empty_api_key(mock_anthropic):
    """Test that the client handles empty API key gracefully."""
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", ""):
        get_anthropic_client()
        mock_anthropic.assert_called_once_with(api_key="")


def test_get_anthropic_client_handles_none_api_key(mock_anthropic):
    """Test that the client handles None API key gracefully."""
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", None):
        get_anthropic_client()
        mock_anthropic.assert_called_once_with(api_key=None)


def test_get_anthropic_client_with_whitespace_api_key(mock_anthropic):
    """Test that the client handles API key with whitespace."""
    whitespace_key = "  test_key_with_spaces  "
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", whitespace_key):
        get_anthropic_client()
        mock_anthropic.assert_called_once_with(api_key=whitespace_key)


def test_get_anthropic_client_with_special_characters_api_key(mock_anthropic):
    """Test that the client handles API key with special characters."""
    special_key = "sk-ant-api03-!@#$%^&*()_+-=[]{}|;:,.<>?"
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", special_key):
        get_anthropic_client()
        mock_anthropic.assert_called_once_with(api_key=special_key)


def test_get_anthropic_client_multiple_calls_use_same_api_key():
    """Test that multiple calls consistently use the same API key from config."""
    client1 = get_anthropic_client()
    client2 = get_anthropic_client()
    client3 = get_anthropic_client()

    assert client1.api_key == ANTHROPIC_API_KEY
    assert client2.api_key == ANTHROPIC_API_KEY
    assert client3.api_key == ANTHROPIC_API_KEY
    assert client1.api_key == client2.api_key == client3.api_key


def test_get_anthropic_client_api_key_immutable_after_creation():
    """Test that the API key remains consistent after client creation."""
    client = get_anthropic_client()
    original_api_key = client.api_key

    # Verify the API key hasn't changed
    assert client.api_key == original_api_key
    assert client.api_key == ANTHROPIC_API_KEY


@pytest.mark.parametrize(
    "api_key_value",
    [
        "valid_key_123",
        "",
        None,
        "sk-ant-api03-very-long-key-with-many-characters-1234567890",
        "key with spaces",
        "key\nwith\nnewlines",
        "key\twith\ttabs",
    ],
)
def test_get_anthropic_client_with_various_api_key_formats(
    mock_anthropic, api_key_value
):
    """Test that the client handles various API key formats correctly."""
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", api_key_value):
        get_anthropic_client()
        mock_anthropic.assert_called_once_with(api_key=api_key_value)
