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
        
