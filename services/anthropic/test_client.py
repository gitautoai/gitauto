"""Unit tests for services.anthropic.client module."""

from unittest.mock import patch, MagicMock

import pytest
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY
from services.anthropic.client import get_anthropic_client


class TestGetAnthropicClient:
    """Test cases for get_anthropic_client function."""

    def test_returns_anthropic_client_instance(self):
        """Test that get_anthropic_client returns an Anthropic client instance."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        assert client.api_key == ANTHROPIC_API_KEY

    def test_uses_api_key_from_config(self):
        """Test that get_anthropic_client uses the API key from config."""
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", "test_api_key"):
            client = get_anthropic_client()
            assert client.api_key == "test_api_key"

    def test_creates_new_instance_each_call(self):
        """Test that get_anthropic_client creates a new instance on each call."""
        client1 = get_anthropic_client()
        client2 = get_anthropic_client()
        assert client1 is not client2
        assert isinstance(client1, Anthropic)
        assert isinstance(client2, Anthropic)

    @patch("services.anthropic.client.Anthropic")
    def test_passes_api_key_to_constructor(self, mock_anthropic):
        """Test that get_anthropic_client passes the API key to Anthropic constructor."""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        
        client = get_anthropic_client()
        
        mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)
        assert client == mock_instance

    @patch("services.anthropic.client.Anthropic")
    def test_handles_empty_api_key(self, mock_anthropic):
        """Test that get_anthropic_client handles empty API key."""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", ""):
            client = get_anthropic_client()
            
        mock_anthropic.assert_called_once_with(api_key="")
        assert client == mock_instance

    @patch("services.anthropic.client.Anthropic")
    def test_handles_none_api_key(self, mock_anthropic):
        """Test that get_anthropic_client handles None API key."""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", None):
            client = get_anthropic_client()
            
        mock_anthropic.assert_called_once_with(api_key=None)
        assert client == mock_instance

    @patch("services.anthropic.client.Anthropic")
    def test_handles_whitespace_api_key(self, mock_anthropic):
        """Test that get_anthropic_client handles whitespace-only API key."""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        whitespace_key = "   \t\n   "
        
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", whitespace_key):
            client = get_anthropic_client()
            
        mock_anthropic.assert_called_once_with(api_key=whitespace_key)
        assert client == mock_instance

    @patch("services.anthropic.client.Anthropic")
    def test_handles_long_api_key(self, mock_anthropic):
        """Test that get_anthropic_client handles very long API key."""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        long_key = "a" * 1000  # Very long API key
        
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", long_key):
            client = get_anthropic_client()
            
        mock_anthropic.assert_called_once_with(api_key=long_key)
        assert client == mock_instance

    @patch("services.anthropic.client.Anthropic")
    def test_handles_special_characters_in_api_key(self, mock_anthropic):
        """Test that get_anthropic_client handles API key with special characters."""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        special_key = "sk-ant-api03-!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", special_key):
            client = get_anthropic_client()
            
        mock_anthropic.assert_called_once_with(api_key=special_key)
        assert client == mock_instance

    def test_client_has_correct_attributes(self):
        """Test that the returned client has the expected attributes."""
        client = get_anthropic_client()
        
        # Check that the client has the expected attributes
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'messages')
        assert client.api_key == ANTHROPIC_API_KEY

    def test_multiple_calls_return_independent_clients(self):
        """Test that multiple calls return independent client instances."""
        clients = [get_anthropic_client() for _ in range(5)]
        
        # All should be Anthropic instances
        for client in clients:
            assert isinstance(client, Anthropic)
            assert client.api_key == ANTHROPIC_API_KEY
        
        # All should be different instances
        for i, client1 in enumerate(clients):
            for j, client2 in enumerate(clients):
                if i != j:
                    assert client1 is not client2

    @patch("services.anthropic.client.Anthropic")
    def test_propagates_anthropic_constructor_exceptions(self, mock_anthropic):
        """Test that exceptions from Anthropic constructor are propagated."""
        mock_anthropic.side_effect = ValueError("Invalid API key format")
        
        with pytest.raises(ValueError, match="Invalid API key format"):
            get_anthropic_client()
        
        mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)

    def test_function_return_type_annotation(self):
        """Test that the function returns the correct type as per annotation."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        


class TestGetAnthropicClientIntegration:
    """Integration tests for get_anthropic_client function."""
    
    def test_client_can_be_used_for_basic_operations(self):
        """Test that the returned client can be used for basic operations."""
        client = get_anthropic_client()
        
        # Verify the client has the expected methods and attributes
        assert hasattr(client, 'messages')
        assert hasattr(client, 'api_key')
        assert callable(getattr(client.messages, 'create', None))
        
    def test_client_configuration_is_correct(self):
        """Test that the client is configured correctly."""
        client = get_anthropic_client()
        
        # Check that the client is properly configured
        assert client.api_key == ANTHROPIC_API_KEY
        assert isinstance(client.api_key, (str, type(None)))
        
    def test_client_is_ready_for_api_calls(self):
        """Test that the client is ready for API calls (without making actual calls)."""
        client = get_anthropic_client()
        
        # Verify client has the necessary components for API calls
        assert hasattr(client, '_client')
        assert hasattr(client, 'messages')
        
        # Check that messages has the expected methods
        messages = client.messages
        assert hasattr(messages, 'create')
        assert hasattr(messages, 'count_tokens')
        
    def test_multiple_clients_have_same_configuration(self):
        """Test that multiple clients have the same configuration."""
        clients = [get_anthropic_client() for _ in range(3)]
        
        # All clients should have the same API key
        api_keys = [client.api_key for client in clients]
        assert all(key == ANTHROPIC_API_KEY for key in api_keys)
        assert len(set(api_keys)) == 1  # All keys should be the same


@pytest.fixture
def mock_anthropic():
    """Fixture that provides a mocked Anthropic class."""
    with patch("services.anthropic.client.Anthropic") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def test_api_key():
    """Fixture that provides a test API key."""
    return "sk-ant-api03-test-key-12345"


@pytest.fixture
def patched_api_key(test_api_key):
