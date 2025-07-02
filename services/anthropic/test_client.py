from unittest.mock import patch, MagicMock, Mock

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

    def test_client_has_correct_api_key(self):
        """Test that the client is configured with the correct API key."""
        client = get_anthropic_client()
        assert client.api_key == ANTHROPIC_API_KEY

    def test_creates_new_instance_each_call(self):
        """Test that each call to get_anthropic_client creates a new instance."""
        client1 = get_anthropic_client()
        client2 = get_anthropic_client()
        assert client1 is not client2

    @patch("services.anthropic.client.ANTHROPIC_API_KEY", "custom_test_key")
    def test_uses_api_key_from_config(self):
        """Test that the client uses the API key from config."""
        client = get_anthropic_client()
        assert client.api_key == "custom_test_key"

    @patch("services.anthropic.client.ANTHROPIC_API_KEY", "")
    def test_handles_empty_api_key(self):
        """Test that the client can be created with an empty API key."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        assert client.api_key == ""

    @patch("services.anthropic.client.ANTHROPIC_API_KEY", None)
    def test_handles_none_api_key(self):
        """Test that the client can be created with None API key."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        assert client.api_key is None

    def test_client_has_expected_attributes(self):
        """Test that the returned client has expected Anthropic client attributes."""
        client = get_anthropic_client()
        # Check for key attributes that should exist on an Anthropic client
        assert hasattr(client, 'messages')
        assert hasattr(client, 'api_key')
        assert hasattr(client, '_client')

    def test_multiple_calls_return_different_objects_with_same_config(self):
        """Test that multiple calls return different objects but with same configuration."""
        client1 = get_anthropic_client()
        client2 = get_anthropic_client()
        
        # Different instances
        assert client1 is not client2
        # Same configuration
        assert client1.api_key == client2.api_key
        assert client1.api_key == ANTHROPIC_API_KEY


class TestGetAnthropicClientMocked:
    """Test cases for get_anthropic_client function using mocks to test constructor calls."""

    @patch("services.anthropic.client.Anthropic")
    def test_passes_api_key_to_constructor(self, mock_anthropic):
        """Test that get_anthropic_client passes the correct API key to Anthropic constructor."""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        
        result = get_anthropic_client()
        
        mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)
        assert result == mock_instance

    @patch("services.anthropic.client.Anthropic")
    def test_constructor_called_with_empty_string_api_key(self, mock_anthropic):
        """Test constructor is called correctly with empty string API key."""
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", ""):
            get_anthropic_client()
            mock_anthropic.assert_called_once_with(api_key="")

    @patch("services.anthropic.client.Anthropic")
    def test_constructor_called_with_none_api_key(self, mock_anthropic):
        """Test constructor is called correctly with None API key."""
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", None):
            get_anthropic_client()
            mock_anthropic.assert_called_once_with(api_key=None)

    @patch("services.anthropic.client.Anthropic")
    def test_constructor_called_with_custom_api_key(self, mock_anthropic):
        """Test constructor is called correctly with custom API key."""
        custom_key = "sk-ant-api03-custom-test-key-123"
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", custom_key):
            get_anthropic_client()
            mock_anthropic.assert_called_once_with(api_key=custom_key)

    @patch("services.anthropic.client.Anthropic")
    def test_returns_anthropic_constructor_result(self, mock_anthropic):
        """Test that get_anthropic_client returns whatever Anthropic constructor returns."""
        mock_instance = Mock()
        mock_anthropic.return_value = mock_instance
        
        result = get_anthropic_client()
        
        assert result is mock_instance

    @patch("services.anthropic.client.Anthropic")
    def test_constructor_called_once_per_function_call(self, mock_anthropic):
        """Test that Anthropic constructor is called once for each function call."""
        get_anthropic_client()
        get_anthropic_client()
        
        assert mock_anthropic.call_count == 2
