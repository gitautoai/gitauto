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
    get_anthropic_client()
    mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)


def test_get_anthropic_client_returns_mocked_instance(mock_anthropic):
    """Test that get_anthropic_client returns the mocked instance."""
    client = get_anthropic_client()
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


def test_get_anthropic_client_with_mock_preserves_behavior(mock_anthropic):
    """Test that mocking preserves the expected behavior."""
    # Configure mock to have specific behavior
    mock_instance = mock_anthropic.return_value
    mock_instance.api_key = "mocked_key"
    
    client = get_anthropic_client()
    
    # Verify the mock was called correctly
    mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)
    # Verify we get the mocked instance
    assert client == mock_instance
    assert client.api_key == "mocked_key"


def test_get_anthropic_client_multiple_calls_with_mock(mock_anthropic):
    """Test multiple calls with mocked Anthropic class."""
    client1 = get_anthropic_client()
    client2 = get_anthropic_client()
    
    # Each call should create a new mock instance
    assert mock_anthropic.call_count == 2
    # But both should return the same mock instance
    assert client1 == mock_anthropic.return_value
    assert client2 == mock_anthropic.return_value


@pytest.mark.parametrize("api_key_value", [
    "valid_key_123",
    "",
    None,
    "sk-ant-api03-very-long-key-with-many-characters-1234567890",
    "key with spaces",
    "key\nwith\nnewlines",
    "key\twith\ttabs",
])
def test_get_anthropic_client_with_various_api_key_formats(mock_anthropic, api_key_value):
    """Test that the client handles various API key formats correctly."""
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", api_key_value):
        get_anthropic_client()
        mock_anthropic.assert_called_once_with(api_key=api_key_value)


def test_get_anthropic_client_function_exists():
    """Test that the get_anthropic_client function exists and is callable."""
    assert callable(get_anthropic_client)


def test_get_anthropic_client_return_type_annotation():
    """Test that the function has the correct return type annotation."""
    import inspect
    signature = inspect.signature(get_anthropic_client)
    assert signature.return_annotation == Anthropic


def test_get_anthropic_client_no_parameters():
    """Test that the function takes no parameters."""
    import inspect
    signature = inspect.signature(get_anthropic_client)
    assert len(signature.parameters) == 0


def test_get_anthropic_client_imports_work():
    """Test that all required imports are available."""
    # This test ensures the module can be imported without errors
    from services.anthropic.client import get_anthropic_client
    from config import ANTHROPIC_API_KEY
    from anthropic import Anthropic
    
    assert get_anthropic_client is not None
    assert ANTHROPIC_API_KEY is not None
    assert Anthropic is not None


def test_get_anthropic_client_config_dependency():
    """Test that the function properly depends on config."""
    # Test that changing the config affects the client
    original_key = ANTHROPIC_API_KEY
    test_key = "test_dependency_key"
    
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", test_key):
        client = get_anthropic_client()
        assert client.api_key == test_key
        assert client.api_key != original_key


def test_get_anthropic_client_with_long_api_key(mock_anthropic):
    """Test handling of very long API keys."""
    long_key = "sk-ant-api03-" + "x" * 1000
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", long_key):
        get_anthropic_client()
        mock_anthropic.assert_called_once_with(api_key=long_key)


def test_get_anthropic_client_with_unicode_api_key(mock_anthropic):
    """Test handling of API keys with unicode characters."""
    unicode_key = "sk-ant-api03-测试-🔑-key"
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", unicode_key):
        get_anthropic_client()
        mock_anthropic.assert_called_once_with(api_key=unicode_key)